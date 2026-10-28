import io
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

from accounting.models import Account, FiscalYear, Period, Voucher
from accounting.services import post_voucher, reverse_voucher, trial_balance
from core.models import BusinessUnit


class BalanceProperties(TestCase):
    @settings(max_examples=12, deadline=None)
    @given(st.lists(st.integers(min_value=1, max_value=10**12), min_size=1, max_size=12))
    def test_post_and_reverse_preserve_balances(self, amounts):
        user = User.objects.create_user("property-user")
        call_command("seed_platform", stdout=io.StringIO())
        call_command("seed_accounts", stdout=io.StringIO())
        unit = BusinessUnit.objects.first()
        day = timezone.localdate()
        year = FiscalYear.objects.create(
            business_unit=unit,
            name="Property year",
            start=day - timedelta(days=1),
            end=day + timedelta(days=1),
        )
        Period.objects.create(year=year, start=year.start, end=year.end)
        a = Account.objects.get(business_unit=unit, code="6101")
        b = Account.objects.get(business_unit=unit, code="7101")
        for index, value in enumerate(amounts):
            voucher = post_voucher(
                unit_id=unit.pk,
                date=day,
                actor=user,
                source_type="property",
                source_key=f"p:{index}",
                lines=[{"account": a.pk, "debit": value}, {"account": b.pk, "credit": value}],
            )
            reverse_voucher(voucher, user, day)
        self.assertEqual(Voucher.objects.filter(status="permanent").count(), 2 * len(amounts))
        for row in trial_balance(unit.pk):
            self.assertEqual(row["debit"], row["credit"])
