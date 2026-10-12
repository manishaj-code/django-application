from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["subject", "name", "email", "created_at", "is_read"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["name", "email", "subject", "message"]
    date_hierarchy = "created_at"
    readonly_fields = ["name", "email", "subject", "message", "created_at"]
    fields = ["name", "email", "subject", "message", "created_at", "is_read"]
    actions = ["mark_read", "mark_unread"]

    def has_add_permission(self, request):
        return False  # messages only arrive through the public form

    @admin.action(description="Mark selected messages as read", permissions=["change"])
    def mark_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} message(s) marked as read.")

    @admin.action(description="Mark selected messages as unread", permissions=["change"])
    def mark_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} message(s) marked as unread.")
