import io
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from content.models import Category, Content
from content.roles import EDITOR_GROUP_NAME

User = get_user_model()
PASSWORD = "S3cure-test-passphrase!"


@pytest.fixture(autouse=True)
def _clear_cache():
    """Rate-limit counters live in the cache; isolate every test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def password():
    return PASSWORD


@pytest.fixture
def user(db):
    return User.objects.create_user("alice", "alice@example.com", PASSWORD, first_name="Alice")


@pytest.fixture
def editor(db):
    """Staff user in the Editors group (what an administrator would set up)."""
    staff = User.objects.create_user("eddie", "eddie@example.com", PASSWORD, is_staff=True)
    staff.groups.add(Group.objects.get(name=EDITOR_GROUP_NAME))
    return staff


@pytest.fixture
def staff_without_perms(db):
    return User.objects.create_user("sam", "sam@example.com", PASSWORD, is_staff=True)


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser("root", "root@example.com", PASSWORD)


@pytest.fixture
def category(db):
    return Category.objects.create(name="News", description="Latest news")


@pytest.fixture
def make_content(db):
    def _make(title="An article", status=Content.Status.PUBLISHED, **kwargs):
        kwargs.setdefault("body", "First paragraph.\n\nSecond paragraph.")
        return Content.objects.create(title=title, status=status, **kwargs)

    return _make


@pytest.fixture
def published(make_content, category):
    return make_content("Published item", category=category, summary="A summary")


@pytest.fixture
def draft(make_content, category):
    return make_content("Draft item", status=Content.Status.DRAFT, category=category)


@pytest.fixture
def scheduled(make_content):
    return make_content("Future item", published_at=timezone.now() + timedelta(days=3))


def make_image(name="photo.png", fmt="PNG", size=(20, 20)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "steelblue").save(buffer, fmt)
    content_type = f"image/{fmt.lower()}"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


@pytest.fixture
def image_file():
    return make_image()
