"""Creates the "Editors" group with content-management permissions."""

from django.db import DEFAULT_DB_ALIAS

EDITOR_GROUP_NAME = "Editors"

EDITOR_PERMISSIONS = [
    ("content", "add_content"),
    ("content", "change_content"),
    ("content", "delete_content"),
    ("content", "view_content"),
    ("content", "add_category"),
    ("content", "change_category"),
    ("content", "delete_category"),
    ("content", "view_category"),
    ("core", "view_contactmessage"),
    ("core", "change_contactmessage"),
]


def create_editor_group(sender, apps, using=DEFAULT_DB_ALIAS, **kwargs):
    """post_migrate handler. Only fills permissions when the group is new, so
    changes an administrator makes to the group later are preserved."""
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    group, created = Group.objects.using(using).get_or_create(name=EDITOR_GROUP_NAME)
    if not created:
        return
    query = Permission.objects.using(using).none()
    for app_label, codename in EDITOR_PERMISSIONS:
        query = query | Permission.objects.using(using).filter(
            content_type__app_label=app_label, codename=codename
        )
    group.permissions.set(query)
