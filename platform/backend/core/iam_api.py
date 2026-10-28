from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.sessions.models import Session
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import AuditEntry, Capability, PermissionOverride, Role, UserScope
from .services import require


class IAMViewSet(viewsets.ModelViewSet):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        require(request.user, "iam.role.manage")


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "permissions", "users"]

    def validate(self, data):
        if self.instance and self.instance.name == "مدیر سیستم" and "permissions" in data:
            raise ValidationError("مجوزهای نقش مدیر سیستم قابل تغییر نیست")
        return data

    def validate_name(self, value):
        if self.instance and self.instance.name == "مدیر سیستم" and value != self.instance.name:
            raise ValidationError("نام نقش مدیر سیستم قابل تغییر نیست")
        return value


class RoleViewSet(IAMViewSet):
    queryset = Role.objects.prefetch_related("permissions", "users").all()
    serializer_class = RoleSerializer

    def perform_destroy(self, instance):
        if instance.name == "مدیر سیستم":
            raise ValidationError("نقش مدیر سیستم حذف نمی‌شود")
        instance.delete()


class CapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Capability
        fields = ["id", "code"]


class CapabilityViewSet(IAMViewSet):
    queryset = Capability.objects.order_by("code")
    serializer_class = CapabilitySerializer
    http_method_names = ["get", "head", "options"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=12)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_active", "password"]

    def validate(self, data):
        if self.instance and self.instance.is_superuser:
            raise ValidationError("حساب مدیر ریشه فقط در مدیریت امن قابل تغییر است")
        if not self.instance and "password" not in data:
            raise ValidationError("رمز عبور لازم است")
        if "password" in data:
            validate_password(data["password"], self.instance)
        return data

    def create(self, data):
        return User.objects.create_user(**data)

    def update(self, instance, data):
        password = data.pop("password", None)
        for key, value in data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserViewSet(IAMViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    @action(detail=True, methods=["post"])
    def revoke_sessions(self, request, pk=None):
        user = self.get_object()
        if user.is_superuser and request.user.pk != user.pk:
            raise ValidationError("دسترسی به مدیر ریشه محدود است")
        for session in Session.objects.filter(expire_date__gt=timezone.now()):
            if session.get_decoded().get("_auth_user_id") == str(user.pk):
                session.delete()
        AuditEntry.objects.create(
            actor=request.user, action="iam.sessions.revoked", target=str(user.pk)
        )
        return Response({"ok": True})


class ScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserScope
        fields = "__all__"


class ScopeViewSet(IAMViewSet):
    queryset = UserScope.objects.all()
    serializer_class = ScopeSerializer


class OverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionOverride
        fields = "__all__"


class OverrideViewSet(IAMViewSet):
    queryset = PermissionOverride.objects.all()
    serializer_class = OverrideSerializer
