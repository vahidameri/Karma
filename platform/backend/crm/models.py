from django.db import models


class Party(models.Model):
    name = models.CharField(max_length=200)
    kind = models.CharField(
        max_length=12,
        choices=[("person", "حقیقی"), ("company", "حقوقی")],
        default="person",
    )
    mobile = models.CharField(max_length=20, unique=True, null=True, blank=True)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    economic_code = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    payment_terms = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    custom_fields = models.JSONField(default=dict)
    created_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)

    def __str__(self):
        return self.name
