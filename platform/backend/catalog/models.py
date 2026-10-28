from django.db import models


class Standard(models.Model):
    photo = models.ForeignKey(
        "Asset", null=True, blank=True, on_delete=models.SET_NULL, related_name="standard_photos"
    )
    drawing = models.ForeignKey(
        "Asset", null=True, blank=True, on_delete=models.SET_NULL, related_name="standard_drawings"
    )
    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=250, blank=True)
    dimensions = models.JSONField(default=dict)

    def __str__(self):
        return self.code


class Product(models.Model):
    standard = models.ForeignKey(Standard, on_delete=models.PROTECT)
    system_code = models.CharField(max_length=40, unique=True)
    technical_code = models.CharField(max_length=180, unique=True)
    name = models.CharField(max_length=250)
    size = models.CharField(max_length=40)
    length = models.CharField(max_length=40, blank=True)
    grade = models.CharField(max_length=30, blank=True)
    finish = models.CharField(max_length=30, blank=True)
    cost = models.DecimalField(max_digits=20, decimal_places=0, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["standard", "size", "length", "grade", "finish"],
                name="unique_product_attributes",
            )
        ]


class ProductAlias(models.Model):
    code = models.CharField(max_length=180, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="aliases")


class CodeSequence(models.Model):
    name = models.CharField(max_length=50, unique=True)
    value = models.PositiveBigIntegerField(default=100000)


class Asset(models.Model):
    digest = models.CharField(primary_key=True, max_length=64)
    file = models.FileField(upload_to="assets")
    content_type = models.CharField(max_length=40)
