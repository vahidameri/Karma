from django.contrib import admin

from .models import (
    AuditEntry,
    BusinessUnit,
    Capability,
    ModuleFlag,
    PermissionOverride,
    Role,
    UserScope,
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    filter_horizontal = ("permissions", "users")
    search_fields = ("name",)

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (
            obj is None or obj.name != "مدیر سیستم"
        )

    def get_readonly_fields(self, request, obj=None):
        return ("name", "permissions") if obj and obj.name == "مدیر سیستم" else ()

    def delete_queryset(self, request, queryset):
        from django.core.exceptions import PermissionDenied

        if queryset.filter(name="مدیر سیستم").exists():
            raise PermissionDenied("نقش مدیر سیستم حذف نمی‌شود")
        return super().delete_queryset(request, queryset)


@admin.register(AuditEntry)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


for model in [BusinessUnit, Capability, UserScope, PermissionOverride, ModuleFlag]:
    admin.site.register(model)
