"""Create local development secrets once; never replaces existing configuration."""

import secrets
from pathlib import Path

path = Path(__file__).resolve().parents[1] / ".env"
if path.exists():
    print("Existing .env preserved")
else:
    path.write_text(
        "POSTGRES_DB=karma\nPOSTGRES_PASSWORD="
        + secrets.token_hex(24)
        + "\nDJANGO_SECRET_KEY="
        + secrets.token_urlsafe(60)
        + "\n"
    )
    path.chmod(0o600)
    print(
        "Created private .env with independent development secrets; no application accounts created"
    )
