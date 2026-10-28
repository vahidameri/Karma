from decimal import ROUND_HALF_UP, Decimal, localcontext

import jdatetime
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounting.services import open_period
from catalog.models import CodeSequence
from core.models import AuditEntry, OutboxEvent
from core.services import require, require_scope

from .models import Document


def require_document_action(actor, document, action):
    from core.services import permissions_for

    code = f"sales.document.{action}"
    require(actor, code if code in permissions_for(actor) else f"sales.{document.kind}.{action}")


PREFIX = {
    "request": "REQ",
    "quote": "PRF",
    "supply": "SUP",
    "invoice": "INV",
    "return": "RET",
    "purchase": "PUR",
    "purchase_return": "RPU",
    "packing": "PKL",
}


@transaction.atomic
def issue_document(document, actor):
    from core.services import lock_business_unit

    lock_business_unit(document.business_unit_id)
    doc = Document.objects.select_for_update().select_related("customer").get(pk=document.pk)
    if doc.business_unit_id != document.business_unit_id:
        raise ValidationError("واحد سند تغییر کرده است؛ سند را دوباره بارگذاری کنید")
    require_document_action(actor, doc, "issue")
    require_scope(actor, doc.business_unit_id, doc.created_by_id)
    if doc.status != "draft":
        raise ValidationError("سند قبلاً صادر شده است")
    if doc.customer.business_unit_id != doc.business_unit_id:
        raise ValidationError("مشتری متعلق به واحد دیگری است")
    open_period(doc.business_unit_id, doc.doc_date)
    delta = (timezone.localdate() - doc.doc_date).days
    if delta < 0 or delta > 0:
        require(actor, "sales.invoice.backdate")
    if doc.kind in ["return", "purchase_return"]:
        expected = "invoice" if doc.kind == "return" else "purchase"
        if not doc.parent_id or doc.parent.kind != expected or doc.parent.status != "issued":
            raise ValidationError("فاکتور مبدأ معتبر لازم است")
        Document.objects.select_for_update().get(pk=doc.parent_id)
        if doc.tax_rate != doc.parent.tax_rate:
            raise ValidationError("نرخ مالیات باید با فاکتور مبدأ یکسان باشد")
    if doc.parent_id and doc.kind in ["invoice", "supply", "packing", "quote"]:
        parent = Document.objects.select_for_update().get(pk=doc.parent_id)
        allowed_parents = {
            "invoice": {"quote": ["approved"], "supply": ["completed"]},
            "supply": {"quote": ["approved"]},
            "packing": {"invoice": ["issued"]},
            "quote": {"request": ["issued"], "quote": ["revised"]},
        }
        if parent.status not in allowed_parents.get(doc.kind, {}).get(parent.kind, []):
            raise ValidationError("سند مبدأ هنوز در وضعیت مجاز نیست")
        if (
            doc.kind == "invoice"
            and Document.objects.filter(
                business_unit=doc.business_unit,
                deal_number=parent.deal_number,
                kind="invoice",
                status="issued",
            )
            .exclude(pk=doc.pk)
            .exists()
        ):
            raise ValidationError("برای این معامله فاکتور فعال وجود دارد")
    lines = list(doc.lines.all())
    if not lines:
        raise ValidationError("حداقل یک ردیف لازم است")
    if not Decimal(0) <= doc.tax_rate <= Decimal(100) or doc.discount < 0 or doc.shipping < 0:
        raise ValidationError("مالیات و تخفیف نامعتبر")
    for line in lines:
        line.product_snapshot = {
            "system_code": line.product.system_code,
            "technical_code": line.product.technical_code,
            "name": line.product.name,
        }
        line.save(update_fields=["product_snapshot"])
    with localcontext() as context:
        context.prec = 64
        doc.subtotal = sum(
            (entry.quantity * entry.unit_price).quantize(Decimal(1), rounding=ROUND_HALF_UP)
            for entry in lines
        )
    from core.serializers import validate_money_precision

    validate_money_precision(doc.subtotal)
    if doc.subtotal >= 10**20:
        raise ValidationError("مبلغ سند از حد مجاز بیشتر است")
    if doc.discount > doc.subtotal:
        raise ValidationError("تخفیف بیشتر از مبلغ سند است")
    doc.tax = ((doc.subtotal - doc.discount) * doc.tax_rate / 100).quantize(
        Decimal(1), rounding=ROUND_HALF_UP
    )
    doc.total = doc.subtotal - doc.discount + doc.tax + doc.shipping
    validate_money_precision(doc.total)
    if doc.total >= 10**20 or doc.tax >= 10**20:
        raise ValidationError("مبلغ سند از حد مجاز بیشتر است")
    if doc.kind in ["invoice", "purchase", "return", "purchase_return"] and doc.total <= 0:
        raise ValidationError("مبلغ سند مالی باید مثبت باشد")
    if doc.kind in ["return", "purchase_return"]:
        from django.db.models import Sum

        previous = Document.objects.filter(parent=doc.parent, kind=doc.kind, status="issued")
        if doc.total + (previous.aggregate(n=Sum("total"))["n"] or 0) > doc.parent.total:
            raise ValidationError("مبلغ برگشت از مانده فاکتور بیشتر است")
        for line in lines:
            original = (
                doc.parent.lines.filter(product=line.product).aggregate(n=Sum("quantity"))["n"] or 0
            )
            from .models import DocumentLine

            returned = (
                DocumentLine.objects.filter(document__in=previous, product=line.product).aggregate(
                    n=Sum("quantity")
                )["n"]
                or 0
            )
            requested = sum(item.quantity for item in lines if item.product_id == line.product_id)
            if requested + returned > original:
                raise ValidationError("تعداد برگشتی بیش از فاکتور است")
    key = f"deal:{doc.business_unit_id}"
    CodeSequence.objects.get_or_create(name=key, defaults={"value": 0})
    seq = CodeSequence.objects.select_for_update().get(name=key)
    if doc.parent_id and doc.parent.deal_number:
        doc.deal_number = doc.parent.deal_number
    else:
        seq.value += 1
        seq.save(update_fields=["value"])
        day = jdatetime.date.fromgregorian(date=doc.doc_date).strftime("%Y%m%d")
        doc.deal_number = f"{doc.business_unit_id}-{day}-{seq.value:04d}"
    base_number = PREFIX[doc.kind] + "-" + doc.deal_number
    existing_count = (
        Document.objects.filter(
            business_unit=doc.business_unit, deal_number=doc.deal_number, kind=doc.kind
        )
        .exclude(pk=doc.pk)
        .exclude(number=None)
        .count()
    )
    doc.number = base_number + (f"-{existing_count}" if existing_count else "")
    doc.buyer_snapshot = {
        key: getattr(doc.customer, key)
        for key in [
            "name",
            "mobile",
            "national_id",
            "economic_code",
            "address",
            "city",
            "payment_terms",
        ]
    }
    doc.settings_snapshot = {
        "business_unit": doc.business_unit.name,
        "tax_rate": str(doc.tax_rate),
    }
    if doc.kind in ["invoice", "purchase", "return", "purchase_return"]:
        from accounting.models import PostingRule

        rule = PostingRule.objects.filter(business_unit=doc.business_unit, event=doc.kind).first()
        if not rule:
            raise ValidationError("قواعد ثبت این نوع سند تنظیم نشده است")
        doc.settings_snapshot["posting_rule"] = rule.lines
    doc.status = "sent" if doc.kind == "quote" else "issued"
    doc.issued_at = timezone.now()
    doc.save()
    if doc.kind in ["invoice", "purchase", "return", "purchase_return"]:
        OutboxEvent.objects.create(topic="InvoiceIssued", payload={"id": doc.pk})
    if doc.kind == "invoice" and doc.parent_id:
        ancestor = doc.parent
        for _ in range(4):
            if ancestor.kind == "quote":
                ancestor.status = "invoiced"
                ancestor.save(update_fields=["status"])
                break
            if not ancestor.parent_id:
                break
            ancestor = ancestor.parent
    AuditEntry.objects.create(actor=actor, action="sales.issue", target=str(doc.pk))
    return doc


@transaction.atomic
def void_document(document, actor):
    from core.services import lock_business_unit

    lock_business_unit(document.business_unit_id)
    from accounting.services import post_invoice_event, reverse_voucher
    from treasury.models import Allocation

    doc = Document.objects.select_for_update().get(pk=document.pk)
    require_document_action(actor, doc, "void")
    require_scope(actor, doc.business_unit_id, doc.created_by_id)
    if doc.status != "issued":
        raise ValidationError("فقط سند صادرشده قابل ابطال است")
    if (
        Allocation.objects.filter(document=doc, payment__void=False).exists()
        or Document.objects.filter(
            parent=doc, kind__in=["return", "purchase_return"], status="issued"
        ).exists()
    ):
        raise ValidationError("ابتدا دریافت‌ها یا برگشتی فعال را باطل کنید")
    if doc.kind in ["invoice", "purchase", "return", "purchase_return"]:
        voucher = post_invoice_event(doc.pk)
        reverse_voucher(voucher, actor, timezone.localdate())
    doc.status = "void"
    doc.save(update_fields=["status"])
    AuditEntry.objects.create(actor=actor, action="sales.void", target=str(doc.pk))
    return doc


@transaction.atomic
def change_quote_state(document, actor, target):
    doc = Document.objects.select_for_update().get(pk=document.pk)
    require_document_action(actor, doc, "approve")
    require_scope(actor, doc.business_unit_id, doc.created_by_id)
    if doc.kind != "quote" or doc.status != "sent" or target != "approved":
        raise ValidationError("این انتقال پیش‌فاکتور مجاز نیست")
    doc.status = target
    doc.save(update_fields=["status"])
    AuditEntry.objects.create(actor=actor, action="sales.quote.approved", target=str(doc.pk))
    return doc


@transaction.atomic
def convert_document(document, actor, kind):
    from .models import DocumentLine

    parent = Document.objects.select_for_update().get(pk=document.pk)
    require_scope(actor, parent.business_unit_id, parent.created_by_id)
    allowed = {
        "quote": {"approved": ["supply", "invoice"], "sent": ["quote"]},
        "supply": {"completed": ["invoice"]},
        "invoice": {"issued": ["packing", "return"]},
        "purchase": {"issued": ["purchase_return"]},
        "request": {"issued": ["quote"]},
    }
    if kind not in allowed.get(parent.kind, {}).get(parent.status, []):
        raise ValidationError("تبدیل این سند در وضعیت فعلی مجاز نیست")
    doc = Document(
        business_unit=parent.business_unit,
        customer=parent.customer,
        kind=kind,
        doc_date=timezone.localdate(),
        created_by=actor,
        parent=parent,
        deal_number=parent.deal_number,
        tax_rate=parent.tax_rate,
        discount=parent.discount,
        shipping=parent.shipping,
        notes=parent.notes,
    )
    require_document_action(actor, doc, "create")
    doc.save()
    DocumentLine.objects.bulk_create(
        [
            DocumentLine(
                document=doc,
                product=line.product,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                notes=line.notes,
            )
            for line in parent.lines.all()
        ]
    )
    if kind == "quote" and parent.kind == "quote":
        parent.status = "revised"
        parent.save(update_fields=["status"])
    AuditEntry.objects.create(actor=actor, action="sales.convert", target=f"{parent.pk}:{doc.pk}")
    return doc


@transaction.atomic
def fulfill_supply(document, actor, items, complete=False):
    from .models import DocumentLine

    doc = Document.objects.select_for_update().get(pk=document.pk)
    require_document_action(actor, doc, "fulfill")
    require_scope(actor, doc.business_unit_id, doc.created_by_id)
    if doc.kind != "supply" or doc.status not in ["draft", "issued"]:
        raise ValidationError("برگهٔ تأمین قفل است")
    # Issued document lines are immutable at the DB level. Supply progress is a separate entity.
    from .models import SupplyProgress

    for item in items:
        line = DocumentLine.objects.filter(pk=item["line"], document=doc).first()
        if not line or not 0 <= Decimal(str(item["quantity"])) <= line.quantity:
            raise ValidationError("مقدار تأمین نامعتبر است")
        SupplyProgress.objects.update_or_create(
            line=line,
            defaults={
                "quantity": item["quantity"],
                "source": item.get("source", ""),
                "notes": item.get("notes", ""),
                "updated_by": actor,
            },
        )
    if complete:
        if any(
            not hasattr(line, "progress") or line.progress.quantity < line.quantity
            for line in doc.lines.all()
        ):
            raise ValidationError("همه ردیف‌ها تأمین نشده‌اند")
        if doc.status == "draft":
            doc = issue_document(doc, actor)
        doc.status = "completed"
        doc.save(update_fields=["status"])
    return doc
