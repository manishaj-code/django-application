import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .validators import validate_file_size, validate_image_extension


def unique_slugify(instance, value, max_length):
    """Return a slug for ``value`` not used by any other row of the model."""
    base = slugify(value)[: max_length - 8].strip("-") or "item"
    slug = base
    others = type(instance)._default_manager.exclude(pk=instance.pk)
    suffix = 2
    while others.filter(slug=slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def content_image_upload_to(instance, filename):
    """Store uploads under a random name so user file names never leak."""
    ext = Path(filename).suffix.lower()
    return f"content/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{ext}"


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CategoryQuerySet(models.QuerySet):
    def with_published_counts(self):
        now = timezone.now()
        return self.annotate(
            published_count=Count(
                "contents",
                filter=Q(
                    contents__status=Content.Status.PUBLISHED,
                    contents__published_at__lte=now,
                ),
            )
        )


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        help_text="Used in URLs. Leave blank to generate it from the name.",
    )
    description = models.TextField(blank=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.slug and self.name:
            self.slug = unique_slugify(self, self.name, self._meta.get_field("slug").max_length)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, self._meta.get_field("slug").max_length)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{reverse('content:list')}?category={self.slug}"


class ContentQuerySet(models.QuerySet):
    def published(self):
        """Items the public may see: published and not scheduled for later."""
        return self.filter(status=Content.Status.PUBLISHED, published_at__lte=timezone.now())


class Content(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        help_text="Used in URLs. Leave blank to generate it from the title.",
    )
    summary = models.CharField(
        max_length=300, blank=True, help_text="Short teaser shown on listing cards."
    )
    body = models.TextField(help_text="Plain text. Blank lines start new paragraphs.")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contents",
    )
    featured_image = models.ImageField(
        upload_to=content_image_upload_to,
        blank=True,
        validators=[validate_image_extension, validate_file_size],
        help_text="Optional. JPG, PNG, WebP or GIF, up to the configured size limit.",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set automatically on first publish. A future date schedules the item.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="contents",
    )

    objects = ContentQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "content item"
        verbose_name_plural = "content"
        indexes = [
            models.Index(fields=["status", "-published_at"], name="content_status_pub_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["draft", "published"]),
                name="content_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(status="draft") | Q(published_at__isnull=False),
                name="content_published_has_date",
                violation_error_message="Published content needs a publication date.",
            ),
        ]

    def __str__(self):
        return self.title

    def _fill_defaults(self):
        if not self.slug and self.title:
            self.slug = unique_slugify(self, self.title, self._meta.get_field("slug").max_length)
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()

    def clean(self):
        super().clean()
        self._fill_defaults()

    def save(self, *args, **kwargs):
        self._fill_defaults()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("content:detail", kwargs={"slug": self.slug})

    @property
    def is_public(self):
        return (
            self.status == self.Status.PUBLISHED
            and self.published_at is not None
            and self.published_at <= timezone.now()
        )

    @property
    def is_scheduled(self):
        return (
            self.status == self.Status.PUBLISHED
            and self.published_at is not None
            and self.published_at > timezone.now()
        )
