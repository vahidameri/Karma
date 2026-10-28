"""Owner-only PostgreSQL backup, with optional restore into a newly created disposable DB."""

import argparse
import os
import secrets
import subprocess
from datetime import UTC, datetime
from pathlib import Path

base = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--verify", action="store_true")
args = p.parse_args()
config = {}
for line in (base / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        key, value = line.split("=", 1)
        config[key] = value
source = config.get("POSTGRES_DB", "karma")
out = base / "backups"
out.mkdir(mode=0o700, exist_ok=True)
path = out / (
    "karma-"
    + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    + "-"
    + secrets.token_hex(3)
    + ".dump"
)
command = ["docker", "compose", "exec", "-T", "postgres"]


def run(*parts, **kwargs):
    return subprocess.run(command + list(parts), cwd=base, check=True, **kwargs)


with path.open("xb") as f:
    os.chmod(path, 0o600)
    run("pg_dump", "-U", "karma", "-Fc", source, stdout=f)
print("Backup created:", path.name)
if args.verify:
    target = "karma_restore_" + secrets.token_hex(6)
    run("createdb", "-U", "karma", target)
    try:
        with path.open("rb") as f:
            run(
                "pg_restore",
                "-U",
                "karma",
                "-d",
                target,
                stdin=f,
                stdout=subprocess.DEVNULL,
            )
        query = "SELECT count(*) FROM catalog_product; SELECT count(*) FROM catalog_standard; SELECT count(*) FROM accounting_voucher;"
        before = run(
            "psql", "-U", "karma", "-d", source, "-Atc", query, capture_output=True
        ).stdout
        after = run(
            "psql", "-U", "karma", "-d", target, "-Atc", query, capture_output=True
        ).stdout
        if before != after:
            raise RuntimeError("Restored row counts do not match")
        print("Disposable restore verified: product, standard and voucher counts match")
    finally:
        run("dropdb", "-U", "karma", target)
