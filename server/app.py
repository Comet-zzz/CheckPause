"""CheckPause API server.

The client sends raw material - the game, the engine numbers, the conversation
so far - and this service builds the prompt, calls the model and streams the
reply back as plain text. The tuned prompt never leaves the server.
"""

import platform
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server import config, deepseek, prompting

SERVICE_NAME = "CheckPause Server"
SERVICE_VERSION = "0.2.0"
STARTED_AT = datetime.now(timezone.utc)

MAX_PGN_CHARS = 200_000
MAX_ANALYSIS_CHARS = 400_000

app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)


class ConversationMessage(BaseModel):
    role: str
    content: str


class AnalyzeRequest(BaseModel):
    pgn: str = Field(min_length=1, max_length=MAX_PGN_CHARS)
    analysis: str = Field(default="", max_length=MAX_ANALYSIS_CHARS)
    history: list[ConversationMessage] = Field(default_factory=list)
    language: str = Field(default="", max_length=16)


def _require_token(token):
    """Stop scanners and casual abuse until real accounts exist."""
    expected = config.access_token()
    if expected and token != expected:
        raise HTTPException(status_code=401, detail="invalid or missing token")


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
        "prompt": "placeholder" if config.using_placeholder_prompt() else "tuned",
        "upstream_configured": bool(config.api_key()),
    }


@app.get("/health")
def health():
    """Machine-facing check, kept separate for monitoring later on."""
    return {"status": "ok"}


@app.post("/v1/analyze")
async def analyze(
    request: AnalyzeRequest,
    x_checkpause_token: str = Header(default=""),
):
    """Build the prompt on the server and stream the reply back."""
    _require_token(x_checkpause_token)

    messages = prompting.build_messages(
        request.pgn, request.analysis, request.history, request.language
    )

    try:
        stream = await deepseek.open_stream(messages)
    except deepseek.UpstreamError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return StreamingResponse(
        deepseek.iter_text(stream),
        media_type="text/plain; charset=utf-8",
    )
