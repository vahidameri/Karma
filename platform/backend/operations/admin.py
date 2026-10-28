from django.contrib import admin

from .models import Letter, Notification, SettingRevision


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Letter, ReadOnlyAdmin)
admin.site.register(SettingRevision, ReadOnlyAdmin)
admin.site.register(Notification, ReadOnlyAdmin)
