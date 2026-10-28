import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django_otp import login as otp_login
from django_otp import match_token


@require_http_methods(["GET", "POST", "DELETE"])
@csrf_protect
def session(request):
    if request.method == "GET":
        return JsonResponse(
            {
                "csrfToken": get_token(request),
                "authenticated": request.user.is_authenticated,
            }
        )
    if request.method == "DELETE":
        logout(request)
        return JsonResponse({"ok": True})
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({"detail": "درخواست نامعتبر"}, status=400)
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("username"), str)
        or not isinstance(data.get("password"), str)
        or len(data["username"]) > 150
        or len(data["password"]) > 256
        or not isinstance(data.get("otp", ""), str)
        or len(data.get("otp", "")) > 8
    ):
        return JsonResponse({"detail": "اطلاعات ورود نامعتبر است"}, status=400)
    from .auth_limiter import allowed, clear

    if not allowed(request, data["username"]):
        return JsonResponse({"detail": "تعداد تلاش بیش از حد مجاز است"}, status=429)
    user = authenticate(
        request, username=data.get("username", ""), password=data.get("password", "")
    )
    if not user:
        return JsonResponse({"detail": "اطلاعات ورود نادرست است"}, status=403)
    from .services import sensitive_account

    sensitive = sensitive_account(user)
    device = match_token(user, str(data.get("otp", ""))) if data.get("otp") else None
    if sensitive and not device:
        return JsonResponse({"detail": "برای این حساب رمز دومرحله‌ای معتبر لازم است"}, status=403)
    login(request, user)
    if device:
        otp_login(request, device)
    clear(request, data["username"])
    return JsonResponse({"username": user.username})
