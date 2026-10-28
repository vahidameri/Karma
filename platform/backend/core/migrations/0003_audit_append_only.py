from django.db import migrations


def install(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for op in ["UPDATE", "DELETE"]:
            schema_editor.execute(
                f"CREATE TRIGGER audit_no_{op.lower()} BEFORE {op} ON core_auditentry BEGIN SELECT RAISE(ABORT,'Audit log is append-only'); END"
            )
    else:
        schema_editor.execute(
            "CREATE FUNCTION karma_audit_append_only() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Audit log is append-only'; END $$"
        )
        schema_editor.execute(
            "CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE ON core_auditentry FOR EACH ROW EXECUTE FUNCTION karma_audit_append_only()"
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0002_outboxevent_attempts_outboxevent_last_error_and_more")]
    operations = [migrations.RunPython(install)]
