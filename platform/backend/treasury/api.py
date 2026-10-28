from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from core.scoped_api import ScopedViewSet
from core.serializers import ExactModelSerializer, JalaliDateField

from .models import Cheque, Payment
from .services import create_payment, transition_cheque


class PaymentSerializer(ExactModelSerializer):
    doc_date = JalaliDateField()
    allocations = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["created_by", "voucher", "void"]

    def create(self, data):
        return create_payment(
            actor=data.pop("created_by"),
            allocations=data.pop("allocations", []),
            **data,
        )


class PaymentViewSet(ScopedViewSet):
    module = "treasury"
    resource = "payment"
    queryset = Payment.objects.all().order_by("-id")
    serializer_class = PaymentSerializer
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        from django.utils import timezone

        from .services import void_payment

        return Response(
            self.get_serializer(
                void_payment(self.get_object(), request.user, timezone.localdate())
            ).data
        )


class ChequeSerializer(ExactModelSerializer):
    due_date = JalaliDateField()

    class Meta:
        model = Cheque
        fields = "__all__"
        read_only_fields = ["created_by", "state"]

    def validate(self, data):
        data = super().validate(data)
        if data["party"].business_unit_id != data["business_unit"].pk:
            raise serializers.ValidationError("طرف حساب واحد دیگری است")
        if (
            data["amount"] <= 0
            or len(data["sayad_number"]) != 16
            or not data["sayad_number"].isdigit()
        ):
            raise serializers.ValidationError("مبلغ یا شناسه صیادی نامعتبر")
        return data


class ChequeViewSet(ScopedViewSet):
    module = "treasury"
    resource = "cheque"
    queryset = Cheque.objects.all().order_by("-id")
    serializer_class = ChequeSerializer
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        from datetime import date

        result = transition_cheque(
            self.get_object(),
            request.user,
            request.data.get("state"),
            date.fromisoformat(request.data["doc_date"]),
        )
        return Response(self.get_serializer(result).data)
