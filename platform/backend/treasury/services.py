from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from accounting.models import Account, PostingRule
from accounting.services import amount, post_voucher
from core.services import require, require_scope

from .models import Allocation, Cheque, Payment


@transaction.atomic
def create_payment(actor, allocations, **data):
    from core.services import lock_business_unit

    lock_business_unit(data["business_unit"].pk)
    from sales.models import Document

    require(actor, "treasury.payment.create")
    require_scope(actor, data["business_unit"].pk, actor.pk)
    if data["party"].business_unit_id != data["business_unit"].pk:
        raise ValidationError("طرف حساب واحد دیگری است")
    require_scope(actor, data["business_unit"].pk, data["party"].created_by_id)
    value = amount(data["amount"])
    if value <= 0:
        raise ValidationError("مبلغ باید مثبت باشد")
    payment = Payment.objects.create(created_by=actor, **data)
    rule = PostingRule.objects.get(
        business_unit=payment.business_unit,
        event="receive" if payment.direction == "receive" else "send",
    )
    counter = Account.objects.get(
        business_unit=payment.business_unit, code=rule.lines[0]["account"]
    )
    bank_side = "debit" if payment.direction == "receive" else "credit"
    other_side = "credit" if bank_side == "debit" else "debit"
    payment.voucher = post_voucher(
        unit_id=payment.business_unit_id,
        date=payment.doc_date,
        actor=actor,
        source_type="payment",
        source_key=f"payment:{payment.pk}",
        lines=[
            {"account": payment.account_id, bank_side: value, "detail": payment.detail},
            {"account": counter.pk, other_side: value, "party": payment.party_id},
        ],
    )
    used = 0
    for item in sorted(allocations, key=lambda x: x["document"]):
        doc = Document.objects.select_for_update().get(pk=item["document"])
        require_scope(actor, doc.business_unit_id, doc.created_by_id)
        allocation = amount(item["amount"])
        allowed_kind = "invoice" if payment.direction == "receive" else "purchase"
        if (
            doc.kind != allowed_kind
            or doc.status != "issued"
            or doc.customer_id != payment.party_id
            or doc.business_unit_id != payment.business_unit_id
        ):
            raise ValidationError("فاکتور نامعتبر برای تخصیص")
        paid = (
            Allocation.objects.filter(document=doc, payment__void=False).aggregate(n=Sum("amount"))[
                "n"
            ]
            or 0
        )
        used += allocation
        if allocation <= 0 or paid + allocation > doc.total or used > value:
            raise ValidationError("تخصیص بیش از مانده است")
        Allocation.objects.create(payment=payment, document=doc, amount=allocation)
    payment.save(update_fields=["voucher"])
    return payment


TRANSITIONS = {
    "incoming": {
        "draft": ["held"],
        "held": ["collecting", "endorsed", "cleared", "bounced"],
        "collecting": ["cleared", "bounced"],
        "bounced": ["settled", "collecting", "held"],
    },
    "outgoing": {
        "draft": ["issued"],
        "issued": ["cleared", "bounced"],
        "bounced": ["issued"],
    },
}


@transaction.atomic
def transition_cheque(cheque, actor, target, date):
    from core.services import lock_business_unit

    lock_business_unit(cheque.business_unit_id)
    from accounting.services import reverse_voucher

    from .models import ChequeTransition

    require(actor, "treasury.cheque.transition")
    require_scope(actor, cheque.business_unit_id, cheque.created_by_id)
    cheque = Cheque.objects.select_for_update().get(pk=cheque.pk)
    if target not in TRANSITIONS[cheque.kind].get(cheque.state, []):
        raise ValidationError("انتقال وضعیت چک مجاز نیست")
    if cheque.state == "bounced" and target in ["held", "collecting", "issued"]:
        last = cheque.transitions.order_by("-pk").first()
        if not last or last.target != "bounced" or last.source != target:
            raise ValidationError("وضعیت قبلی با لغو برگشت منطبق نیست")
        voucher = reverse_voucher(last.voucher, actor, date)
    else:
        event = f"cheque.{cheque.kind}.{cheque.state}.{target}"
        rule = PostingRule.objects.get(business_unit=cheque.business_unit, event=event)
        lines = []
        for line in rule.lines:
            account = Account.objects.get(business_unit=cheque.business_unit, code=line["account"])
            item = {"account": account.pk, line["side"]: cheque.amount}
            if "party" in account.detail_kinds:
                if line.get("beneficiary"):
                    if (
                        not cheque.endorsed_to_id
                        or cheque.endorsed_to.business_unit_id != cheque.business_unit_id
                    ):
                        raise ValidationError("گیرندهٔ واگذاری تعیین نشده است")
                    item["party"] = cheque.endorsed_to_id
                else:
                    item["party"] = cheque.party_id
            item["detail"] = {}
            if "cheque" in account.detail_kinds:
                item["detail"]["cheque"] = cheque.pk
            if "bank_account" in account.detail_kinds:
                item["detail"]["bank_account"] = cheque.bank
            lines.append(item)
        n = cheque.transitions.count()
        voucher = post_voucher(
            unit_id=cheque.business_unit_id,
            date=date,
            actor=actor,
            source_type=event,
            source_key=f"cheque:{cheque.pk}:{n}",
            lines=lines,
        )
    ChequeTransition.objects.create(
        cheque=cheque, source=cheque.state, target=target, voucher=voucher
    )
    cheque.state = target
    cheque.save(update_fields=["state"])
    return cheque


@transaction.atomic
def void_payment(payment, actor, date):
    from core.services import lock_business_unit

    lock_business_unit(payment.business_unit_id)
    from accounting.services import reverse_voucher

    require(actor, "treasury.payment.void")
    require_scope(actor, payment.business_unit_id, payment.created_by_id)
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.void:
        return payment
    if not payment.voucher_id:
        raise ValidationError("سند حسابداری دریافت/پرداخت ثبت نشده است")
    reverse_voucher(payment.voucher, actor, date)
    payment.void = True
    payment.save(update_fields=["void"])
    return payment
