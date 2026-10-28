from django.db import migrations


def install(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "sqlite":
        sql = [
            """CREATE TRIGGER ledger_post_balanced BEFORE UPDATE OF status ON accounting_voucher WHEN NEW.status='permanent' BEGIN SELECT CASE WHEN (SELECT COUNT(*) FROM accounting_voucherline WHERE voucher_id=NEW.id)<2 OR (SELECT COALESCE(SUM(debit-credit),0) FROM accounting_voucherline WHERE voucher_id=NEW.id)!=0 THEN RAISE(ABORT,'Unbalanced voucher') END; END""",
            """CREATE TRIGGER ledger_header_immutable BEFORE UPDATE ON accounting_voucher WHEN OLD.status='permanent' BEGIN SELECT RAISE(ABORT,'Permanent voucher is immutable'); END""",
            """CREATE TRIGGER ledger_header_delete BEFORE DELETE ON accounting_voucher WHEN OLD.status='permanent' BEGIN SELECT RAISE(ABORT,'Permanent voucher is immutable'); END""",
            """CREATE TRIGGER ledger_no_direct_post BEFORE INSERT ON accounting_voucher WHEN NEW.status='permanent' BEGIN SELECT RAISE(ABORT,'Post after inserting balanced lines'); END""",
        ]
        for operation in ["INSERT", "UPDATE", "DELETE"]:
            ref = "OLD" if operation == "DELETE" else "NEW"
            condition = (
                f"(SELECT status FROM accounting_voucher WHERE id={ref}.voucher_id)='permanent'"
            )
            if operation == "UPDATE":
                condition += " OR (SELECT status FROM accounting_voucher WHERE id=OLD.voucher_id)='permanent'"
            sql.append(
                f"CREATE TRIGGER ledger_line_{operation.lower()} BEFORE {operation} ON accounting_voucherline WHEN {condition} BEGIN SELECT RAISE(ABORT,'Permanent voucher lines are immutable'); END"
            )
    elif vendor == "postgresql":
        sql = [
            """CREATE FUNCTION karma_guard_header() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF TG_OP='DELETE' THEN IF OLD.status='permanent' THEN RAISE EXCEPTION 'Permanent voucher is immutable'; END IF; RETURN OLD; END IF;
        IF TG_OP='INSERT' AND NEW.status='permanent' THEN RAISE EXCEPTION 'Post after inserting balanced lines'; END IF;
        IF TG_OP='UPDATE' AND OLD.status='permanent' THEN RAISE EXCEPTION 'Permanent voucher is immutable'; END IF;
        IF NEW.status='permanent' AND ((SELECT COUNT(*) FROM accounting_voucherline WHERE voucher_id=NEW.id)<2 OR (SELECT COALESCE(SUM(debit-credit),0) FROM accounting_voucherline WHERE voucher_id=NEW.id)<>0) THEN RAISE EXCEPTION 'Unbalanced voucher'; END IF;
        RETURN NEW; END $$""",
            "CREATE TRIGGER ledger_header BEFORE INSERT OR UPDATE OR DELETE ON accounting_voucher FOR EACH ROW EXECUTE FUNCTION karma_guard_header()",
            """CREATE FUNCTION karma_guard_line() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF TG_OP<>'INSERT' THEN IF (SELECT status FROM accounting_voucher WHERE id=OLD.voucher_id)='permanent' THEN RAISE EXCEPTION 'Permanent lines are immutable'; END IF; END IF;
        IF TG_OP<>'DELETE' THEN IF (SELECT status FROM accounting_voucher WHERE id=NEW.voucher_id)='permanent' THEN RAISE EXCEPTION 'Permanent lines are immutable'; END IF; RETURN NEW; END IF;
        RETURN OLD; END $$""",
            "CREATE TRIGGER ledger_line BEFORE INSERT OR UPDATE OR DELETE ON accounting_voucherline FOR EACH ROW EXECUTE FUNCTION karma_guard_line()",
        ]
    else:
        raise RuntimeError("Unsupported database for ledger integrity")
    for statement in sql:
        schema_editor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [("accounting", "0001_initial")]
    operations = [migrations.RunPython(install)]
