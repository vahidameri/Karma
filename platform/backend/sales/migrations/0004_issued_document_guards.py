from django.db import migrations


def install(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    model = apps.get_model("sales", "Document")
    fields = [f.column for f in model._meta.fields if f.column != "status"]
    if vendor == "sqlite":
        changed = " OR ".join(f'NEW."{f}" IS NOT OLD."{f}"' for f in fields)
        sql = [
            f"CREATE TRIGGER document_immutable BEFORE UPDATE ON sales_document WHEN OLD.status<>'draft' AND ({changed}) BEGIN SELECT RAISE(ABORT,'Issued document is immutable'); END",
            "CREATE TRIGGER document_no_delete BEFORE DELETE ON sales_document WHEN OLD.status<>'draft' BEGIN SELECT RAISE(ABORT,'Issued document is immutable'); END",
        ]
        for op in ["INSERT", "UPDATE", "DELETE"]:
            ref = "OLD" if op == "DELETE" else "NEW"
            condition = f"(SELECT status FROM sales_document WHERE id={ref}.document_id)<>'draft'"
            if op == "UPDATE":
                condition += (
                    " OR (SELECT status FROM sales_document WHERE id=OLD.document_id)<>'draft'"
                )
            sql.append(
                f"CREATE TRIGGER document_line_{op.lower()} BEFORE {op} ON sales_documentline WHEN {condition} BEGIN SELECT RAISE(ABORT,'Issued lines are immutable'); END"
            )
    else:
        sql = [
            """CREATE FUNCTION karma_guard_document() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF OLD.status<>'draft' THEN
        IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Issued document is immutable'; END IF;
        IF (to_jsonb(NEW)-'status') IS DISTINCT FROM (to_jsonb(OLD)-'status') THEN RAISE EXCEPTION 'Issued document is immutable'; END IF; END IF;
        IF TG_OP='DELETE' THEN RETURN OLD; END IF; RETURN NEW; END $$""",
            "CREATE TRIGGER document_immutable BEFORE UPDATE OR DELETE ON sales_document FOR EACH ROW EXECUTE FUNCTION karma_guard_document()",
            """CREATE FUNCTION karma_guard_document_line() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF TG_OP<>'INSERT' THEN IF (SELECT status FROM sales_document WHERE id=OLD.document_id FOR UPDATE)<>'draft' THEN RAISE EXCEPTION 'Issued lines are immutable'; END IF; END IF;
        IF TG_OP<>'DELETE' THEN IF (SELECT status FROM sales_document WHERE id=NEW.document_id FOR UPDATE)<>'draft' THEN RAISE EXCEPTION 'Issued lines are immutable'; END IF; RETURN NEW; END IF;
        RETURN OLD; END $$""",
            "CREATE TRIGGER document_line_immutable BEFORE INSERT OR UPDATE OR DELETE ON sales_documentline FOR EACH ROW EXECUTE FUNCTION karma_guard_document_line()",
        ]
    for statement in sql:
        schema_editor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [("sales", "0003_inquiry_inquiryquota")]
    operations = [migrations.RunPython(install)]
