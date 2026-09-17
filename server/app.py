"""CheckPause API server.

The client sends raw material - the game, the engine numbers, the conversation
so far - and this service builds the prompt, calls the model and streams the
reply back as plain text. The tuned prompt never leaves the server.

Requests are paid for with credits, and the charge has to survive the awkward
cases as well as the happy one:

* credits are reserved *before* the model runs, because a balance of one credit
  must not be able to start a request that costs fifty;
* the reservation is settled against the usage the upstream reports, so a user
  pays for what they actually got;
* a reply cut off mid-stream still settles. The upstream did the work and the
  token counts never arrived, so the reservation stands rather than the request
  coming free.
"""

import platform
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server import (
    accounts,
    config,
    payments,
    pricing,
    prompting,
    site,
    store,
    upstream,
)

SERVICE_NAME = "CheckPause Server"
SERVICE_VERSION = "0.4.0"
STARTED_AT = datetime.now(timezone.utc)

MAX_PGN_CHARS = 200_000
MAX_ANALYSIS_CHARS = 400_000


@asynccontextmanager
async def lifespan(_app):
    # A crash mid-request leaves a reservation that nothing will ever settle.
    # Charging it keeps the ledger matching the balances.
    store.sweep_stale_holds()
    yield


app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION, lifespan=lifespan)
app.include_router(accounts.router)
app.include_router(payments.router)
app.include_router(site.router)


class ConversationMessage(BaseModel):
    role: str
    content: str


class AnalyzeRequest(BaseModel):
    pgn: str = Field(min_length=1, max_length=MAX_PGN_CHARS)
    analysis: str = Field(default="", max_length=MAX_ANALYSIS_CHARS)
    history: list[ConversationMessage] = Field(default_factory=list)
    language: str = Field(default="", max_length=16)


def settle(hold_id, usage):
    """Charge for a finished request.

    An uncounted request pays the reservation: the upstream generated tokens
    even though the counts never made it back, so it is not free.
    """
    if usage.counted:
        return store.settle_hold(
            hold_id,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost=pricing.credits_for(usage.input_tokens, usage.output_tokens),
            price_version=pricing.PRICE_VERSION,
        )
    return store.settle_hold(hold_id, note="usage was never counted")


async def billed(stream, usage, hold_id):
    """Relay the reply, then close the reservation it ran against."""
    try:
        async for piece in upstream.iter_text(stream, usage):
            yield piece
    finally:
        try:
            settle(hold_id, usage)
        except store.StoreError:
            # The reply is already on its way; a settlement that fails must not
            # become an exception the client cannot do anything with. The
            # reservation stays open until the startup sweep picks it up.
            pass


@app.get("/status")
def status():
    """Machine-readable status. The front page belongs to the shop now."""
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
    user=Depends(accounts.require_user),
):
    """Build the prompt on the server and stream the reply back."""
    messages = prompting.build_messages(
        request.pgn, request.analysis, request.history, request.language
    )

    # The cap passed here is the one sent upstream, so the reservation covers
    # the most the request is able to cost.
    reservation = pricing.estimate_hold(
        messages, config.max_answer_tokens()
    )
    try:
        hold_id = store.open_hold(
            user["id"], reservation, note="analyze reservation"
        )
    except store.NoCredits as error:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "no_credits",
                "message": "the balance does not cover this request",
                "balance": error.balance,
                "needed": error.needed,
            },
        ) from error

    try:
        stream = await upstream.open_stream(messages)
    except upstream.UpstreamError as error:
        # Nothing was generated, so nothing is charged.
        store.refund_hold(hold_id, note="upstream refused the request")
        raise HTTPException(
            status_code=502,
            detail={"code": "upstream_error", "message": str(error)},
        ) from error

    return StreamingResponse(
        billed(stream, upstream.Usage(), hold_id),
        media_type="text/plain; charset=utf-8",
    )
