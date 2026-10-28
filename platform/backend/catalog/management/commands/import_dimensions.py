import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Standard


class Command(BaseCommand):
    help = "Import audited dimension tables for already-migrated standard identities"

    def add_arguments(self, parser):
        parser.add_argument("paths", nargs="+", type=Path)

    @transaction.atomic
    def handle(self, *args, **options):
        count = 0
        for path in options["paths"]:
            for code, dimensions in json.loads(path.read_text()).items():
                count += Standard.objects.filter(code=code).update(dimensions=dimensions)
        self.stdout.write(f"Updated dimensions on {count} standard records")
