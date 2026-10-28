from django.db import models
from django.db.models import Q


class FiscalYear(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    name = models.CharField(max_length=80)
    start = models.DateField()
    end = models.DateField()
    closed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(end__gte=models.F("start")), name="year_dates_ordered"
            )
        ]


class Period(models.Model):
    year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT)
    start = models.DateField()
    end = models.DateField()
    closed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(end__gte=models.F("start")), name="period_dates_ordered"
            )
        ]


class Account(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=120)
    detail_kinds = models.JSONField(default=list)
    detail_required = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["business_unit", "code"], name="unique_account_code")
        ]

    def __str__(self):
        return f"{self.code} {self.name}"


class PostingRule(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    event = models.CharField(max_length=80)
    lines = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["business_unit", "event"], name="unique_posting_rule")
        ]


class Voucher(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    period = models.ForeignKey(Period, on_delete=models.PROTECT)
    number = models.PositiveBigIntegerField()
    doc_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=12,
        default="draft",
        choices=[("draft", "پیش‌نویس"), ("temporary", "موقت"), ("permanent", "دائم")],
    )
    source_type = models.CharField(max_length=80)
    source_key = models.CharField(max_length=120, unique=True)
    reversed_voucher = models.OneToOneField("self", null=True, blank=True, on_delete=models.PROTECT)
    created_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business_unit", "period", "number"],
                name="unique_voucher_number",
            )
        ]


class VoucherLine(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    party = models.ForeignKey("crm.Party", null=True, blank=True, on_delete=models.PROTECT)
    detail = models.JSONField(default=dict)
    debit = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    credit = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(debit__gt=0, credit=0) | Q(credit__gt=0, debit=0)),
                name="one_positive_side",
            )
        ]
