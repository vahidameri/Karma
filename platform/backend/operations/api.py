from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.scoped_api import ScopedViewSet
from core.serializers import JalaliDateField

from .models import Letter, Notification, SettingRevision


class LetterSerializer(serializers.ModelSerializer):
    doc_date = JalaliDateField()

    class Meta:
        model = Letter
        fields = "__all__"
        read_only_fields = ["created_by"]


class LetterViewSet(ScopedViewSet):
    module = "secretariat"
    resource = "letter"
    serializer_class = LetterSerializer
    queryset = Letter.objects.all().order_by("-id")


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SettingRevision
        fields = "__all__"
        read_only_fields = ["created_by"]


class SettingViewSet(ScopedViewSet):
    module = "settings"
    resource = "revision"
    serializer_class = SettingSerializer
    queryset = SettingRevision.objects.all().order_by("-id")
    http_method_names = ["get", "post", "head", "options"]


@api_view(["GET"])
def notifications(request):
    return Response(
        list(
            Notification.objects.filter(recipient=request.user).values(
                "id", "message", "created_at", "read_at"
            )[:100]
        )
    )
