from rest_framework.exceptions import NotFound, PermissionDenied

from .models import ModuleFlag, UserScope


def permissions_for(user):
    if not user.is_authenticated or not user.is_active:
        return set()
    from .models import Capability, PermissionOverride

    codes = (
        set(Capability.objects.values_list("code", flat=True))
        if user.is_superuser or user.karma_roles.filter(name="مدیر سیستم").exists()
        else set(Capability.objects.filter(role__users=user).values_list("code", flat=True))
    )
    for item in PermissionOverride.objects.filter(user=user).select_related("permission"):
        if item.allow:
            codes.add(item.permission.code)
        else:
            codes.discard(item.permission.code)
    disabled = set(ModuleFlag.objects.filter(enabled=False).values_list("name", flat=True))
    return {c for c in codes if c.split(".")[0] not in disabled}


def sensitive_account(user):
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    from .models import Capability, PermissionOverride

    if user.karma_roles.filter(name__in=["مدیر سیستم", "حسابدار"]).exists():
        return True
    from django.db.models import Q

    condition = (
        Q(code__startswith="accounting.")
        | Q(code__startswith="payroll.")
        | Q(code__startswith="iam.")
    )
    return (
        Capability.objects.filter(condition, role__users=user).exists()
        or PermissionOverride.objects.filter(user=user, allow=True)
        .filter(
            Q(permission__code__startswith="accounting.")
            | Q(permission__code__startswith="payroll.")
            | Q(permission__code__startswith="iam.")
        )
        .exists()
    )


def mfa_satisfied(user):
    return not sensitive_account(user) or getattr(user, "is_verified", lambda: False)()


def require(user, code):
    if not user.is_authenticated:
        raise PermissionDenied()
    if not mfa_satisfied(user):
        raise PermissionDenied("احراز هویت دومرحله‌ای لازم است")
    module_enabled(code.split(".")[0])
    if code not in permissions_for(user):
        raise PermissionDenied()


def module_enabled(name):
    if ModuleFlag.objects.filter(name=name, enabled=False).exists():
        raise NotFound()


def require_scope(user, business_unit_id, owner_id=None):
    if user.is_superuser:
        return
    scope = UserScope.objects.filter(user=user, business_unit_id=business_unit_id).first()
    if not scope or (scope.own_only and owner_id != user.pk):
        raise PermissionDenied()


def lock_business_unit(unit_id):
    """Acquire before entity/year locks so financial writers share one lock order."""
    from django.db import connection

    from .models import BusinessUnit

    query = (
        BusinessUnit.objects.select_for_update(no_key=True)
        if connection.vendor == "postgresql"
        else BusinessUnit.objects.select_for_update()
    )
    try:
        return query.get(pk=unit_id)
    except BusinessUnit.DoesNotExist:
        raise NotFound("واحد تجاری وجود ندارد")
