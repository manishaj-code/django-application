import pytest
from django.core import mail
from django.db import connection
from django.test import override_settings
from django.urls import reverse

from core.models import ContactMessage

pytestmark = pytest.mark.django_db
CONTACT_URL = reverse("core:contact")


def contact_data(**overrides):
    data = {
        "name": "Bob",
        "email": "bob@example.com",
        "subject": "Hello",
        "message": "I would like to know more.",
        "website": "",
    }
    data.update(overrides)
    return data


class TestStaticPages:
    @pytest.mark.parametrize("name", ["core:home", "core:about", "core:contact", "content:list"])
    def test_public_pages_render(self, client, name):
        response = client.get(reverse(name))
        assert response.status_code == 200
        assert b"<nav" in response.content and b"<footer" in response.content


class TestContactForm:
    def test_valid_submission_saved(self, client):
        response = client.post(CONTACT_URL, contact_data(), follow=True)
        assert response.redirect_chain[-1][0] == CONTACT_URL
        assert b"your message has been sent" in response.content
        message = ContactMessage.objects.get()
        assert message.email == "bob@example.com"
        assert not message.is_read
        assert mail.outbox == []  # no recipient configured

    @override_settings(CONTACT_RECIPIENT_EMAIL="staff@example.com")
    def test_notification_email_when_configured(self, client):
        client.post(CONTACT_URL, contact_data())
        assert mail.outbox[0].to == ["staff@example.com"]
        assert "Hello" in mail.outbox[0].subject

    @pytest.mark.parametrize(
        "overrides, field",
        [
            ({"name": ""}, "name"),
            ({"name": "   "}, "name"),
            ({"email": "bad"}, "email"),
            ({"subject": ""}, "subject"),
            ({"message": "short"}, "message"),
            ({"message": "x" * 5001}, "message"),
        ],
    )
    def test_server_side_validation(self, client, overrides, field):
        response = client.post(CONTACT_URL, contact_data(**overrides))
        assert response.status_code == 200
        assert field in response.context["form"].errors
        assert b"Please correct the errors below" in response.content
        assert not ContactMessage.objects.exists()

    def test_honeypot_discards_spam_silently(self, client):
        response = client.post(CONTACT_URL, contact_data(website="http://spam"), follow=True)
        assert b"your message has been sent" in response.content
        assert not ContactMessage.objects.exists()


class TestHealthCheck:
    def test_ok(self, client):
        response = client.get(reverse("healthz"))
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok"}
        assert "no-cache" in response["Cache-Control"]

    def test_reports_database_failure(self, client, monkeypatch):
        def broken_cursor(*args, **kwargs):
            raise RuntimeError("db down")

        monkeypatch.setattr(connection, "cursor", broken_cursor)
        response = client.get(reverse("healthz"))
        assert response.status_code == 503
        assert response.json()["status"] == "error"
        assert "db down" not in response.content.decode()

    def test_post_not_allowed(self, client):
        assert client.post(reverse("healthz")).status_code == 405


class TestErrorPages:
    def test_404_page(self, client):
        response = client.get("/definitely/not/here/")
        assert response.status_code == 404
        assert b"Page not found" in response.content
        assert b"<nav" in response.content

    def test_500_page_has_no_details(self, rf):
        from core.views import server_error

        response = server_error(rf.get("/"))
        assert response.status_code == 500
        assert b"Something went wrong" in response.content
        assert b"Traceback" not in response.content

    def test_403_page(self, rf, db):
        from django.contrib.auth.models import AnonymousUser

        from core.views import permission_denied

        request = rf.get("/")
        request.user = AnonymousUser()
        response = permission_denied(request)
        assert response.status_code == 403
        assert b"Access denied" in response.content

    def test_400_page(self, rf):
        from django.contrib.auth.models import AnonymousUser

        from core.views import bad_request

        request = rf.get("/")
        request.user = AnonymousUser()
        assert bad_request(request).status_code == 400
