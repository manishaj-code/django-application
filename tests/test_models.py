from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.utils import timezone

from content.models import Category, Content
from tests.conftest import make_image

pytestmark = pytest.mark.django_db


class TestCategory:
    def test_slug_generated_from_name(self):
        assert Category.objects.create(name="Press Releases").slug == "press-releases"

    def test_duplicate_slugs_are_made_unique(self):
        first = Category.objects.create(name="Tech!")
        second = Category.objects.create(name="Tech?")
        assert first.slug == "tech"
        assert second.slug == "tech-2"

    def test_name_is_unique(self, category):
        with pytest.raises(IntegrityError), transaction.atomic():
            Category.objects.create(name=category.name, slug="other")

    def test_slug_is_unique_at_database_level(self, category):
        with pytest.raises(IntegrityError), transaction.atomic():
            Category.objects.create(name="Different", slug=category.slug)

    def test_published_counts_only_count_visible_content(self, category, make_content):
        make_content("a", category=category)
        make_content("b", category=category, status=Content.Status.DRAFT)
        make_content("c", category=category, published_at=timezone.now() + timedelta(days=1))
        annotated = Category.objects.with_published_counts().get(pk=category.pk)
        assert annotated.published_count == 1


class TestContentSlugs:
    def test_slug_generated_from_title(self, make_content):
        assert make_content("Hello, World!").slug == "hello-world"

    def test_duplicate_titles_get_unique_slugs(self, make_content):
        slugs = [make_content("Same title").slug for _ in range(3)]
        assert slugs == ["same-title", "same-title-2", "same-title-3"]

    def test_explicit_slug_is_kept(self, make_content):
        assert make_content("Title", slug="custom-slug").slug == "custom-slug"

    def test_slug_unchanged_when_title_edited(self, make_content):
        item = make_content("Original")
        item.title = "Renamed"
        item.save()
        item.refresh_from_db()
        assert item.slug == "original"

    def test_title_without_ascii_characters_gets_fallback_slug(self, make_content):
        assert make_content("日本語").slug == "item"

    def test_duplicate_slug_rejected_by_database(self, make_content):
        make_content("One", slug="dup")
        with pytest.raises(IntegrityError), transaction.atomic():
            Content.objects.bulk_create([Content(title="Two", slug="dup", body="x")])

    def test_duplicate_slug_rejected_by_validation(self, make_content):
        make_content("One", slug="dup")
        item = Content(title="Two", slug="dup", body="x")
        with pytest.raises(ValidationError) as exc:
            item.full_clean()
        assert "slug" in exc.value.message_dict


class TestContentPublication:
    def test_new_content_defaults_to_draft(self, make_content):
        item = Content.objects.create(title="T", body="b")
        assert item.status == Content.Status.DRAFT
        assert item.published_at is None
        assert not item.is_public

    def test_publishing_sets_published_at(self, draft):
        draft.status = Content.Status.PUBLISHED
        draft.save()
        assert draft.published_at is not None
        assert draft.is_public

    def test_full_clean_sets_published_at(self):
        item = Content(title="T", body="b", status=Content.Status.PUBLISHED)
        item.full_clean()
        assert item.published_at is not None

    def test_future_publication_is_scheduled_not_public(self, scheduled):
        assert scheduled.is_scheduled
        assert not scheduled.is_public
        assert scheduled not in Content.objects.published()

    def test_published_queryset(self, published, draft, scheduled):
        assert list(Content.objects.published()) == [published]

    def test_check_constraint_requires_date_when_published(self, draft):
        with pytest.raises(IntegrityError), transaction.atomic():
            Content.objects.filter(pk=draft.pk).update(status=Content.Status.PUBLISHED)

    def test_check_constraint_rejects_unknown_status(self, draft):
        with pytest.raises(IntegrityError), transaction.atomic():
            Content.objects.filter(pk=draft.pk).update(status="archived")

    def test_body_is_required(self):
        with pytest.raises(ValidationError) as exc:
            Content(title="T", body="").full_clean()
        assert "body" in exc.value.message_dict

    def test_title_max_length(self):
        with pytest.raises(ValidationError) as exc:
            Content(title="x" * 201, body="b").full_clean()
        assert "title" in exc.value.message_dict


class TestCategoryRelationship:
    def test_category_reverse_relation(self, category, make_content):
        item = make_content(category=category)
        assert list(category.contents.all()) == [item]

    def test_deleting_category_keeps_content(self, category, make_content):
        item = make_content(category=category)
        category.delete()
        item.refresh_from_db()
        assert item.category is None

    def test_category_is_optional(self, make_content):
        item = make_content(category=None)
        item.full_clean()


class TestContentCrud:
    def test_create_read_update_delete(self, category, user):
        item = Content.objects.create(title="CRUD", body="b", category=category, created_by=user)
        assert Content.objects.get(pk=item.pk).created_by == user
        item.summary = "Updated"
        item.save()
        assert Content.objects.get(pk=item.pk).summary == "Updated"
        assert item.updated_at >= item.created_at
        item.delete()
        assert not Content.objects.filter(pk=item.pk).exists()

    def test_deleting_author_keeps_content(self, user, make_content):
        item = make_content(created_by=user)
        user.delete()
        item.refresh_from_db()
        assert item.created_by is None

    def test_default_ordering_newest_first(self, make_content):
        old = make_content("Old", published_at=timezone.now() - timedelta(days=2))
        new = make_content("New")
        assert list(Content.objects.published()) == [new, old]


class TestFeaturedImage:
    def test_valid_image_saved_under_random_name(self, image_file):
        item = Content(title="Img", body="b", featured_image=image_file)
        item.full_clean()
        item.save()
        assert item.featured_image.name.startswith("content/")
        assert "photo" not in item.featured_image.name
        assert item.featured_image.name.endswith(".png")

    def test_disallowed_extension_rejected(self):
        item = Content(title="Img", body="b", featured_image=make_image("pic.bmp", "BMP"))
        with pytest.raises(ValidationError) as exc:
            item.full_clean()
        assert "featured_image" in exc.value.message_dict

    @override_settings(MAX_UPLOAD_SIZE_MB=0)
    def test_oversized_image_rejected(self, image_file):
        item = Content(title="Img", body="b", featured_image=image_file)
        with pytest.raises(ValidationError) as exc:
            item.full_clean()
        assert "too large" in str(exc.value)

    def test_image_file_deleted_with_content(self, image_file, django_capture_on_commit_callbacks):
        item = Content.objects.create(title="Img", body="b", featured_image=image_file)
        storage, name = item.featured_image.storage, item.featured_image.name
        assert storage.exists(name)
        with django_capture_on_commit_callbacks(execute=True):
            item.delete()
        assert not storage.exists(name)

    def test_replaced_image_file_is_deleted(self, django_capture_on_commit_callbacks):
        item = Content.objects.create(title="Img", body="b", featured_image=make_image())
        storage, old_name = item.featured_image.storage, item.featured_image.name
        item.featured_image = make_image("second.png")
        with django_capture_on_commit_callbacks(execute=True):
            item.save()
        assert not storage.exists(old_name)
        assert storage.exists(item.featured_image.name)


class TestSeedCommand:
    def test_seed_is_idempotent(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("seed_demo_content", count=8, stdout=StringIO())
        call_command("seed_demo_content", count=8, stdout=StringIO())
        assert Content.objects.count() == 8
        assert Category.objects.count() == 3
        assert Content.objects.published().count() == 7
