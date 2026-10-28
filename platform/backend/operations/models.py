from django.db import models


class SettingRevision(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    key = models.CharField(max_length=100)
    value = models.JSONField()
    created_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class FieldMemory(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=300)
    count = models.PositiveIntegerField(default=1)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business_unit", "key", "value"], name="unique_field_memory"
            )
        ]


class Letter(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    kind = models.CharField(
        max_length=12,
        choices=[("incoming", "وارده"), ("outgoing", "صادره"), ("internal", "داخلی")],
    )
    subject = models.CharField(max_length=250)
    body = models.TextField()
    doc_date = models.DateField()
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.PROTECT, related_name="letters_created"
    )
    assigned_to = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="letters_assigned",
    )
    status = models.CharField(max_length=20, default="draft")


class Notification(models.Model):
    recipient = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    message = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True)
