from core.scoped_api import ScopedViewSet
from core.serializers import ExactModelSerializer

from .models import Party


class PartySerializer(ExactModelSerializer):
    class Meta:
        model = Party
        fields = "__all__"
        read_only_fields = ["created_by"]

    def validate_mobile(self, value):
        from search.parser import normalize

        return normalize(value).replace(" ", "") if value else None

    def validate_national_id(self, value):
        from search.parser import normalize

        return normalize(value).replace(" ", "") if value else None


class PartyViewSet(ScopedViewSet):
    module = "crm"
    resource = "party"
    queryset = Party.objects.all().order_by("name")
    serializer_class = PartySerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        from django.db.models import Q

        qs = super().get_queryset()
        q = self.request.query_params.get("q", "")
        return (
            qs.filter(Q(name__icontains=q) | Q(mobile__icontains=q) | Q(national_id__icontains=q))
            if q
            else qs
        )
