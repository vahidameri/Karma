from django.db import migrations


def update_defaults(apps, schema_editor):
    Rule = apps.get_model("accounting", "PostingRule")
    for rule in Rule.objects.filter(event__in=["return", "purchase_return"]):
        # Update only the exact defaults emitted by alpha bootstrap, preserving custom rules.
        old = (
            [
                {"account": "6102", "side": "debit", "amount": "net", "party": False},
                {"account": "3201", "side": "debit", "amount": "tax", "party": False},
                {"account": "1201", "side": "credit", "amount": "total", "party": True},
            ]
            if rule.event == "return"
            else [
                {"account": "3101", "side": "debit", "amount": "total", "party": True},
                {"account": "7103", "side": "credit", "amount": "net", "party": False},
                {"account": "1402", "side": "credit", "amount": "tax", "party": False},
            ]
        )
        if rule.lines == old:
            rule.lines.insert(
                1,
                {
                    "account": "6201" if rule.event == "return" else "7104",
                    "side": "debit" if rule.event == "return" else "credit",
                    "amount": "shipping",
                    "party": False,
                },
            )
            rule.save(update_fields=["lines"])


class Migration(migrations.Migration):
    dependencies = [("accounting", "0002_ledger_guards")]
    operations = [migrations.RunPython(update_defaults, migrations.RunPython.noop)]
