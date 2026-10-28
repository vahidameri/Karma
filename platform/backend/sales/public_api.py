from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import Throttled
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from catalog.models import Product
from core.models import BusinessUnit
from search.parser import normalize

from .models import Inquiry, InquiryQuota


class InquiryItem(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(max_digits=18, decimal_places=3, min_value=Decimal("0.001"))


class InquirySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    mobile = serializers.CharField(max_length=20)
    business_unit = serializers.PrimaryKeyRelatedField(queryset=BusinessUnit.objects.all())
    items = InquiryItem(many=True, allow_empty=False, max_length=100)

    def validate_mobile(self, value):
        import re

        value = normalize(value).replace(" ", "")
        if not re.fullmatch(r"09[0-9]{9}", value):
            raise serializers.ValidationError("شماره موبایل معتبر وارد کنید")
        return value


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def inquiry(request):
    from core.services import module_enabled

    module_enabled("sales")
    serializer = InquirySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    quota, _ = InquiryQuota.objects.get_or_create(mobile=data["mobile"], day=timezone.localdate())
    quota = InquiryQuota.objects.select_for_update().get(pk=quota.pk)
    if quota.count >= 10:
        raise Throttled(detail="حداکثر ده درخواست در روز برای هر موبایل مجاز است")
    quota.count += 1
    quota.save(update_fields=["count"])
    items = [
        {
            "product": item["product"].pk,
            "system_code": item["product"].system_code,
            "quantity": str(item["quantity"]),
        }
        for item in data.pop("items")
    ]
    record = Inquiry.objects.create(items=items, **data)
    return Response({"id": record.pk, "status": "received"}, status=201)
