from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from accounting.models import Account, PostingRule
from accounting.services import post_voucher
from core.services import require, require_scope

from .models import Payslip


def rial(value):
    return value.quantize(Decimal(1), rounding=ROUND_HALF_UP)


def calculate(contract, policy, work_days, paid_days, overtime_hours):
    rates = policy.rates
    if not 1 <= work_days <= 31 or not 0 <= paid_days <= work_days or overtime_hours < 0:
        raise ValidationError("کارکرد نامعتبر است")
    if contract.monthly_salary < 0 or contract.allowances < 0 or contract.hourly_overtime < 0:
        raise ValidationError("مبالغ قرارداد نامعتبر است")
    gross = rial(
        (contract.monthly_salary + contract.allowances) * paid_days / work_days
        + contract.hourly_overtime * overtime_hours
    )
    er = Decimal(str(rates["employee_insurance_rate"]))
    orr = Decimal(str(rates["employer_insurance_rate"]))
    cap = Decimal(str(rates["insurance_cap"]))
    if not 0 <= er <= 1 or not 0 <= orr <= 1 or cap < 0:
        raise ValidationError("نرخ بیمه نامعتبر است")
    insurance_base = min(gross, cap)
    employee = rial(insurance_base * er)
    employer = rial(insurance_base * orr)
    taxable = (
        max(Decimal(0), gross - employee)
        if rates.get("deduct_employee_insurance_from_tax", False)
        else gross
    )
    last = Decimal(0)
    tax = Decimal(0)
    for bracket in rates["tax_brackets"]:
        upper = Decimal(str(bracket["up_to"])) if bracket["up_to"] is not None else taxable
        rate = Decimal(str(bracket["rate"]))
        if not 0 <= rate <= 1 or (bracket["up_to"] is not None and upper <= last):
            raise ValidationError("پله‌های مالیات نامعتبر است")
        tax += max(Decimal(0), min(taxable, upper) - last) * rate
        last = upper
        if taxable <= upper:
            break
    tax = rial(tax)
    if employee + tax > gross:
        raise ValidationError("کسورات بیش از حقوق است")
    return dict(
        gross=gross,
        employee_insurance=employee,
        employer_insurance=employer,
        tax=tax,
        net=gross - employee - tax,
    )


@transaction.atomic
def issue_payslip(slip, actor):
    from core.services import lock_business_unit

    lock_business_unit(slip.business_unit_id)
    require(actor, "payroll.payslip.issue")
    require_scope(actor, slip.business_unit_id, slip.created_by_id)
    slip = Payslip.objects.select_for_update().select_related("contract", "policy").get(pk=slip.pk)
    if slip.voucher_id:
        raise ValidationError("فیش قبلاً صادر شده")
    if (
        slip.contract.business_unit_id != slip.business_unit_id
        or slip.policy.business_unit_id != slip.business_unit_id
    ):
        raise ValidationError("واحد قرارداد و نرخ‌ها متفاوت است")
    if not slip.policy.year.start <= slip.doc_date <= slip.policy.year.end:
        raise ValidationError("نرخ‌ها متعلق به سال دیگری هستند")
    values = calculate(
        slip.contract, slip.policy, slip.work_days, slip.paid_days, slip.overtime_hours
    )
    rule = PostingRule.objects.get(business_unit=slip.business_unit, event="payroll")
    lines = []
    for item in rule.lines:
        value = (
            values["employee_insurance"] + values["employer_insurance"]
            if item["amount"] == "total_insurance"
            else values[item["amount"]]
        )
        if not value:
            continue
        account = Account.objects.get(business_unit=slip.business_unit, code=item["account"])
        line = {"account": account.pk, item["side"]: value}
        if item.get("party"):
            line["party"] = slip.contract.employee_id
        lines.append(line)
    slip.voucher = post_voucher(
        unit_id=slip.business_unit_id,
        date=slip.doc_date,
        actor=actor,
        source_type="payroll",
        source_key=f"payroll:{slip.pk}",
        lines=lines,
    )
    for key, value in values.items():
        setattr(slip, key, value)
    slip.policy_snapshot = slip.policy.rates
    slip.save()
    return slip
