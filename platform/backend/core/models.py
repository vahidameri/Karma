from django.conf import settings
from django.db import models


class BusinessUnit(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Capability(models.Model):
    code = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.code


class Role(models.Model):
    name = models.CharField(max_length=150, unique=True)
    permissions = models.ManyToManyField(Capability, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="karma_roles", blank=True)

    def __str__(self):
        return self.name


class UserScope(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    own_only = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "business_unit"], name="unique_user_scope")
        ]


class PermissionOverride(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    permission = models.ForeignKey(Capability, on_delete=models.CASCADE)
    allow = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "permission"], name="unique_override")
        ]


class ModuleFlag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    enabled = models.BooleanField(default=True)


class AuditEntry(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=120)
    target = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class OutboxEvent(models.Model):
    attempts = models.PositiveIntegerField(default=0)
    retry_at = models.DateTimeField(null=True)
    last_error = models.CharField(max_length=120, blank=True)
    topic = models.CharField(max_length=100)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True)


class BootstrapState(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
