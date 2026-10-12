import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from content.models import Category, Content
from content.roles import EDITOR_GROUP_NAME
from tests.conftest import make_image

pytestmark = pytest.mark.django_db

ADMIN_INDEX = reverse("admin:index")
CONTENT_ADD = reverse("admin:content_content_add")
CONTENT_LIST = reverse("admin:content_content_changelist")


def content_form(**overrides):
    data = {
        "title": "Admin created",
        "slug": "",
        "summary": "Summary",
        "body": "Body text",
        "category": "",
        "status": Content.Status.DRAFT,
        "published_at_0": "",
        "published_at_1": "",
    }
    data.update(overrides)
    return data


class TestAdminAccess:
    def test_anonymous_redirected_to_admin_login(self, client):
        response = client.get(ADMIN_INDEX)
        assert response.status_code == 302
        assert reverse("admin:login") in response.url

    def test_regular_user_cannot_access_admin(self, client, user):
        client.force_login(user)
        response = client.get(ADMIN_INDEX)
        assert response.status_code == 302
        assert reverse("admin:login") in response.url

    def test_regular_user_cannot_log_into_admin(self, client, user, password):
        response = client.post(
            reverse("admin:login"), {"username": "alice", "password": password}
        )
        assert response.status_code == 200
        assert b"Please enter the correct username and password for a staff" in response.content

    def test_staff_without_permissions_gets_403_on_models(self, client, staff_without_perms):
        client.force_login(staff_without_perms)
        assert client.get(ADMIN_INDEX).status_code == 200
        assert client.get(CONTENT_LIST).status_code == 403
        assert client.get(reverse("admin:accounts_user_changelist")).status_code == 403

    def test_editor_cannot_manage_users(self, client, editor):
        client.force_login(editor)
        assert client.get(CONTENT_LIST).status_code == 200
        assert client.get(reverse("admin:accounts_user_changelist")).status_code == 403
        assert client.get(reverse("admin:auth_group_changelist")).status_code == 403

    def test_superuser_can_manage_users(self, client, superuser, user):
        client.force_login(superuser)
        assert client.get(reverse("admin:accounts_user_changelist")).status_code == 200
        response = client.get(reverse("admin:accounts_user_change", args=[user.pk]))
        assert response.status_code == 200

    def test_editors_group_exists_with_expected_permissions(self):
        perms = set(
            Group.objects.get(name=EDITOR_GROUP_NAME).permissions.values_list("codename", flat=True)
        )
        assert {"add_content", "change_content", "delete_content", "view_category"} <= perms
        assert not any(p.endswith("_user") or p.endswith("_group") for p in perms)


class TestAdminContentManagement:
    @pytest.fixture(autouse=True)
    def login(self, client, editor):
        client.force_login(editor)

    def test_changelist_search_and_filters(self, client, published, draft):
        response = client.get(CONTENT_LIST, {"q": "Published"})
        assert response.status_code == 200
        assert list(response.context["cl"].result_list) == [published]
        response = client.get(CONTENT_LIST, {"status__exact": "draft"})
        assert list(response.context["cl"].result_list) == [draft]
        response = client.get(CONTENT_LIST, {"category__id__exact": published.category.pk})
        assert set(response.context["cl"].result_list) == {published, draft}

    def test_create_content_sets_author_and_slug(self, client, editor, category):
        response = client.post(CONTENT_ADD, content_form(category=category.pk))
        assert response.status_code == 302, response.context["adminform"].form.errors
        item = Content.objects.get(title="Admin created")
        assert item.created_by == editor
        assert item.slug == "admin-created"
        assert item.category == category
        assert item.status == Content.Status.DRAFT

    def test_create_published_content_gets_date(self, client):
        client.post(CONTENT_ADD, content_form(status=Content.Status.PUBLISHED))
        item = Content.objects.get(title="Admin created")
        assert item.published_at is not None
        assert item.is_public

    def test_create_with_image(self, client):
        client.post(CONTENT_ADD, {**content_form(), "featured_image": make_image()})
        assert Content.objects.get(title="Admin created").featured_image

    def test_create_with_invalid_image_shows_error(self, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake = SimpleUploadedFile("evil.png", b"<?php echo 1; ?>", content_type="image/png")
        response = client.post(CONTENT_ADD, {**content_form(), "featured_image": fake})
        assert response.status_code == 200
        assert "featured_image" in response.context["adminform"].form.errors
        assert not Content.objects.exists()

    def test_missing_required_fields_show_errors(self, client):
        response = client.post(CONTENT_ADD, content_form(title="", body=""))
        errors = response.context["adminform"].form.errors
        assert {"title", "body"} <= set(errors)

    def test_duplicate_slug_shows_error(self, client, published):
        response = client.post(CONTENT_ADD, content_form(slug=published.slug))
        assert "slug" in response.context["adminform"].form.errors

    def test_edit_content(self, client, draft, editor):
        url = reverse("admin:content_content_change", args=[draft.pk])
        assert client.get(url).status_code == 200
        response = client.post(
            url,
            content_form(title="Edited", slug=draft.slug, category=draft.category.pk),
        )
        assert response.status_code == 302
        draft.refresh_from_db()
        assert draft.title == "Edited"

    def test_delete_content(self, client, draft):
        url = reverse("admin:content_content_delete", args=[draft.pk])
        assert client.get(url).status_code == 200
        client.post(url, {"post": "yes"})
        assert not Content.objects.filter(pk=draft.pk).exists()

    def test_publish_action(self, client, draft):
        client.post(CONTENT_LIST, {"action": "publish", "_selected_action": [draft.pk]})
        draft.refresh_from_db()
        assert draft.status == Content.Status.PUBLISHED
        assert draft.published_at is not None

    def test_unpublish_action(self, client, published):
        client.post(CONTENT_LIST, {"action": "unpublish", "_selected_action": [published.pk]})
        published.refresh_from_db()
        assert published.status == Content.Status.DRAFT
        assert not Content.objects.published().exists()

    def test_republish_keeps_original_date(self, client, published):
        original = published.published_at
        client.post(CONTENT_LIST, {"action": "unpublish", "_selected_action": [published.pk]})
        client.post(CONTENT_LIST, {"action": "publish", "_selected_action": [published.pk]})
        published.refresh_from_db()
        assert published.published_at == original

    def test_manage_categories(self, client):
        add_url = reverse("admin:content_category_add")
        client.post(add_url, {"name": "Guides", "slug": "", "description": ""})
        category = Category.objects.get(name="Guides")
        assert category.slug == "guides"
        change_url = reverse("admin:content_category_change", args=[category.pk])
        client.post(change_url, {"name": "How-to guides", "slug": "guides", "description": "d"})
        category.refresh_from_db()
        assert category.name == "How-to guides"
        client.post(reverse("admin:content_category_delete", args=[category.pk]), {"post": "yes"})
        assert not Category.objects.filter(pk=category.pk).exists()

    def test_category_search(self, client, category):
        response = client.get(reverse("admin:content_category_changelist"), {"q": "News"})
        assert list(response.context["cl"].result_list) == [category]


class TestAdminContactMessages:
    def test_editor_can_view_but_not_add(self, client, editor):
        client.force_login(editor)
        assert client.get(reverse("admin:core_contactmessage_changelist")).status_code == 200
        assert client.get(reverse("admin:core_contactmessage_add")).status_code == 403
