from rest_framework import viewsets

from .models import UserScope
from .services import require, require_scope


class ScopedViewSet(viewsets.ModelViewSet):
    module = ""
    resource = ""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        action = {
            "GET": "view",
            "POST": "create",
            "PATCH": "edit",
            "PUT": "edit",
            "DELETE": "delete",
        }.get(request.method, "view")
        if self.action in ["transition", "issue", "void", "approve", "fulfill"]:
            action = self.action
        require(request.user, f"{self.module}.{self.resource}.{action}")

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not self.detail and self.request.query_params.get("unit"):
            from rest_framework import serializers

            unit = serializers.IntegerField(min_value=1).run_validation(
                self.request.query_params["unit"]
            )
            require_scope(user, unit, user.pk)
            qs = qs.filter(business_unit_id=unit)
        # Detail lookup deliberately checks the scope after permission checks to return 403.
        if user.is_superuser or self.detail:
            return qs
        from django.db.models import Q

        scopes = UserScope.objects.filter(user=user)
        condition = Q(pk__in=[])
        for scope in scopes:
            clause = Q(business_unit_id=scope.business_unit_id)
            if scope.own_only:
                clause &= Q(created_by=user)
            condition |= clause
        return qs.filter(condition)

    def get_object(self):
        obj = super().get_object()
        require_scope(self.request.user, obj.business_unit_id, obj.created_by_id)
        return obj

    def perform_create(self, serializer):
        require_scope(
            self.request.user,
            serializer.validated_data["business_unit"].pk,
            self.request.user.pk,
        )
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        unit = serializer.validated_data.get("business_unit", serializer.instance.business_unit)
        require_scope(self.request.user, unit.pk, serializer.instance.created_by_id)
        serializer.save()
