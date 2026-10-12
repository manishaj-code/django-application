from django.contrib import admin
from django.db.models import Count
from django.utils import timezone
from django.utils.html import format_html

from .models import Category, Content


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "content_count", "updated_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ["name"]}
    readonly_fields = ["created_at", "updated_at"]
    fields = ["name", "slug", "description", "created_at", "updated_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_content_count=Count("contents"))

    @admin.display(description="Items", ordering="_content_count")
    def content_count(self, obj):
        return obj._content_count


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "status",
        "published_at",
        "created_by",
        "updated_at",
    ]
    list_display_links = ["title"]
    list_filter = ["status", "category", "published_at", "created_at"]
    list_select_related = ["category", "created_by"]
    search_fields = ["title", "slug", "summary", "body"]
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ["title"]}
    autocomplete_fields = ["category"]
    readonly_fields = ["image_preview", "created_by", "created_at", "updated_at", "public_link"]
    actions = ["publish", "unpublish"]
    list_per_page = 25
    save_on_top = True
    fieldsets = [
        (None, {"fields": ["title", "slug", "category", "summary", "body"]}),
        ("Image", {"fields": ["featured_image", "image_preview"]}),
        ("Publication", {"fields": ["status", "published_at", "public_link"]}),
        (
            "History",
            {"fields": ["created_by", "created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if obj and obj.featured_image:
            return format_html(
                '<img src="{}" alt="" style="max-height:160px;max-width:320px">',
                obj.featured_image.url,
            )
        return "—"

    @admin.display(description="Public page")
    def public_link(self, obj):
        if obj and obj.pk:
            label = "View on site" if obj.is_public else "Preview (not public yet)"
            return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>',
                               obj.get_absolute_url(), label)
        return "—"

    @admin.action(description="Publish selected items", permissions=["change"])
    def publish(self, request, queryset):
        now = timezone.now()
        drafts = queryset.filter(status=Content.Status.DRAFT)
        count = drafts.filter(published_at__isnull=True).update(
            status=Content.Status.PUBLISHED, published_at=now
        )
        count += drafts.update(status=Content.Status.PUBLISHED)
        self.message_user(request, f"{count} item(s) published.")

    @admin.action(description="Unpublish selected items (back to draft)", permissions=["change"])
    def unpublish(self, request, queryset):
        count = queryset.filter(status=Content.Status.PUBLISHED).update(
            status=Content.Status.DRAFT
        )
        self.message_user(request, f"{count} item(s) moved back to draft.")
