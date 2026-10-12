import pytest
from django.test import Client, override_settings
from django.urls import reverse

from core.ratelimit import client_ip, parse_rate

pytestmark = pytest.mark.django_db


class TestCsrf:
    @pytest.mark.parametrize(
        "url_name",
        ["login", "accounts:register", "password_reset", "core:contact", "logout"],
    )
    def test_post_without_token_is_rejected(self, url_name):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse(url_name), {})
        assert response.status_code == 403
        assert b"Session expired" in response.content

    def test_forms_include_csrf_token(self, client):
        for url in [reverse("login"), reverse("accounts:register"), reverse("core:contact")]:
            assert b"csrfmiddlewaretoken" in client.get(url).content


class TestRateLimiting:
    @override_settings(RATELIMITS={"login": "3/m", "register": "10/h",
                                   "password_reset": "5/h", "contact": "10/h"})
    def test_login_throttled(self, client, user):
        for _ in range(3):
            assert client.post(reverse("login"), {"username": "alice", "password": "x"}).status_code == 200
        response = client.post(reverse("login"), {"username": "alice", "password": "x"})
        assert response.status_code == 429
        assert b"Too many attempts" in response.content
        # GET requests are not counted.
        assert client.get(reverse("login")).status_code == 200

    @override_settings(RATELIMITS={"login": "2/m", "register": "10/h",
                                   "password_reset": "5/h", "contact": "10/h"})
    def test_limit_is_per_ip(self, user):
        a, b = Client(REMOTE_ADDR="10.0.0.1"), Client(REMOTE_ADDR="10.0.0.2")
        for _ in range(2):
            a.post(reverse("login"), {"username": "alice", "password": "x"})
        assert a.post(reverse("login"), {}).status_code == 429
        assert b.post(reverse("login"), {}).status_code == 200

    @override_settings(RATELIMITS={"login": "2/m", "register": "10/h",
                                   "password_reset": "5/h", "contact": "10/h"})
    def test_admin_login_throttled(self, client):
        for _ in range(2):
            client.post(reverse("admin:login"), {"username": "x", "password": "y"})
        assert client.post(reverse("admin:login"), {"username": "x", "password": "y"}).status_code == 429

    @pytest.mark.parametrize(
        "name, url_name, data",
        [
            ("register", "accounts:register", {}),
            ("password_reset", "password_reset", {"email": "a@example.com"}),
            ("contact", "core:contact", {}),
        ],
    )
    def test_other_sensitive_endpoints_throttled(self, client, settings, name, url_name, data):
        settings.RATELIMITS = {**settings.RATELIMITS, name: "1/h"}
        client.post(reverse(url_name), data)
        assert client.post(reverse(url_name), data).status_code == 429

    @override_settings(RATELIMIT_ENABLED=False, RATELIMITS={"login": "1/m", "register": "1/h",
                                                            "password_reset": "1/h", "contact": "1/h"})
    def test_can_be_disabled(self, client):
        for _ in range(3):
            assert client.post(reverse("login"), {}).status_code == 200

    def test_parse_rate(self):
        assert parse_rate("10/m") == (10, 60)
        assert parse_rate("5/h") == (5, 3600)
        with pytest.raises(ValueError):
            parse_rate("ten per minute")

    def test_client_ip_ignores_forwarded_header_without_trusted_proxy(self, rf, settings):
        settings.NUM_PROXIES = 0
        request = rf.get("/", HTTP_X_FORWARDED_FOR="1.2.3.4", REMOTE_ADDR="10.0.0.9")
        assert client_ip(request) == "10.0.0.9"

    def test_client_ip_uses_trusted_proxy_entry(self, rf, settings):
        settings.NUM_PROXIES = 1
        request = rf.get("/", HTTP_X_FORWARDED_FOR="6.6.6.6, 1.2.3.4", REMOTE_ADDR="10.0.0.9")
        assert client_ip(request) == "1.2.3.4"


class TestSecurityHeaders:
    def test_public_pages_have_security_headers(self, client):
        response = client.get(reverse("core:home"))
        assert "default-src 'self'" in response["Content-Security-Policy"]
        assert "frame-ancestors 'none'" in response["Content-Security-Policy"]
        assert response["X-Frame-Options"] == "DENY"
        assert response["X-Content-Type-Options"] == "nosniff"
        assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "camera=()" in response["Permissions-Policy"]

    def test_admin_has_no_csp(self, client):
        response = client.get(reverse("admin:login"))
        assert "Content-Security-Policy" not in response
        assert response["X-Frame-Options"] == "DENY"

    def test_session_cookie_is_httponly(self, client, user, password):
        response = client.post(reverse("login"), {"username": "alice", "password": password})
        assert response.cookies["sessionid"]["httponly"]
        assert response.cookies["sessionid"]["samesite"] == "Lax"

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_https_redirect_except_health_check(self, client):
        response = client.get(reverse("core:home"))
        assert response.status_code == 301
        assert response.url.startswith("https://")
        assert client.get(reverse("healthz")).status_code == 200


class TestProductionSettings:
    def test_production_defaults_are_secure(self, monkeypatch):
        """Import settings fresh with DEBUG=False and check the hardened defaults."""
        import importlib

        import config.settings as settings_module

        monkeypatch.setenv("DEBUG", "False")
        for name in ["SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE",
                     "SECURE_HSTS_SECONDS", "ALLOWED_HOSTS", "EMAIL_BACKEND"]:
            monkeypatch.delenv(name, raising=False)
        # Ignore any developer .env so only the code defaults are tested.
        monkeypatch.setattr("environ.Env.read_env", lambda *a, **k: None)
        fresh = importlib.reload(settings_module)
        try:
            assert fresh.DEBUG is False
            assert fresh.SECURE_SSL_REDIRECT is True
            assert fresh.SESSION_COOKIE_SECURE is True
            assert fresh.CSRF_COOKIE_SECURE is True
            assert fresh.SECURE_HSTS_SECONDS > 0
            assert fresh.ALLOWED_HOSTS == []
            assert fresh.EMAIL_BACKEND.endswith("smtp.EmailBackend")
        finally:
            monkeypatch.undo()
            importlib.reload(settings_module)

    def test_missing_secret_key_fails_loudly(self, monkeypatch):
        import importlib

        from django.core.exceptions import ImproperlyConfigured

        import config.settings as settings_module

        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.setattr("environ.Env.read_env", lambda *a, **k: None)
        try:
            with pytest.raises(ImproperlyConfigured):
                importlib.reload(settings_module)
        finally:
            monkeypatch.undo()
            importlib.reload(settings_module)
