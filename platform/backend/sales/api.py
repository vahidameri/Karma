from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.scoped_api import ScopedViewSet
from core.serializers import ExactModelSerializer, JalaliDateField
from core.services import require
from treasury.models import Allocation

from .models import Document, DocumentLine
from .services import (
    change_quote_state,
    convert_document,
    fulfill_supply,
    issue_document,
    void_document,
)


class LineSerializer(ExactModelSerializer):
    product_code = serializers.CharField(source="product.technical_code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    progress = serializers.SerializerMethodField()

    def get_progress(self, obj):
        value = getattr(obj, "progress", None)
        return (
            {"quantity": str(value.quantity), "source": value.source, "notes": value.notes}
            if value
            else None
        )

    class Meta:
        model = DocumentLine
        exclude = ["document"]
        read_only_fields = ["id", "product_snapshot"]


class DocumentSerializer(ExactModelSerializer):
    accounting_status = serializers.SerializerMethodField()

    def get_accounting_status(self, obj):
        if obj.kind not in ["invoice", "return", "purchase", "purchase_return"]:
            return "not_applicable"
        from accounting.models import Voucher

        return (
            "posted"
            if Voucher.objects.filter(source_key=f"document:{obj.pk}").exists()
            else "pending"
        )

    customer_name = serializers.CharField(source="customer.name", read_only=True)
    doc_date = JalaliDateField()
    lines = LineSerializer(many=True)
    paid = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = [
            "created_by",
            "status",
            "issued_at",
            "created_at",
            "deal_number",
            "number",
            "buyer_snapshot",
            "settings_snapshot",
            "subtotal",
            "tax",
            "total",
        ]

    def get_paid(self, obj):
        return str(
            Allocation.objects.filter(document=obj, payment__void=False).aggregate(n=Sum("amount"))[
                "n"
            ]
            or 0
        )

    def validate(self, data):
        data = super().validate(data)
        if self.instance and "kind" in data and data["kind"] != self.instance.kind:
            raise ValidationError("نوع سند قابل تغییر نیست؛ از تبدیل سند استفاده کنید")
        if self.instance and self.instance.status != "draft":
            raise ValidationError("سند صادرشده قابل ویرایش نیست")
        unit = data.get("business_unit", getattr(self.instance, "business_unit", None))
        customer = data.get("customer", getattr(self.instance, "customer", None))
        if customer and unit and customer.business_unit_id != unit.pk:
            raise ValidationError("مشتری متعلق به واحد دیگری است")
        from core.services import require_scope

        if customer and unit:
            require_scope(self.context["request"].user, unit.pk, customer.created_by_id)
        parent = data.get("parent", getattr(self.instance, "parent", None))
        if parent:
            from .services import require_document_action

            require_scope(
                self.context["request"].user, parent.business_unit_id, parent.created_by_id
            )
            require_document_action(self.context["request"].user, parent, "view")
        if parent and (parent.business_unit_id != unit.pk or parent.customer_id != customer.pk):
            raise ValidationError("سند مبدأ نامعتبر است")
        return data

    @transaction.atomic
    def create(self, data):
        lines = data.pop("lines")
        doc = Document.objects.create(**data)
        for line in lines:
            DocumentLine.objects.create(document=doc, **line)
        return doc

    @transaction.atomic
    def update(self, instance, data):
        instance = Document.objects.select_for_update().get(pk=instance.pk)
        if instance.status != "draft":
            raise ValidationError("سند قفل است")
        lines = data.pop("lines", None)
        for k, v in data.items():
            setattr(instance, k, v)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            for line in lines:
                DocumentLine.objects.create(document=instance, **line)
        return instance


class DocumentViewSet(ScopedViewSet):
    module = "sales"
    resource = "document"
    serializer_class = DocumentSerializer
    queryset = (
        Document.objects.select_related("customer")
        .prefetch_related("lines__progress", "lines__product")
        .order_by("-pk")
    )
    http_method_names = ["get", "post", "patch", "head", "options"]

    def initial(self, request, *args, **kwargs):
        from core.services import module_enabled, permissions_for

        viewsets.ModelViewSet.initial(self, request, *args, **kwargs)
        module_enabled("sales")
        if self.action in ["list", "create"]:
            action = "view" if self.action == "list" else "create"
            codes = permissions_for(request.user)
            general = f"sales.document.{action}"
            if general in codes:
                require(request.user, general)
            elif self.action == "list":
                available = [
                    f"sales.{kind}.{action}"
                    for kind, _ in Document.TYPES
                    if f"sales.{kind}.{action}" in codes
                ]
                require(request.user, available[0] if available else general)
            else:
                kind = request.data.get("kind", "") if isinstance(request.data, dict) else ""
                require(request.user, f"sales.{kind}.create")

    def get_queryset(self):
        from core.services import permissions_for

        qs = super().get_queryset()
        if not self.detail:
            codes = permissions_for(self.request.user)
            if "sales.document.view" not in codes:
                qs = qs.filter(
                    kind__in=[kind for kind, _ in Document.TYPES if f"sales.{kind}.view" in codes]
                )
        return qs

    def get_object(self):
        from .services import require_document_action

        obj = super().get_object()
        action = {
            "retrieve": "view",
            "partial_update": "edit",
            "update": "edit",
            "pdf": "print",
            "convert": "view",
        }.get(self.action, self.action)
        require_document_action(self.request.user, obj, action)
        return obj

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        return Response(self.get_serializer(issue_document(self.get_object(), request.user)).data)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        return Response(self.get_serializer(void_document(self.get_object(), request.user)).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return Response(
            self.get_serializer(
                change_quote_state(self.get_object(), request.user, "approved")
            ).data
        )

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        data = ConvertInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            self.get_serializer(
                convert_document(self.get_object(), request.user, data.validated_data["kind"])
            ).data,
            status=201,
        )

    @action(detail=True, methods=["post"])
    def fulfill(self, request, pk=None):
        data = FulfillInput(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(
            self.get_serializer(
                fulfill_supply(self.get_object(), request.user, **data.validated_data)
            ).data
        )

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        from django.http import HttpResponse

        from documents.services import document_pdf

        return HttpResponse(document_pdf(self.get_object()), content_type="application/pdf")


class ConvertInput(serializers.Serializer):
    kind = serializers.ChoiceField(choices=Document.TYPES)


class FulfillItem(serializers.Serializer):
    line = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=18, decimal_places=3, min_value=0)
    source = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class FulfillInput(serializers.Serializer):
    items = FulfillItem(many=True, max_length=1000)
    complete = serializers.BooleanField(default=False)
