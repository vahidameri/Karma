from django.core.management.base import BaseCommand

from core.models import BusinessUnit, Capability


class Command(BaseCommand):
    help = "Create non-secret defaults; never creates accounts or passwords"

    def handle(self, *args, **kwargs):
        for name in ["کارما", "آلیاژ پیچ کار ماد"]:
            BusinessUnit.objects.get_or_create(name=name)
        codes = [
            "catalog.product.create",
            "catalog.product.edit",
            "catalog.price.view_cost",
            "iam.role.manage",
        ]
        for code in codes:
            Capability.objects.get_or_create(code=code)
        self.stdout.write("Default units and base capabilities created (idempotent)")
