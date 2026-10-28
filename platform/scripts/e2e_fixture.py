"""Only run via with_services.py --database karma_e2e. No default or production accounts."""

import json
import os
import secrets
import sys
from pathlib import Path

if os.environ.get("POSTGRES_DB") != "karma_e2e":
    raise RuntimeError("Refusing to seed a non-test database")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
import jdatetime
from accounting.models import FiscalYear, Period
from core.models import BusinessUnit, Capability, Role, UserScope
from crm.models import Party
from django.contrib.auth.models import User
from django.utils import timezone

password = secrets.token_urlsafe(28)
user = User.objects.create_user("e2e-sales", password=password)
role = Role.objects.create(name="E2E sales role")
role.permissions.set(Capability.objects.filter(code__startswith="sales."))
role.permissions.add(
    *Capability.objects.filter(code__in=["crm.party.view", "crm.party.create"])
)
role.users.add(user)
unit = BusinessUnit.objects.get(name="کارما")
UserScope.objects.create(user=user, business_unit=unit)
party = Party.objects.create(
    name="خریدار آزمون یکپارچه",
    mobile="09121112222",
    business_unit=unit,
    created_by=user,
)
today = jdatetime.date.fromgregorian(date=timezone.localdate())
start = jdatetime.date(today.year, 1, 1).togregorian()
end = jdatetime.date(today.year + 1, 1, 1).togregorian() - timezone.timedelta(days=1)
year = FiscalYear.objects.create(
    business_unit=unit, name="E2E fiscal year", start=start, end=end
)
Period.objects.create(year=year, start=start, end=end)

from catalog.models import Product
from sales.models import Document, DocumentLine

private = Document.objects.create(
    business_unit=unit,
    customer=party,
    kind="quote",
    doc_date=timezone.localdate(),
    created_by=user,
    notes="Private unit-one fixture",
)
DocumentLine.objects.create(
    document=private,
    product=Product.objects.get(system_code="KR-100001"),
    quantity=1,
    unit_price=1000,
)
second_password = secrets.token_urlsafe(28)
second = User.objects.create_user("e2e-other-unit", password=second_password)
role.users.add(second)
second_unit = BusinessUnit.objects.get(name="آلیاژ پیچ کار ماد")
UserScope.objects.create(user=second, business_unit=second_unit)
path = Path("/tmp/karma-e2e-credentials.json")
path.write_text(
    json.dumps(
        {
            "username": user.username,
            "password": password,
            "party": party.pk,
            "unit": unit.pk,
            "second_username": second.username,
            "second_password": second_password,
            "second_unit": second_unit.pk,
        }
    )
)
path.chmod(0o600)
print("Disposable E2E fixtures created; no credential values logged")
