from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ContentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "content"

    def ready(self):
        from . import signals  # noqa: F401
        from .roles import create_editor_group

        post_migrate.connect(create_editor_group, sender=self)
