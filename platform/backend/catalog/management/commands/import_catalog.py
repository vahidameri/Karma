import json
import re
from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import CodeSequence, Product, ProductAlias, Standard
from catalog.services import technical_code
from core.models import OutboxEvent


def atom(value):
    return str(value).strip() if value is not None else ""


class Command(BaseCommand):
    help = "Import DIN and ASTM source workbooks idempotently. Never replaces existing KR codes."

    def add_arguments(self, parser):
        parser.add_argument("--source", type=Path, required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        source = options["source"]
        entries = []
        dimensions = json.loads((source / "output/DIN_full_tables.json").read_text())
        wb = openpyxl.load_workbook(
            source / "output/DIN_SKU_list.xlsx", read_only=True, data_only=True
        )
        standards = {}
        for row in list(wb["Parents"].values)[1:]:
            standard, _ = Standard.objects.update_or_create(
                code=row[0],
                defaults={"name": row[2] or "", "dimensions": dimensions.get(row[0], {})},
            )
            standards[row[0]] = standard
        for row in list(wb["SKUs"].values)[1:]:
            entries.append(
                (
                    dict(
                        standard=standards[row[1]],
                        name=row[2],
                        size=atom(row[7]),
                        length=atom(row[8]),
                        grade="",
                        finish="",
                    ),
                    row[0],
                )
            )
        wb.close()
        astm = source / "astm/پیچ و مهره ASTM.xlsx"
        if astm.exists():
            wb = openpyxl.load_workbook(astm, read_only=True, data_only=True)
            for row in list(wb["کدهای کالا"].values)[1:]:
                code = re.sub(r"\s+", "", row[3]).upper()
                standard, _ = Standard.objects.get_or_create(
                    code=code,
                    defaults={
                        "name": row[5],
                        "dimensions": {
                            "source": "astm/پیچ و مهره ASTM.xlsx",
                            "drawings": atom(row[14]),
                        },
                    },
                )
                entries.append(
                    (
                        dict(
                            standard=standard,
                            name=row[2],
                            size=atom(row[6]),
                            length=atom(row[8]),
                            grade=atom(row[4]),
                            finish="",
                        ),
                        row[0],
                    )
                )
            wb.close()
        # Acquire the shared namespace lock once, reserve all codes, then insert in batches.
        CodeSequence.objects.get_or_create(name="product")
        seq = CodeSequence.objects.select_for_update().get(name="product")
        existing = {p.technical_code: p for p in Product.objects.all()}
        aliases = {a.code: a.product_id for a in ProductAlias.objects.all()}
        largest = max(
            [
                int(p.system_code[3:])
                for p in existing.values()
                if re.fullmatch(r"KR-\d+", p.system_code)
            ]
            + [seq.value]
        )
        seq.value = largest
        new = []
        pending_aliases = []
        for attrs, source_code in entries:
            tech = technical_code(
                attrs["standard"], attrs["size"], attrs["length"], attrs["grade"], attrs["finish"]
            )
            if tech in aliases and tech not in existing:
                raise CommandError(f"Alias collision for {tech}; review source data")
            product = existing.get(tech)
            if not product:
                seq.value += 1
                product = Product(system_code=f"KR-{seq.value}", technical_code=tech, **attrs)
                new.append(product)
                existing[tech] = product
            if source_code != tech:
                pending_aliases.append((source_code, product))
        Product.objects.bulk_create(new, batch_size=500)
        seq.save(update_fields=["value"])
        to_add = []
        for code, product in pending_aliases:
            if code in existing and existing[code].pk != product.pk:
                raise CommandError("Source alias conflicts with a technical code")
            if code in aliases:
                if aliases[code] != product.pk:
                    raise CommandError("Source alias points at another product")
                continue
            to_add.append(ProductAlias(code=code, product=product))
            aliases[code] = product.pk
        ProductAlias.objects.bulk_create(to_add, batch_size=500)
        OutboxEvent.objects.bulk_create(
            [OutboxEvent(topic="ProductCreated", payload={"id": p.pk}) for p in new], batch_size=500
        )
        self.stdout.write(
            f"Imported {len(new)} products; total={Product.objects.count()}; source aliases={len(to_add)}. Legacy KR data was not supplied; staging codes must be reconciled before production migration."
        )
