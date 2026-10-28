from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.models import UserScope
from core.serializers import JalaliDateField
from core.services import require, require_scope

from .closing import close_year
from .models import Account, FiscalYear, Period, Voucher
from .services import post_voucher, trial_balance


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = "__all__"


class LedgerLineInput(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    debit = serializers.DecimalField(max_digits=20, decimal_places=0, min_value=0, default=0)
    credit = serializers.DecimalField(max_digits=20, decimal_places=0, min_value=0, default=0)
    party = serializers.IntegerField(required=False, min_value=1)
    detail = serializers.DictField(required=False, default=dict)
    description = serializers.CharField(required=False, allow_blank=True)


class LedgerInput(serializers.Serializer):
    business_unit = serializers.IntegerField(min_value=1)
    doc_date = JalaliDateField()
    idempotency_key = serializers.CharField(max_length=80)
    lines = LedgerLineInput(many=True, allow_empty=False, max_length=1000)


@api_view(["GET", "POST"])
def ledger(request):
    if request.method == "POST" and not isinstance(request.data, dict):
        raise serializers.ValidationError("Expected a JSON object")
    unit_field = serializers.IntegerField(min_value=1)
    unit = unit_field.run_validation(
        request.query_params.get("unit", request.data.get("business_unit", 0))
    )
    require_scope(request.user, unit, request.user.pk)
    if request.method == "GET":
        require(request.user, "accounting.voucher.view")
        own = (
            UserScope.objects.filter(
                user=request.user, business_unit_id=unit, own_only=True
            ).exists()
            and not request.user.is_superuser
        )
        rows = trial_balance(unit, request.user.pk if own else None)
        return Response(
            [{**row, "debit": str(row["debit"]), "credit": str(row["credit"])} for row in rows]
        )
    require(request.user, "accounting.voucher.post")
    serializer = LedgerInput(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    lines = [{**item, "account": item["account"].pk} for item in values["lines"]]
    v = post_voucher(
        unit_id=unit,
        date=values["doc_date"],
        actor=request.user,
        source_type="manual",
        source_key=f"manual:{unit}:" + values["idempotency_key"],
        lines=lines,
    )
    return Response(VoucherSerializer(v).data, status=201)


class CloseYearInput(serializers.Serializer):
    year = serializers.PrimaryKeyRelatedField(queryset=FiscalYear.objects.all())
    next_period = serializers.PrimaryKeyRelatedField(queryset=Period.objects.all())
    ending_inventory = serializers.DecimalField(max_digits=20, decimal_places=0, min_value=0)


@api_view(["POST"])
def fiscal_close(request):
    data = CloseYearInput(data=request.data)
    data.is_valid(raise_exception=True)
    values = data.validated_data
    return Response(
        close_year(values["year"], request.user, values["ending_inventory"], values["next_period"])
    )
