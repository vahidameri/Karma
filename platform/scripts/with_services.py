"""Run a backend command using local development services, without logging secrets."""

import os
import subprocess
import sys
from pathlib import Path

base = Path(__file__).resolve().parents[1]
values = {}
for line in (base / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        key, value = line.split("=", 1)
        values[key] = value
os.environ.update(
    POSTGRES_HOST="127.0.0.1",
    POSTGRES_DB=values.get("POSTGRES_DB", "karma"),
    POSTGRES_USER="karma",
    POSTGRES_PASSWORD=values["POSTGRES_PASSWORD"],
    DJANGO_SECRET_KEY=values["DJANGO_SECRET_KEY"],
    REDIS_URL="redis://127.0.0.1:6379/0",
)
if "--search" in sys.argv:
    os.environ["ELASTICSEARCH_URL"] = "http://127.0.0.1:9200"
    sys.argv.remove("--search")
if "--database" in sys.argv:
    i = sys.argv.index("--database")
    database = sys.argv[i + 1]
    import re

    if not re.fullmatch(r"[A-Za-z0-9_]{1,63}", database):
        raise ValueError("Invalid database name")
    os.environ["POSTGRES_DB"] = database
    os.environ["KARMA_TASK_QUEUE"] = database
    del sys.argv[i : i + 2]
raise SystemExit(subprocess.call([sys.executable, *sys.argv[1:]], cwd=base / "backend"))
