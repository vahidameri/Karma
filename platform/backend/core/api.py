from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services import permissions_for


@api_view(["GET"])
def me(request):
    from .models import BusinessUnit

    units = (
        BusinessUnit.objects.all()
        if request.user.is_superuser
        else BusinessUnit.objects.filter(userscope__user=request.user).distinct()
    )
    return Response(
        {
            "username": request.user.username,
            "permissions": sorted(permissions_for(request.user)),
            "units": list(units.order_by("pk").values("id", "name")),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return Response({"status": "ok", "version": "2.0.0-alpha.1"})
