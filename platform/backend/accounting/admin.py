from django.contrib import admin

from .models import Account, FiscalYear, Period, PostingRule, Voucher


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "business_unit", "active")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.voucherline_set.exists():
            return ("business_unit", "code", "name", "detail_kinds", "detail_required")
        return ()


@admin.register(FiscalYear)
class YearAdmin(admin.ModelAdmin):
    readonly_fields = ("closed",)


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    readonly_fields = ("closed",)


admin.site.register(PostingRule)


@admin.register(Voucher)
class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
