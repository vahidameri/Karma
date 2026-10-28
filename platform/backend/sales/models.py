from django.db import models


class Document(models.Model):
    TYPES = [
        ("request", "درخواست"),
        ("quote", "پیش‌فاکتور"),
        ("supply", "تأمین"),
        ("invoice", "فاکتور فروش"),
        ("return", "برگشت فروش"),
        ("purchase", "فاکتور خرید"),
        ("purchase_return", "برگشت خرید"),
        ("packing", "بسته‌بندی"),
    ]
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    customer = models.ForeignKey("crm.Party", on_delete=models.PROTECT)
    kind = models.CharField(max_length=20, choices=TYPES)
    status = models.CharField(max_length=20, default="draft")
    doc_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    issued_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT)
    deal_number = models.CharField(max_length=80, null=True, blank=True)
    number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    buyer_snapshot = models.JSONField(default=dict)
    settings_snapshot = models.JSONField(default=dict)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    shipping = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    subtotal = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    tax = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    total = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    notes = models.TextField(blank=True)


class DocumentLine(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    product_snapshot = models.JSONField(default=dict)
    description = models.CharField(max_length=300, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=3)
    unit_price = models.DecimalField(max_digits=20, decimal_places=0)
    supplied_quantity = models.DecimalField(max_digits=18, decimal_places=3, default=0)
    supply_source = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0, unit_price__gte=0),
                name="positive_invoice_line",
            )
        ]


class Inquiry(models.Model):
    name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=11)
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    items = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class InquiryQuota(models.Model):
    mobile = models.CharField(max_length=11)
    day = models.DateField()
    count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["mobile", "day"], name="unique_daily_inquiry_quota")
        ]


class SupplyProgress(models.Model):
    line = models.OneToOneField(DocumentLine, on_delete=models.PROTECT, related_name="progress")
    quantity = models.DecimalField(max_digits=18, decimal_places=3, default=0)
    source = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    updated_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)
