from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Sum
from rest_framework.exceptions import ValidationError

from core.models import AuditEntry

from .models import Account, Period, PostingRule, Voucher, VoucherLine

ZERO = Decimal(0)


def amount(value):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result != result.to_integral_value() or abs(result) >= 10**20:
            raise ValueError()
        from core.serializers import validate_money_precision

        validate_money_precision(result)
        return result
    except ValidationError:
        raise
    except Exception:
        raise ValidationError("مبلغ باید ریال صحیح باشد")


def open_period(unit_id, date):
    periods = Period.objects.filter(
        year__business_unit_id=unit_id,
        year__closed=False,
        closed=False,
        start__lte=date,
        end__gte=date,
        year__start__lte=date,
        year__end__gte=date,
    )
    if periods.count() != 1:
        raise ValidationError("تاریخ باید در یک دورهٔ مالی باز و یکتا باشد")
    return periods.get()


@transaction.atomic
def post_voucher(*, unit_id, date, actor, source_type, source_key, lines, reverse=None):
    existing = Voucher.objects.filter(source_key=source_key).first()
    if existing:
        if existing.business_unit_id != unit_id:
            raise ValidationError("کلید تکرار متعلق به واحد دیگری است")
        return existing
    from core.services import lock_business_unit

    lock_business_unit(unit_id)
    period = open_period(unit_id, date)
    from .models import FiscalYear

    FiscalYear.objects.select_for_update().get(pk=period.year_id)
    period = open_period(unit_id, date)
    existing = Voucher.objects.filter(source_key=source_key).first()
    if existing:
        if existing.business_unit_id != unit_id:
            raise ValidationError("کلید تکرار متعلق به واحد دیگری است")
        return existing
    normalized = []
    for line in lines:
        account = Account.objects.get(pk=line["account"])
        if account.business_unit_id != unit_id or not account.active:
            raise ValidationError("حساب نامعتبر")
        debit, credit = amount(line.get("debit", 0)), amount(line.get("credit", 0))
        if not ((debit > 0 and credit == 0) or (credit > 0 and debit == 0)):
            raise ValidationError("هر ردیف باید فقط یک سمت مثبت داشته باشد")
        party = line.get("party")
        detail = line.get("detail", {})
        if not isinstance(detail, dict) or any(
            not isinstance(v, (str, int)) or not str(v).strip() or v == 0 for v in detail.values()
        ):
            raise ValidationError("تفصیلی خالی یا نامعتبر است")
        kinds = set(detail) | ({"party"} if party else set())
        if account.detail_required and not kinds.intersection(account.detail_kinds):
            raise ValidationError("تفصیلی اجباری حساب وارد نشده")
        if kinds - set(account.detail_kinds):
            raise ValidationError("نوع تفصیلی مجاز نیست")
        if party:
            from crm.models import Party

            if not Party.objects.filter(pk=party, business_unit_id=unit_id).exists():
                raise ValidationError("طرف حساب واحد دیگری است")
        normalized.append(
            dict(
                account=account,
                debit=debit,
                credit=credit,
                party_id=party,
                detail=detail,
                description=line.get("description", ""),
            )
        )
    if len(normalized) < 2 or sum(x["debit"] for x in normalized) != sum(
        x["credit"] for x in normalized
    ):
        raise ValidationError("سند تراز نیست")
    number = (
        Voucher.objects.filter(period__year_id=period.year_id).aggregate(n=Max("number"))["n"] or 0
    ) + 1
    v = Voucher.objects.create(
        business_unit_id=unit_id,
        period=period,
        number=number,
        doc_date=date,
        source_type=source_type,
        source_key=source_key,
        created_by=actor,
        reversed_voucher=reverse,
    )
    VoucherLine.objects.bulk_create([VoucherLine(voucher=v, **line) for line in normalized])
    v.status = "permanent"
    v.save(update_fields=["status"])
    AuditEntry.objects.create(actor=actor, action="accounting.post", target=str(v.pk))
    return v


@transaction.atomic
def reverse_voucher(voucher, actor, date):
    return post_voucher(
        unit_id=voucher.business_unit_id,
        date=date,
        actor=actor,
        source_type="reversal",
        source_key=f"reverse:{voucher.pk}",
        reverse=voucher,
        lines=[
            dict(
                account=entry.account_id,
                debit=entry.credit,
                credit=entry.debit,
                party=entry.party_id,
                detail=entry.detail,
            )
            for entry in voucher.lines.all()
        ],
    )


def post_invoice_event(document_id):
    from sales.models import Document

    doc = Document.objects.select_related("created_by").get(pk=document_id)
    rule_lines = doc.settings_snapshot.get("posting_rule")
    if rule_lines is None:
        rule_lines = PostingRule.objects.get(business_unit=doc.business_unit, event=doc.kind).lines
    values = {
        "total": doc.total,
        "subtotal": doc.subtotal,
        "net": doc.subtotal - doc.discount,
        "discount": doc.discount,
        "tax": doc.tax,
        "shipping": doc.shipping,
    }
    lines = []
    for item in rule_lines:
        value = values[item["amount"]]
        if value <= 0:
            continue
        account = Account.objects.get(business_unit=doc.business_unit, code=item["account"])
        line = {"account": account.pk, item["side"]: value}
        if item.get("party"):
            line["party"] = doc.customer_id
        lines.append(line)
    return post_voucher(
        unit_id=doc.business_unit_id,
        date=doc.doc_date,
        actor=doc.created_by,
        source_type=doc.kind,
        source_key=f"document:{doc.pk}",
        lines=lines,
    )


def trial_balance(unit_id, owner_id=None):
    qs = VoucherLine.objects.filter(
        voucher__business_unit_id=unit_id,
        voucher__status__in=["temporary", "permanent"],
    )
    if owner_id:
        qs = qs.filter(voucher__created_by_id=owner_id)
    from django.db import connection

    if connection.vendor == "sqlite":
        # SQLite's Decimal aggregate converter has only 15 significant digits.
        # Accepted individual amounts remain exact; sum them in Decimal in development.
        totals = {}
        for row in qs.values("account__code", "account__name", "debit", "credit"):
            key = (row["account__code"], row["account__name"])
            result = totals.setdefault(
                key,
                {
                    "account__code": key[0],
                    "account__name": key[1],
                    "debit": Decimal(0),
                    "credit": Decimal(0),
                },
            )
            result["debit"] += row["debit"]
            result["credit"] += row["credit"]
        return [totals[key] for key in sorted(totals)]
    return list(
        qs.values("account__code", "account__name")
        .annotate(debit=Sum("debit"), credit=Sum("credit"))
        .order_by("account__code")
    )
