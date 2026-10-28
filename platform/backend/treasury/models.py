from django.db import models


class Payment(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    party = models.ForeignKey("crm.Party", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=0)
    direction = models.CharField(max_length=10, choices=[("receive", "دریافت"), ("send", "پرداخت")])
    account = models.ForeignKey("accounting.Account", on_delete=models.PROTECT)
    detail = models.JSONField(default=dict)
    doc_date = models.DateField()
    created_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    voucher = models.OneToOneField("accounting.Voucher", on_delete=models.PROTECT, null=True)
    void = models.BooleanField(default=False)


class Allocation(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT)
    document = models.ForeignKey("sales.Document", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["payment", "document"], name="unique_allocation"),
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="positive_allocation"),
        ]


class Cheque(models.Model):
    endorsed_to = models.ForeignKey(
        "crm.Party",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="endorsed_cheques",
    )
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    party = models.ForeignKey("crm.Party", on_delete=models.PROTECT)
    number = models.CharField(max_length=80)
    sayad_number = models.CharField(max_length=16, unique=True)
    bank = models.CharField(max_length=120)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=20, decimal_places=0)
    kind = models.CharField(
        max_length=12, choices=[("incoming", "دریافتی"), ("outgoing", "پرداختی")]
    )
    state = models.CharField(max_length=30, default="draft")
    created_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)


class ChequeTransition(models.Model):
    cheque = models.ForeignKey(Cheque, on_delete=models.PROTECT, related_name="transitions")
    source = models.CharField(max_length=30)
    target = models.CharField(max_length=30)
    voucher = models.ForeignKey("accounting.Voucher", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
