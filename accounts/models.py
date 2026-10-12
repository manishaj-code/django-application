from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    """
    Project user model. Identical to Django's default user except that an
    email address is required and unique (case-insensitive), which password
    reset relies on.
    """

    email = models.EmailField("email address")

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="accounts_user_email_ci_unique",
                violation_error_message="A user with this email address already exists.",
            ),
        ]

    def __str__(self):
        return self.get_full_name() or self.username
