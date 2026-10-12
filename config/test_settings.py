"""
Settings for the automated test suite.

By default tests run against an in-memory SQLite database so they need no
database server. Set ``TEST_DATABASE=postgres`` to run them against the
PostgreSQL server configured in ``.env`` instead (the DB user then needs the
CREATEDB privilege so Django can create ``test_<DB_NAME>``).
"""

import os
import tempfile

TEST_DATABASE = os.environ.get("TEST_DATABASE", "sqlite").lower()

os.environ.setdefault("SECRET_KEY", "insecure-key-for-automated-tests-only")
if TEST_DATABASE != "postgres":
    for _name in ("DB_NAME", "DB_USER", "DB_PASSWORD"):
        os.environ.setdefault(_name, "unused")

from .settings import *  # noqa: E402,F401,F403

if TEST_DATABASE != "postgres":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

DEBUG = False
SITE_NAME = "Django CMS"
ALLOWED_HOSTS = ["testserver", "localhost"]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CONTACT_RECIPIENT_EMAIL = ""
RATELIMIT_ENABLED = True
NUM_PROXIES = 0

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="cms-test-media-"))  # noqa: F405
STATIC_ROOT = Path(tempfile.mkdtemp(prefix="cms-test-static-"))  # noqa: F405
