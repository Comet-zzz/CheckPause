"""Send a de-identified review sample to the server for model training.

A bring-your-own-key reply is produced upstream and never touches the server, so
the only way the project can learn from it is if the client sends a copy. What
travels is raw material only: the game, the engine numbers, the conversation and
the reply. No account, no key, no token - just a random install id, which exists
so the server can rate limit an install without knowing who it is.

Consent for this is given once, by accepting the agreement shown during
installation; there is deliberately no in-app switch. Whether the client sends
is therefore always yes, and ``get_share_reviews`` keeps that decision in one
named place rather than scattering the assumption.

This is best effort by design. A sample that cannot be sent is dropped, because
an upload failure must never interrupt a reply the user already has.
"""

import re
import threading

import httpx

from checkpause.data.settings import get_install_id, get_share_reviews

SAMPLE_ENDPOINT = "/v1/dataset/samples"
SAMPLE_TIMEOUT = 20.0

# The server caps the conversation it will keep; trimming here means an upload
# is never rejected for being merely long.
MAX_MESSAGES = 40

# A PGN tag pair line, e.g. [White "Magnus"].
_PGN_TAG = re.compile(r'^\[\s*([A-Za-z0-9_]+)\s+"(?:[^"\\]|\\.)*"\s*\]\s*$')

# Tag pairs that describe the position rather than the people. Everything else
# (White, Black, Event, Site, Date, Round, Annotator, ...) is dropped: those are
# where a pasted game carries real names or platform ids.
_KEEP_PGN_TAGS = {"fen", "setup"}


def strip_pgn_headers(pgn):
    """Drop every PGN tag pair except the two that describe the position.

    A pasted game very often carries [White]/[Black]/[Event]/[Site]/[Date], so
    the raw PGN is the classic place de-identification leaks. [FEN] and [SetUp]
    are kept because a game that starts from a non-standard position cannot be
    understood without them, and neither names a person.
    """
    kept = []
    for line in (pgn or "").splitlines():
        match = _PGN_TAG.match(line)
        if match:
            if match.group(1).casefold() in _KEEP_PGN_TAGS:
                kept.append(line.strip())
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def build_sample(
    pgn,
    analysis,
    messages,
    reply,
    language="",
    client_version="",
    install_id="",
    source="local",
):
    """The de-identified material a local review contributes.

    The system entry is dropped: in local mode it is the frozen client prompt,
    which is not what a training example should be built from. Only user and
    assistant turns travel, and only the most recent ones.
    """
    history = []
    for message in messages or []:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        if role not in ("user", "assistant"):
            continue
        history.append({"role": role, "content": message.get("content") or ""})
    return {
        "pgn": strip_pgn_headers(pgn),
        "analysis": (analysis or "").strip(),
        "history": history[-MAX_MESSAGES:],
        "reply": reply or "",
        "language": language or "",
        "client_version": client_version or "",
        "install_id": install_id or "",
        "source": source or "local",
    }


def send_sample(server_url, sample, timeout=SAMPLE_TIMEOUT):
    """Best-effort upload. True when the server accepted it.

    Never raises. A dropped sample costs one training example, while an
    exception raised here would surface inside a reply the user already has.
    """
    if not sample or not (sample.get("pgn") or "").strip():
        return False
    url = (server_url or "").rstrip("/") + SAMPLE_ENDPOINT
    try:
        response = httpx.post(url, json=sample, timeout=timeout)
    except httpx.HTTPError:
        return False
    return response.status_code < 400


def send_sample_async(server_url, sample):
    """Upload in a daemon thread so the interface never waits on it."""
    worker = threading.Thread(
        target=send_sample,
        args=(server_url, sample),
        daemon=True,
    )
    worker.start()


def maybe_send_local_sample(server_url, pgn, analysis, messages, reply, language, version):
    """Build and send a sample for a local review.

    Returns the sample that was built, or None when there was nothing to send.
    Callers use the return value only in tests; the interface ignores it.
    """
    if not get_share_reviews():
        return None
    sample = build_sample(
        pgn,
        analysis,
        messages,
        reply,
        language=language,
        client_version=version,
        install_id=get_install_id(),
        source="local",
    )
    if not sample["pgn"]:
        return None
    send_sample_async(server_url, sample)
    return sample
