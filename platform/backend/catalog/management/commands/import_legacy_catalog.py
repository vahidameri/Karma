import csv
import hashlib
import io
import json
import re
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image

from catalog.models import Asset, CodeSequence, Product, ProductAlias, Standard
from catalog.services import technical_code
from core.models import OutboxEvent


def clean(value):
    return "" if value in ["—", "-", ""] else value


class Command(BaseCommand):
    help = "Import the supplied v1.3 export, preserving every KR code; rejects conflicting data"

    def add_arguments(self, parser):
        parser.add_argument("--source", type=Path, required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        source = options["source"]
        rows = list(csv.DictReader((source / "skus.csv").open(encoding="utf-8-sig")))
        if len(rows) != len({r["کد محصول"] for r in rows}) or len(rows) != len(
            {r["کد فنی"] for r in rows}
        ):
            raise CommandError("Duplicate legacy identifiers")
        CodeSequence.objects.get_or_create(name="product")
        seq = CodeSequence.objects.select_for_update().get(name="product")
        standards = {}
        for row in csv.DictReader((source / "standards.csv").open(encoding="utf-8-sig")):
            obj, _ = Standard.objects.update_or_create(
                code=row["شناسه"], defaults={"name": row["نام فارسی"]}
            )
            standards[row["استاندارد"]] = obj
        manifest = json.loads((source / "manifest.json").read_text())["images"]
        assets = {}
        for name, digest in manifest.items():
            if Path(name).name != name:
                raise CommandError("Invalid asset path")
            raw = (source / "images" / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != digest:
                raise CommandError("Asset checksum failed")
            with Image.open(io.BytesIO(raw)) as image:
                image.verify()
                content_type = Image.MIME.get(image.format, "")
            if content_type not in ["image/png", "image/webp", "image/jpeg"]:
                raise CommandError("Unsupported asset type")
            asset, created = Asset.objects.get_or_create(
                digest=digest, defaults={"content_type": content_type}
            )
            canonical = f"assets/{digest}{Path(name).suffix}"
            if default_storage.exists(canonical):
                with default_storage.open(canonical, "rb") as existing_file:
                    if hashlib.sha256(existing_file.read()).hexdigest() != digest:
                        raise CommandError("Stored asset checksum failed")
                if asset.file.name != canonical:
                    asset.file.name = canonical
                    asset.save(update_fields=["file"])
            elif created or not asset.file or not asset.file.storage.exists(asset.file.name):
                asset.file.save(digest + Path(name).suffix, ContentFile(raw), save=True)
            assets[name] = asset
        mapping = json.loads((source / "asset-map.json").read_text())
        for standard in standards.values():
            data = mapping.get(standard.code, {})
            if data.get("p") in assets:
                standard.photo = assets[data["p"]]
            if data.get("d") in assets:
                standard.drawing = assets[data["d"]]
            standard.save(update_fields=["photo", "drawing"])
        existing = {p.system_code: p for p in Product.objects.all()}
        technical = {p.technical_code: p.system_code for p in existing.values()}
        new = []
        aliases = []
        max_code = seq.value
        canonical_seen = {}
        for row in rows:
            kr = row["کد محصول"]
            old = row["کد فنی"]
            if not re.fullmatch(r"KR-\d+", kr):
                raise CommandError("Invalid KR identifier")
            attrs = dict(
                standard=standards[row["استاندارد"]],
                name=row["نام کالا"],
                size=clean(row["سایز"]),
                length=clean(row["طول"]),
                grade=clean(row["گرید"]),
                finish=clean(row["پوشش"]),
            )
            tech = technical_code(
                attrs["standard"], attrs["size"], attrs["length"], attrs["grade"], attrs["finish"]
            )
            if tech in canonical_seen and canonical_seen[tech] != kr:
                raise CommandError("Canonical code collision requires manual review")
            canonical_seen[tech] = kr
            if tech in technical and technical[tech] != kr:
                raise CommandError(
                    "A technical code is already assigned to another KR; use a clean migration database"
                )
            product = existing.get(kr)
            if product and product.technical_code != tech:
                raise CommandError(
                    "KR code already identifies another product; use a clean migration database"
                )
            if not product:
                product = Product(system_code=kr, technical_code=tech, **attrs)
                new.append(product)
            if old != tech:
                aliases.append((old, product))
            max_code = max(max_code, int(kr[3:]))
        Product.objects.bulk_create(new, batch_size=500)
        for code, product in aliases:
            obj, created = ProductAlias.objects.get_or_create(
                code=code, defaults={"product": product}
            )
            if obj.product_id != product.pk:
                raise CommandError("Legacy alias collision")
        seq.value = max_code
        seq.save(update_fields=["value"])
        OutboxEvent.objects.bulk_create(
            [OutboxEvent(topic="ProductCreated", payload={"id": p.pk}) for p in new], batch_size=500
        )
        after = set(
            Product.objects.filter(system_code__in=[r["کد محصول"] for r in rows]).values_list(
                "system_code", flat=True
            )
        )
        if after != {r["کد محصول"] for r in rows}:
            raise CommandError("KR reconciliation failed")
        self.stdout.write(
            f"Legacy reconciliation: before={len(rows)} after={len(after)}; created={len(new)}; aliases={len(aliases)}; images={len(assets)}"
        )
