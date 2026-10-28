"""Periodic inventory and fiscal closing. Account mappings are configured per unit."""

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from core.services import require, require_scope

from .models import Account, FiscalYear, Period, PostingRule, Voucher, VoucherLine
from .services import amount, post_voucher


@transaction.atomic
def close_year(year, actor, ending_inventory, next_period):
    from core.services import lock_business_unit

    lock_business_unit(year.business_unit_id)
    require(actor, "accounting.year.close")
    require_scope(actor, year.business_unit_id)
    year = FiscalYear.objects.select_for_update().get(pk=year.pk)
    if (
        year.closed
        or next_period.year.business_unit_id != year.business_unit_id
        or next_period.start <= year.end
    ):
        raise ValidationError("سال مقصد نامعتبر است")
    if Voucher.objects.filter(period__year=year, status__in=["draft", "temporary"]).exists():
        raise ValidationError("اسناد نهایی‌نشده وجود دارد")
    from treasury.models import Cheque

    if Cheque.objects.filter(business_unit=year.business_unit, state="draft").exists():
        raise ValidationError("چک بی‌وضعیت وجود دارد")
    from sales.models import Document

    issued = Document.objects.filter(
        business_unit=year.business_unit,
        doc_date__gte=year.start,
        doc_date__lte=year.end,
        status="issued",
        kind__in=["invoice", "purchase", "return", "purchase_return"],
    )
    posted = set(Voucher.objects.filter(period__year=year).values_list("source_key", flat=True))
    if any(f"document:{pk}" not in posted for pk in issued.values_list("pk", flat=True)):
        raise ValidationError("اسناد تجاری ثبت‌نشده در حسابداری وجود دارد")
    config = PostingRule.objects.get(business_unit=year.business_unit, event="year_close").lines
    required = {
        "inventory",
        "purchases",
        "purchase_returns",
        "purchase_freight",
        "cogs",
        "income_summary",
        "retained",
        "closing",
        "opening",
    }
    if not required.issubset(config):
        raise ValidationError("نگاشت بستن سال کامل نیست")
    accounts = {
        key: Account.objects.get(business_unit=year.business_unit, code=code)
        for key, code in config.items()
        if key in required
    }

    def balances():
        rows = (
            VoucherLine.objects.filter(voucher__period__year=year, voucher__status="permanent")
            .values("account_id", "party_id", "detail")
            .annotate(d=Sum("debit"), c=Sum("credit"))
        )
        return [(r, r["d"] - r["c"]) for r in rows if r["d"] != r["c"]]

    def line(account, value, row=None):
        result = {"account": account, "debit": max(value, 0), "credit": max(-value, 0)}
        if row:
            result.update(party=row["party_id"], detail=row["detail"])
        return result

    def post(label, lines, period=next_period, closing=False):
        if not lines:
            return None
        return post_voucher(
            unit_id=year.business_unit_id,
            date=year.end if closing else period.start,
            actor=actor,
            source_type=label,
            source_key=f"year:{year.pk}:{label}",
            lines=lines,
        )

    ending = amount(ending_inventory)
    if ending < 0:
        raise ValidationError("موجودی پایان دوره منفی نیست")
    before = balances()
    inventory = sum(v for r, v in before if r["account_id"] == accounts["inventory"].pk)
    purchases = sum(v for r, v in before if r["account_id"] == accounts["purchases"].pk)
    returns = -sum(v for r, v in before if r["account_id"] == accounts["purchase_returns"].pk)
    freight = sum(v for r, v in before if r["account_id"] == accounts["purchase_freight"].pk)
    # Freight is capitalized consistently with section 7.7; report it explicitly.
    include_freight = bool(config.get("include_purchase_freight", False))
    cogs = inventory + purchases + (freight if include_freight else 0) - returns - ending
    rows = []
    for r, value in before:
        if r["account_id"] in [
            accounts[k].pk
            for k in (
                ["inventory", "purchases", "purchase_returns", "purchase_freight"]
                if include_freight
                else ["inventory", "purchases", "purchase_returns"]
            )
        ]:
            rows.append(line(r["account_id"], -value, r))
    if ending:
        rows.append(line(accounts["inventory"].pk, ending))
    if cogs:
        rows.append(line(accounts["cogs"].pk, cogs))
    post("periodic_cogs", rows, closing=True)
    # Temporary accounts are explicitly configured, not inferred from hard-coded codes.
    temporary = set(config.get("temporary_accounts", []))
    if not temporary:
        raise ValidationError("حساب‌های موقت تعیین نشده‌اند")
    rows = []
    net = Decimal(0)
    for r, value in balances():
        code = Account.objects.get(pk=r["account_id"]).code
        if code in temporary:
            rows.append(line(r["account_id"], -value, r))
            net += value
    if net:
        rows.append(line(accounts["income_summary"].pk, net))
    post("close_temporary", rows, closing=True)
    if net:
        post(
            "transfer_profit",
            [line(accounts["income_summary"].pk, -net), line(accounts["retained"].pk, net)],
            closing=True,
        )
    permanent = balances()
    closing = []
    opening = []
    net = Decimal(0)
    for r, value in permanent:
        closing.append(line(r["account_id"], -value, r))
        opening.append(line(r["account_id"], value, r))
        net += value
    if net:
        raise ValidationError("مانده حساب‌های دائم تراز نیست")
    close = post("closing", closing, closing=True)
    opened = post("opening", opening)
    year.closed = True
    year.save(update_fields=["closed"])
    Period.objects.filter(year=year).update(closed=True)
    return {
        "cogs": str(cogs),
        "ending_inventory": str(ending),
        "freight": str(freight),
        "closing_voucher": close.pk if close else None,
        "opening_voucher": opened.pk if opened else None,
    }
