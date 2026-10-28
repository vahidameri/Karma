from contextvars import ContextVar

current_actor = ContextVar("audit_actor", default=None)


class AuditActorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = current_actor.set(request.user if request.user.is_authenticated else None)
        try:
            return self.get_response(request)
        finally:
            current_actor.reset(token)


class AdminLoginThrottleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.http import JsonResponse

        from .auth_limiter import allowed, clear

        admin_login = request.method == "POST" and request.path == "/admin/login/"
        username = request.POST.get("username", "") if admin_login else ""
        if admin_login and not allowed(request, username):
            return JsonResponse({"detail": "تعداد تلاش بیش از حد مجاز است"}, status=429)
        response = self.get_response(request)
        if admin_login and request.user.is_authenticated:
            clear(request, username)
        return response
