import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError, transaction
from django.urls import reverse

pytestmark = pytest.mark.django_db
User = get_user_model()


def registration_data(**overrides):
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "first_name": "New",
        "last_name": "User",
        "password1": "Very-strong-passw0rd",
        "password2": "Very-strong-passw0rd",
    }
    data.update(overrides)
    return data


class TestRegistration:
    url = reverse("accounts:register")

    def test_page_renders(self, client):
        response = client.get(self.url)
        assert response.status_code == 200
        assert b"Create your account" in response.content

    def test_valid_registration_creates_user_and_logs_in(self, client):
        response = client.post(self.url, registration_data(), follow=True)
        assert response.redirect_chain[-1][0] == reverse("accounts:profile")
        user = User.objects.get(username="newuser")
        assert response.context["user"] == user
        assert b"Your account has been created" in response.content

    def test_password_is_hashed(self, client):
        client.post(self.url, registration_data())
        user = User.objects.get(username="newuser")
        assert user.password != "Very-strong-passw0rd"
        assert user.check_password("Very-strong-passw0rd")

    def test_cannot_grant_self_admin_privileges(self, client):
        client.post(
            self.url,
            registration_data(is_staff="on", is_superuser="on", groups="1"),
        )
        user = User.objects.get(username="newuser")
        assert not user.is_staff
        assert not user.is_superuser
        assert not user.groups.exists()

    @pytest.mark.parametrize(
        "overrides, field",
        [
            ({"password2": "different-passw0rd"}, "password2"),
            ({"password1": "123", "password2": "123"}, "password2"),
            ({"password1": "password", "password2": "password"}, "password2"),
            ({"email": "not-an-email"}, "email"),
            ({"email": ""}, "email"),
            ({"username": ""}, "username"),
            ({"username": "bad user!"}, "username"),
        ],
    )
    def test_invalid_input_shows_errors(self, client, overrides, field):
        response = client.post(self.url, registration_data(**overrides))
        assert response.status_code == 200
        assert field in response.context["form"].errors
        assert b"is-invalid" in response.content
        assert not User.objects.filter(username=overrides.get("username", "newuser")).exists()

    def test_duplicate_email_rejected_case_insensitively(self, client, user):
        response = client.post(self.url, registration_data(email="ALICE@example.com"))
        assert "email" in response.context["form"].errors

    def test_duplicate_username_rejected(self, client, user):
        response = client.post(self.url, registration_data(username="Alice"))
        assert "username" in response.context["form"].errors

    def test_authenticated_user_redirected(self, client, user):
        client.force_login(user)
        assert client.get(self.url).url == reverse("accounts:profile")

    def test_email_uniqueness_enforced_by_database(self, user):
        with pytest.raises(IntegrityError), transaction.atomic():
            User.objects.create_user("other", "Alice@Example.com", "x")


class TestLoginLogout:
    def test_login_page_renders(self, client):
        assert client.get(reverse("login")).status_code == 200

    def test_login_success(self, client, user, password):
        response = client.post(
            reverse("login"), {"username": "alice", "password": password}, follow=True
        )
        assert response.context["user"].is_authenticated
        assert response.redirect_chain[-1][0] == reverse("accounts:profile")

    def test_login_wrong_password(self, client, user):
        response = client.post(reverse("login"), {"username": "alice", "password": "wrong"})
        assert response.status_code == 200
        assert not response.context["user"].is_authenticated
        assert b"Please enter a correct username and password" in response.content

    def test_login_respects_safe_next(self, client, user, password):
        response = client.post(
            reverse("login") + "?next=/content/",
            {"username": "alice", "password": password, "next": "/content/"},
        )
        assert response.url == "/content/"

    def test_login_ignores_external_next(self, client, user, password):
        response = client.post(
            reverse("login"),
            {"username": "alice", "password": password, "next": "https://evil.example/"},
        )
        assert response.url == reverse("accounts:profile")

    def test_inactive_user_cannot_log_in(self, client, user, password):
        user.is_active = False
        user.save()
        client.post(reverse("login"), {"username": "alice", "password": password})
        assert "_auth_user_id" not in client.session

    def test_login_rotates_session_key(self, client, user, password):
        client.get(reverse("login"))
        session = client.session
        session["probe"] = 1
        session.save()
        before = client.session.session_key
        client.post(reverse("login"), {"username": "alice", "password": password})
        assert client.session.session_key != before

    def test_logout_requires_post(self, client, user):
        client.force_login(user)
        assert client.get(reverse("logout")).status_code == 405
        assert "_auth_user_id" in client.session

    def test_logout(self, client, user):
        client.force_login(user)
        response = client.post(reverse("logout"), follow=True)
        assert not response.context["user"].is_authenticated
        assert b"You have been signed out" in response.content


class TestPasswordReset:
    def test_reset_email_sent_for_known_address(self, client, user):
        response = client.post(reverse("password_reset"), {"email": "alice@example.com"})
        assert response.url == reverse("password_reset_done")
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["alice@example.com"]
        assert "/accounts/reset/" in mail.outbox[0].body
        assert mail.outbox[0].subject == "Reset your password on Django CMS"

    def test_unknown_address_gives_same_response_but_no_email(self, client, db):
        response = client.post(reverse("password_reset"), {"email": "nobody@example.com"})
        assert response.url == reverse("password_reset_done")
        assert mail.outbox == []

    def test_full_reset_flow(self, client, user):
        client.post(reverse("password_reset"), {"email": "alice@example.com"})
        link = re.search(r"http://testserver(/accounts/reset/\S+/)", mail.outbox[0].body).group(1)
        response = client.get(link, follow=True)  # redirects to the set-password URL
        set_password_url = response.redirect_chain[-1][0]
        assert response.context["validlink"]
        response = client.post(
            set_password_url,
            {"new_password1": "Brand-new-passw0rd", "new_password2": "Brand-new-passw0rd"},
        )
        assert response.url == reverse("password_reset_complete")
        user.refresh_from_db()
        assert user.check_password("Brand-new-passw0rd")

    def test_invalid_token_shows_error(self, client, user):
        response = client.get(reverse("password_reset_confirm", args=["MQ", "bad-token"]))
        assert response.status_code == 200
        assert not response.context["validlink"]
        assert b"invalid" in response.content


class TestPasswordChange:
    def test_requires_login(self, client):
        response = client.get(reverse("password_change"))
        assert response.status_code == 302
        assert response.url.startswith(reverse("login"))

    def test_change_password(self, client, user, password):
        client.force_login(user)
        response = client.post(
            reverse("password_change"),
            {
                "old_password": password,
                "new_password1": "Another-strong-passw0rd",
                "new_password2": "Another-strong-passw0rd",
            },
        )
        assert response.url == reverse("accounts:profile")
        user.refresh_from_db()
        assert user.check_password("Another-strong-passw0rd")
        # Session survives the password change.
        assert client.get(reverse("accounts:profile")).status_code == 200

    def test_wrong_old_password(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse("password_change"),
            {"old_password": "nope", "new_password1": "x", "new_password2": "x"},
        )
        assert "old_password" in response.context["form"].errors


class TestProfile:
    @pytest.mark.parametrize("name", ["accounts:profile", "accounts:profile_edit"])
    def test_anonymous_redirected_to_login(self, client, name):
        url = reverse(name)
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={url}"

    def test_profile_shows_user_details(self, client, user):
        client.force_login(user)
        response = client.get(reverse("accounts:profile"))
        assert b"alice@example.com" in response.content
        assert b"Member" in response.content

    def test_edit_profile(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse("accounts:profile_edit"),
            {"first_name": "Alicia", "last_name": "Smith", "email": "alicia@example.com"},
            follow=True,
        )
        assert b"Your profile has been updated" in response.content
        user.refresh_from_db()
        assert (user.first_name, user.email) == ("Alicia", "alicia@example.com")

    def test_edit_profile_rejects_taken_email(self, client, user, editor):
        client.force_login(user)
        response = client.post(
            reverse("accounts:profile_edit"),
            {"first_name": "A", "last_name": "", "email": "EDDIE@example.com"},
        )
        assert "email" in response.context["form"].errors

    def test_edit_profile_cannot_escalate_privileges(self, client, user):
        client.force_login(user)
        client.post(
            reverse("accounts:profile_edit"),
            {"first_name": "A", "last_name": "", "email": user.email, "is_staff": "on",
             "is_superuser": "on"},
        )
        user.refresh_from_db()
        assert not user.is_staff and not user.is_superuser
