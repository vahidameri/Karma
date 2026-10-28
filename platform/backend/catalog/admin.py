from django.contrib import admin

from .models import Product, ProductAlias, Standard


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    search_fields = ("code", "name")
    list_display = ("code", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    search_fields = ("system_code", "technical_code", "name")
    list_display = ("system_code", "technical_code", "name")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(ProductAlias)
