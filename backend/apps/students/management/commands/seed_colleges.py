"""Management command to seed initial approved institutional colleges."""

from django.core.management.base import BaseCommand
from apps.students.seeds import seed_default_colleges


class Command(BaseCommand):
    help = "Seed initial approved institutional colleges if not already present"

    def handle(self, *args, **options):
        count = seed_default_colleges()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully completed college seeding. {count} initial colleges created/verified."
            )
        )
