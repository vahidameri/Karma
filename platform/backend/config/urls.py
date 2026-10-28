from django.contrib import admin
from django.urls import include, path
from django_otp.admin import OTPAdminSite
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from accounting.api import fiscal_close, ledger
from catalog.api import AssetView, ProductViewSet, StandardViewSet
from core.api import health, me
from core.auth_api import session
from core.iam_api import CapabilityViewSet, OverrideViewSet, RoleViewSet, ScopeViewSet, UserViewSet
from crm.api import PartyViewSet
from operations.api import LetterViewSet, SettingViewSet, notifications
from payroll.api import ContractViewSet, PayslipViewSet
from sales.api import DocumentViewSet
from sales.public_api import inquiry
from treasury.api import ChequeViewSet, PaymentViewSet


class KarmaAdminSite(OTPAdminSite):
    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser


admin.site.__class__ = KarmaAdminSite


router = DefaultRouter()
for route, view in [
    ("roles", RoleViewSet),
    ("capabilities", CapabilityViewSet),
    ("users", UserViewSet),
    ("scopes", ScopeViewSet),
    ("overrides", OverrideViewSet),
]:
    router.register(route, view, basename=route)
router.register("contracts", ContractViewSet, basename="contract")
router.register("payslips", PayslipViewSet, basename="payslip")
for route, view, name in [
    ("products", ProductViewSet, "product"),
    ("standards", StandardViewSet, "standard"),
    ("parties", PartyViewSet, "party"),
    ("documents", DocumentViewSet, "document"),
    ("payments", PaymentViewSet, "payment"),
    ("cheques", ChequeViewSet, "cheque"),
    ("letters", LetterViewSet, "letter"),
    ("settings", SettingViewSet, "setting"),
]:
    router.register(route, view, basename=name)
urlpatterns = [
    path("api/v1/assets/<str:digest>/", AssetView.as_view()),
    path("api/v1/fiscal-close/", fiscal_close),
    path("api/v1/inquiries/", inquiry),
    path("api/v1/session/", session),
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path("api/v1/me/permissions/", me),
    path("api/v1/ledger/", ledger),
    path("api/v1/notifications/", notifications),
    path("api/v1/health/", health),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
admin.site.site_header = "مدیریت سامانهٔ کارما"
