import io
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection, connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounting.models import Account, FiscalYear, Period, Voucher
from accounting.services import post_invoice_event, post_voucher
from catalog.models import Standard
from catalog.services import create_product
from core.models import BusinessUnit
from crm.models import Party
from sales.models import Document, DocumentLine
from sales.services import issue_document, void_document
from treasury.services import create_payment


@skipUnless(
    connection.vendor == "postgresql",
    "Real row-lock concurrency requires PostgreSQL; SQLite is development-only",
)
class FinancialConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        call_command("seed_platform", stdout=io.StringIO())
        call_command("seed_accounts", stdout=io.StringIO())
        self.user = User.objects.create_superuser("concurrency-owner")
        self.user.is_verified = lambda: True
        self.unit = BusinessUnit.objects.get(name="کارما")
        self.day = timezone.localdate()
        year = FiscalYear.objects.create(
            business_unit=self.unit,
            name="Concurrency",
            start=self.day - timedelta(days=1),
            end=self.day + timedelta(days=1),
        )
        Period.objects.create(year=year, start=year.start, end=year.end)

    def actor(self):
        user = User.objects.get(pk=self.user.pk)
        user.is_verified = lambda: True
        return user

    def test_parallel_postings_have_unique_gapless_numbers(self):
        debit = Account.objects.get(business_unit=self.unit, code="7101")
        credit = Account.objects.get(business_unit=self.unit, code="6101")
        start = Barrier(4)

        def post(i):
            try:
                actor = self.actor()
                start.wait(timeout=10)
                return post_voucher(
                    unit_id=self.unit.pk,
                    date=self.day,
                    actor=actor,
                    source_type="concurrency",
                    source_key=f"parallel:{i}",
                    lines=[
                        {"account": debit.pk, "debit": 100 + i},
                        {"account": credit.pk, "credit": 100 + i},
                    ],
                ).number
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=4) as pool:
            numbers = list(pool.map(post, range(4)))
        self.assertEqual(sorted(numbers), [1, 2, 3, 4])
        self.assertEqual(Voucher.objects.count(), 4)

    def test_payment_and_invoice_void_do_not_deadlock_or_both_commit(self):
        party = Party.objects.create(
            name="Concurrent buyer", business_unit=self.unit, created_by=self.user
        )
        product = create_product(
            standard=Standard.objects.create(code="DIN933"), name="Bolt", size="M10"
        )
        doc = Document.objects.create(
            business_unit=self.unit,
            customer=party,
            kind="invoice",
            doc_date=self.day,
            created_by=self.user,
        )
        DocumentLine.objects.create(document=doc, product=product, quantity=1, unit_price=1000)
        doc = issue_document(doc, self.user)
        post_invoice_event(doc.pk)
        bank = Account.objects.get(business_unit=self.unit, code="1102")
        start = Barrier(2)

        def action(name):
            try:
                actor = self.actor()
                start.wait(timeout=10)
                try:
                    if name == "pay":
                        create_payment(
                            actor,
                            [{"document": doc.pk, "amount": 1000}],
                            business_unit=self.unit,
                            party=party,
                            amount=1000,
                            direction="receive",
                            account=bank,
                            detail={"bank_account": "concurrency-test"},
                            doc_date=self.day,
                        )
                    else:
                        void_document(doc, actor)
                    return True
                except ValidationError:
                    return False
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(action, ["pay", "void"]))
        self.assertEqual(sum(outcomes), 1)
