from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import ExactModelSerializer
from core.services import mfa_satisfied, module_enabled, permissions_for, require
from search.services import search_products

from .models import Product, Standard
from .services import create_product, update_product


class ProductSerializer(ExactModelSerializer):
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        return f"/api/v1/assets/{obj.standard.photo_id}/" if obj.standard.photo_id else None

    standard_code = serializers.CharField(source="standard.code", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "standard",
            "standard_code",
            "image_url",
            "system_code",
            "technical_code",
            "name",
            "size",
            "length",
            "grade",
            "finish",
            "cost",
        ]
        read_only_fields = ["system_code", "technical_code"]

    def get_fields(self):
        fields = super().get_fields()
        if "catalog.price.view_cost" not in permissions_for(
            self.context["request"].user
        ) or not mfa_satisfied(self.context["request"].user):
            fields.pop("cost", None)
        return fields

    def create(self, data):
        from django.db import IntegrityError

        try:
            return create_product(**data)
        except IntegrityError:
            raise serializers.ValidationError("کد یا ترکیب ویژگی‌ها تکراری است")

    def update(self, instance, data):
        from django.db import IntegrityError

        try:
            return update_product(instance, **data)
        except IntegrityError:
            raise serializers.ValidationError("کد یا ترکیب ویژگی‌ها تکراری است")


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        module_enabled("catalog")
        if request.method == "POST":
            require(request.user, "catalog.product.create")
        if request.method == "PATCH":
            require(request.user, "catalog.product.edit")

    def get_queryset(self):
        return Product.objects.select_related("standard").order_by("id")

    def list(self, request):
        rows, parsed, engine = search_products(request.query_params.get("q", ""))
        return Response(
            {
                "results": self.get_serializer(rows, many=True).data,
                "query": parsed,
                "engine": engine,
            }
        )

    @action(detail=False, methods=["get"])
    def resolve(self, request):
        code = request.query_params.get("code", "").upper().strip()
        p = (
            self.get_queryset()
            .filter(Q(system_code=code) | Q(technical_code=code) | Q(aliases__code=code))
            .distinct()
            .first()
        )
        if not p:
            raise NotFound()
        return Response(self.get_serializer(p).data)

    @action(detail=False, methods=["get"])
    def export(self, request):
        import io

        import openpyxl
        from django.http import HttpResponse

        rows, _, _ = search_products(request.query_params.get("q", ""))
        values = self.get_serializer(rows, many=True).data
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "کالاها"
        ws.sheet_view.rightToLeft = True
        labels = {
            "system_code": "کد سیستمی",
            "technical_code": "کد فنی",
            "standard_code": "استاندارد",
            "name": "نام کالا",
            "size": "سایز",
            "length": "طول",
            "grade": "گرید",
            "finish": "پوشش",
            "cost": "قیمت تمام‌شده (ریال)",
        }
        fields = self.get_serializer().fields
        columns = [key for key in labels if key in fields]
        ws.append([labels[key] for key in columns])
        for row in values:
            ws.append([row.get(key) for key in columns])
        # Write literal strings, including names beginning with '=', rather than Excel formulas.
        for row in ws:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.data_type = "s"
        ws.freeze_panes = "A2"
        output = io.BytesIO()
        wb.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="products.xlsx"'
        return response


class StandardSerializer(ExactModelSerializer):
    photo_url = serializers.SerializerMethodField()
    drawing_url = serializers.SerializerMethodField()

    def get_photo_url(self, obj):
        return f"/api/v1/assets/{obj.photo_id}/" if obj.photo_id else None

    def get_drawing_url(self, obj):
        return f"/api/v1/assets/{obj.drawing_id}/" if obj.drawing_id else None

    class Meta:
        model = Standard
        fields = ["id", "code", "name", "dimensions", "photo_url", "drawing_url"]


class StandardViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StandardSerializer
    permission_classes = [AllowAny]
    queryset = Standard.objects.order_by("code")

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        module_enabled("catalog")


class AssetView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request, digest):
        from .models import Asset

        module_enabled("catalog")
        asset = get_object_or_404(Asset, digest=digest)
        response = FileResponse(asset.file.open("rb"), content_type=asset.content_type)
        response["Cache-Control"] = "public, max-age=31536000, immutable"
        return response
