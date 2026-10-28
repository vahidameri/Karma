"""Build behind a cloud egress proxy with its supplied CA; TLS verification stays enabled."""

import json
import os
import socket
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

base = Path(__file__).resolve().parents[1]
env = os.environ.copy()
cache = base / ".cache/docker"
cache.mkdir(parents=True, exist_ok=True)
env.setdefault("DOCKER_CONFIG", str(cache))
command = ["docker", "compose", "-f", str(base / "compose.yaml")]
proxy = urllib.parse.urlsplit(env.get("HTTPS_PROXY", "")).hostname
if proxy:
    env.update(
        BUILD_PROXY_HOST=proxy,
        BUILD_PROXY_IP=socket.gethostbyname(proxy),
        BUILD_NETWORK="host",
    )
ca = env.get("SSL_CERT_FILE")
with tempfile.TemporaryDirectory(prefix="karma-build-") as temp:
    if ca and Path(ca).is_file():
        override = {
            "services": {
                name: {"build": {"secrets": ["cloud_ca"]}}
                for name in ["backend", "frontend"]
            },
            "secrets": {"cloud_ca": {"file": ca}},
        }
        path = Path(temp) / "ca.json"
        path.write_text(json.dumps(override))
        command += ["-f", str(path)]
    command += [
        "build",
        "--build-arg",
        "HTTP_PROXY",
        "--build-arg",
        "HTTPS_PROXY",
        "--build-arg",
        "NO_PROXY",
        "backend",
        "frontend",
    ]
    raise SystemExit(subprocess.call(command, cwd=base, env=env))
