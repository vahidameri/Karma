from django.core.management.base import BaseCommand
from django.db import transaction

from accounting.models import Account, PostingRule
from core.models import BootstrapState, BusinessUnit, Capability, Role

DEFAULTS = [
    ("1101", "صندوق", ["cash_box"]),
    ("1102", "بانک", ["bank_account"]),
    ("1103", "تنخواه", ["petty_cash"]),
    ("1201", "حساب‌های دریافتنی تجاری", ["party"]),
    ("1202", "اسناد دریافتنی", ["cheque", "party"]),
    ("1203", "چک‌های در جریان وصول", ["cheque", "bank_account"]),
    ("1204", "چک‌های برگشتی", ["cheque", "party"]),
    ("1301", "موجودی کالا", []),
    ("1402", "مالیات خرید", []),
    ("3101", "حساب‌های پرداختنی تجاری", ["party"]),
    ("3102", "اسناد پرداختنی", ["cheque", "party"]),
    ("3201", "مالیات فروش", []),
    ("3202", "حقوق پرداختنی", ["party"]),
    ("3203", "بیمه پرداختنی", []),
    ("3204", "مالیات حقوق", []),
    ("3301", "پیش‌دریافت فروش", ["party"]),
    ("5101", "سرمایه", ["party"]),
    ("5301", "سود و زیان انباشته", []),
    ("6101", "فروش کالا", []),
    ("6102", "برگشت از فروش", []),
    ("6103", "تخفیفات فروش", []),
    ("6201", "درآمد حمل", []),
    ("6302", "سود و زیان تسعیر", []),
    ("7101", "بهای تمام‌شده کالای فروش‌رفته", []),
    ("7102", "خرید کالا", []),
    ("7103", "برگشت از خرید", []),
    ("7104", "حمل خرید", []),
    ("7201", "هزینه حقوق", ["party", "cost_center"]),
    ("7501", "کارمزد بانک", []),
    ("8201", "خلاصه سود و زیان", []),
    ("8301", "تراز افتتاحیه", []),
    ("8401", "تراز اختتامیه", []),
]


def rule_line(code, side, value, party=False):
    return {"account": code, "side": side, "amount": value, "party": party}


RULES = {
    "payroll": [
        rule_line("7201", "debit", "gross", True),
        rule_line("7201", "debit", "employer_insurance", True),
        rule_line("3202", "credit", "net", True),
        rule_line("3203", "credit", "total_insurance"),
        rule_line("3204", "credit", "tax"),
    ],
    "invoice": [
        rule_line("1201", "debit", "total", True),
        rule_line("6101", "credit", "subtotal"),
        rule_line("3201", "credit", "tax"),
        rule_line("6201", "credit", "shipping"),
        rule_line("6103", "debit", "discount"),
    ],
    "purchase": [
        rule_line("7102", "debit", "net"),
        rule_line("7104", "debit", "shipping"),
        rule_line("1402", "debit", "tax"),
        rule_line("3101", "credit", "total", True),
    ],
    "return": [
        rule_line("6102", "debit", "net"),
        rule_line("6201", "debit", "shipping"),
        rule_line("3201", "debit", "tax"),
        rule_line("1201", "credit", "total", True),
    ],
    "purchase_return": [
        rule_line("3101", "debit", "total", True),
        rule_line("7103", "credit", "net"),
        rule_line("7104", "credit", "shipping"),
        rule_line("1402", "credit", "tax"),
    ],
    "year_close": {
        "inventory": "1301",
        "purchases": "7102",
        "purchase_returns": "7103",
        "purchase_freight": "7104",
        "cogs": "7101",
        "income_summary": "8201",
        "retained": "5301",
        "closing": "8401",
        "opening": "8301",
        "temporary_accounts": [
            "6101",
            "6102",
            "6103",
            "6201",
            "6302",
            "7101",
            "7102",
            "7103",
            "7104",
            "7201",
            "7501",
        ],
    },
    "receive": [rule_line("1201", "credit", "total", True)],
    "send": [rule_line("3101", "debit", "total", True)],
}
for kind, source, target, debit, credit in [
    ("incoming", "draft", "held", "1202", "1201"),
    ("incoming", "held", "collecting", "1203", "1202"),
    ("incoming", "held", "cleared", "1102", "1202"),
    ("incoming", "collecting", "cleared", "1102", "1203"),
    ("incoming", "collecting", "bounced", "1204", "1203"),
    ("incoming", "held", "bounced", "1204", "1202"),
    ("incoming", "held", "endorsed", "3101", "1202"),
    ("incoming", "bounced", "settled", "1102", "1204"),
    ("outgoing", "draft", "issued", "3101", "3102"),
    ("outgoing", "issued", "cleared", "3102", "1102"),
    ("outgoing", "issued", "bounced", "3102", "3101"),
]:
    RULES[f"cheque.{kind}.{source}.{target}"] = [
        dict(
            account=debit,
            side="debit",
            amount="total",
            beneficiary=(target == "endorsed"),
        ),
        dict(account=credit, side="credit", amount="total"),
    ]


class Command(BaseCommand):
    help = "Install editable draft accounting mappings. Accountant approval required before production."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        for unit in BusinessUnit.objects.all():
            for code, name, kinds in DEFAULTS:
                Account.objects.get_or_create(
                    business_unit=unit,
                    code=code,
                    defaults={
                        "name": name,
                        "detail_kinds": kinds,
                        "detail_required": bool(kinds),
                    },
                )
            for event, lines in RULES.items():
                PostingRule.objects.get_or_create(
                    business_unit=unit, event=event, defaults={"lines": lines}
                )
        for module, resource, actions in [
            ("payroll", "contract", ["view", "create"]),
            ("payroll", "payslip", ["view", "create", "issue"]),
            ("sales", "document", ["view", "create", "edit", "issue", "void", "print"]),
            ("crm", "party", ["view", "create", "edit"]),
            ("accounting", "voucher", ["view", "post"]),
            ("treasury", "payment", ["view", "create", "void"]),
            ("treasury", "cheque", ["view", "create", "transition"]),
            ("secretariat", "letter", ["view", "create", "edit", "delete"]),
            ("settings", "revision", ["view", "create"]),
        ]:
            for action in actions:
                Capability.objects.get_or_create(code=f"{module}.{resource}.{action}")
        for kind in [
            "request",
            "quote",
            "supply",
            "invoice",
            "return",
            "purchase",
            "purchase_return",
            "packing",
        ]:
            for action in [
                "view",
                "create",
                "edit",
                "issue",
                "void",
                "print",
                "approve",
                "fulfill",
            ]:
                Capability.objects.get_or_create(code=f"sales.{kind}.{action}")
        for action in ["approve", "fulfill"]:
            Capability.objects.get_or_create(code=f"sales.document.{action}")
        Capability.objects.get_or_create(code="sales.invoice.backdate")
        for code in [
            "accounting.year.close",
            "accounting.year.reopen",
            "accounting.period.close",
        ]:
            Capability.objects.get_or_create(code=code)
        marker, first_install = BootstrapState.objects.get_or_create(key="roles.v1")
        if first_install:
            all_codes = list(Capability.objects.values_list("code", flat=True))
            templates = {
                "مدیر سیستم": all_codes,
                "مدیر فروش": [c for c in all_codes if c.startswith(("sales.", "crm."))],
                "کارشناس فروش": [
                    c
                    for c in all_codes
                    if c.startswith(
                        ("sales.quote.", "sales.invoice.", "sales.request.", "crm.party.")
                    )
                    and c.endswith((".view", ".create", ".edit", ".issue", ".print"))
                ],
                "کارشناس محصول": ["catalog.product.create", "catalog.product.edit"],
                "حسابدار": [
                    c
                    for c in all_codes
                    if c.startswith(("accounting.", "treasury.", "payroll."))
                    or c
                    in [
                        "crm.party.view",
                        "sales.invoice.view",
                        "sales.purchase.view",
                        "catalog.price.view_cost",
                    ]
                ],
                "کارشناس تأمین": [
                    "sales.supply.view",
                    "sales.supply.fulfill",
                    "sales.supply.print",
                ],
                "فقط‌مشاهده": ["sales.document.view", "crm.party.view"],
                "مشتری": [],
            }
            for name, codes in templates.items():
                role, _ = Role.objects.get_or_create(name=name)
                if not role.permissions.exists() and not role.users.exists():
                    role.permissions.set(Capability.objects.filter(code__in=codes))
        system_role, _ = Role.objects.get_or_create(name="مدیر سیستم")
        system_role.permissions.set(Capability.objects.all())
        self.stdout.write(
            "Draft accounts and rules installed without overwriting existing mappings"
        )
