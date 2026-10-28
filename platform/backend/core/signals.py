from django.contrib.auth.signals import user_login_failed
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .middleware import current_actor
from .models import AuditEntry, ModuleFlag, PermissionOverride, Role, UserScope


@receiver(user_login_failed)
def failed_login(sender, credentials, request, **kwargs):
    AuditEntry.objects.create(
        actor=current_actor.get(),
        action="login.failed",
        target=str(credentials.get("username", ""))[:200],
    )


@receiver(m2m_changed, sender=Role.permissions.through)
@receiver(m2m_changed, sender=Role.users.through)
def role_changed(sender, instance, action, **kwargs):
    if action.startswith("post_"):
        AuditEntry.objects.create(
            actor=current_actor.get(),
            action="iam.membership." + action,
            target=str(instance.pk),
        )


@receiver(post_save)
@receiver(post_delete)
def config_changed(sender, instance, **kwargs):
    if sender in [Role, PermissionOverride, UserScope, ModuleFlag]:
        AuditEntry.objects.create(
            actor=current_actor.get(),
            action="iam.configuration.changed",
            target=f"{sender.__name__}:{instance.pk}",
        )
