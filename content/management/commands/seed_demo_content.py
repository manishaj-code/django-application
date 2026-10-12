from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from content.models import Category, Content

CATEGORIES = {
    "News": "Announcements and updates.",
    "Guides": "Step-by-step how-to articles.",
    "Events": "Upcoming and past events.",
}

BODY = (
    "This is demonstration content created by the seed_demo_content command.\n\n"
    "Replace or delete it from the admin panel once you start adding real content.\n\n"
    "Paragraphs are separated by a blank line, and single line breaks are kept."
)


class Command(BaseCommand):
    help = "Create sample categories and content for local testing (safe to run repeatedly)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=15, help="Number of items to create.")

    @transaction.atomic
    def handle(self, *args, count, **options):
        categories = []
        for name, description in CATEGORIES.items():
            category, _ = Category.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            categories.append(category)

        now = timezone.now()
        created = 0
        for i in range(1, count + 1):
            title = f"Sample article {i}"
            if Content.objects.filter(title=title).exists():
                continue
            Content.objects.create(
                title=title,
                summary=f"A short summary for sample article {i}.",
                body=BODY,
                category=categories[i % len(categories)],
                status=Content.Status.DRAFT if i % 7 == 0 else Content.Status.PUBLISHED,
                published_at=None if i % 7 == 0 else now - timedelta(hours=i),
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} sample item(s)."))
