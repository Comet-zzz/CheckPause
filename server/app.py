"""CheckPause API server.

Milestone 1 only proves the deployment pipeline: the code runs on the server
and answers requests from the public internet.

Milestone 2 adds the real endpoint that builds the prompt server-side, calls
DeepSeek, and streams the reply back to the client.
"""

import platform
import sys
from datetime import datetime, timezone

from fastapi import FastAPI

SERVICE_NAME = "CheckPause Server"
SERVICE_VERSION = "0.1.0"
STARTED_AT = datetime.now(timezone.utc)

app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)


@app.get("/")
def status():
    """Human-facing status page: open the address in a browser."""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": "ok",
        "host": platform.node(),
        "python": sys.version.split()[0],
        "started_at": STARTED_AT.isoformat(),
        "uptime_seconds": int(
            (datetime.now(timezone.utc) - STARTED_AT).total_seconds()
        ),
    }


@app.get("/health")
def health():
    """Machine-facing check, kept separate for monitoring later on."""
    return {"status": "ok"}
