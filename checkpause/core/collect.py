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

A failed upload is never dropped: the same de-identified payload is written to a
local outbox before the request and retried on a later launch, so one offline
minute or a server restart cannot silently remove a finished review. Nothing new
travels - the queued copy is exactly what an upload would have sent.
"""

import json
import os
import re
import threading
import uuid

import httpx

from checkpause.data.paths import DATA_DIR
from checkpause.data.settings import get_install_id, get_share_reviews

SAMPLE_ENDPOINT = "/v1/dataset/samples"
SAMPLE_TIMEOUT = 20.0

# Retries live next to the other local data. The cap keeps a permanently offline
# machine from growing the file without bound; older entries are kept, because
# they are the ones that have been waiting longest.
SAMPLES_OUTBOX_NAME = "samples_outbox.jsonl"
MAX_PENDING_SAMPLES = 200

_outbox_lock = threading.RLock()
_flush_lock = threading.Lock()

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
    side="",
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
        # The side the user played. Worth recording separately: the stored PGN
        # loses its tag pairs here, so without this the training row would not
        # say whose moves "my move" refers to.
        "side": side if side in ("white", "black") else "",
    }


def samples_outbox_path(base_dir=None):
    return os.path.join(base_dir or DATA_DIR, SAMPLES_OUTBOX_NAME)


def _sample_id(entry):
    return str(entry.get("client_sample_id") or "").strip()


def load_sample_outbox(base_dir=None):
    """Samples still waiting for a retry, oldest first."""
    path = samples_outbox_path(base_dir)
    if not os.path.isfile(path):
        return []
    entries = []
    seen = set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except ValueError:
                continue  # a torn line must not hide the samples around it
            if not isinstance(entry, dict):
                continue
            sample_id = _sample_id(entry)
            if not sample_id or sample_id in seen:
                continue
            if not (entry.get("pgn") or "").strip():
                continue
            seen.add(sample_id)
            entries.append(entry)
    return entries


def _write_sample_outbox(entries, base_dir=None):
    path = samples_outbox_path(base_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")
    os.replace(temp, path)


def append_sample_outbox(sample, base_dir=None):
    """Remember one sample for a retry. Returns its id, or "" when not kept."""
    if not sample or not (sample.get("pgn") or "").strip():
        return ""
    entry = dict(sample)
    sample_id = _sample_id(entry) or uuid.uuid4().hex
    entry["client_sample_id"] = sample_id
    with _outbox_lock:
        entries = load_sample_outbox(base_dir)
        if any(_sample_id(item) == sample_id for item in entries):
            return sample_id
        if len(entries) >= MAX_PENDING_SAMPLES:
            # Keep what is already waiting; the new sample still gets one direct
            # attempt, it just cannot also be stored for later.
            return ""
        entries.append(entry)
        _write_sample_outbox(entries, base_dir)
    return sample_id


def remove_sample_outbox(sample_id, base_dir=None):
    """Forget one queued sample once the server has taken it, or refused it."""
    sample_id = str(sample_id or "").strip()
    if not sample_id:
        return False
    with _outbox_lock:
        entries = load_sample_outbox(base_dir)
        remaining = [item for item in entries if _sample_id(item) != sample_id]
        if len(remaining) == len(entries):
            return False
        _write_sample_outbox(remaining, base_dir)
    return True


def _post_sample(server_url, sample, timeout=SAMPLE_TIMEOUT):
    """The server's answer, or None when the request never produced one."""
    url = (server_url or "").rstrip("/") + SAMPLE_ENDPOINT
    try:
        return httpx.post(url, json=sample, timeout=timeout)
    except httpx.HTTPError:
        return None  # offline, DNS, timeout: the sample stays queued


def _is_transient(response):
    """True when the same sample may be accepted on a later try."""
    if response is None:
        return True
    return response.status_code == 429 or response.status_code >= 500


def send_sample(server_url, sample, timeout=SAMPLE_TIMEOUT):
    """One upload attempt. True when the server accepted it.

    Never raises. This is the bare attempt; callers that want durability use
    ``deliver_sample``, which keeps the sample when this returns False.
    """
    if not sample or not (sample.get("pgn") or "").strip():
        return False
    response = _post_sample(server_url, sample, timeout)
    return response is not None and response.status_code < 400


def deliver_sample(server_url, sample, base_dir=None):
    """Upload one sample, keeping it queued unless the server takes it.

    The sample is written down before the request, so closing the app mid-flight
    cannot lose it either. True when this call was accepted.
    """
    if not sample or not (sample.get("pgn") or "").strip():
        return False
    entry = dict(sample)
    entry["client_sample_id"] = _sample_id(entry) or uuid.uuid4().hex
    queued = bool(append_sample_outbox(entry, base_dir))
    response = _post_sample(server_url, entry)
    if queued and _is_transient(response):
        return False
    if queued:
        # Accepted, or refused for good (duplicate, validation): either way a
        # retry would say the same thing again.
        remove_sample_outbox(entry["client_sample_id"], base_dir)
    return response is not None and response.status_code < 400


def flush_sample_outbox(server_url, base_dir=None):
    """Retry queued samples, oldest first. Returns how many were accepted.

    Stops at the first transient failure: when the network is down there is no
    point in waiting out a timeout per queued sample.
    """
    if not _flush_lock.acquire(blocking=False):
        return 0
    try:
        sent = 0
        for entry in load_sample_outbox(base_dir):
            response = _post_sample(server_url, entry)
            if _is_transient(response):
                break
            remove_sample_outbox(_sample_id(entry), base_dir)
            if response.status_code < 400:
                sent += 1
        return sent
    finally:
        _flush_lock.release()


def _deliver_in_background(server_url, sample):
    if deliver_sample(server_url, sample):
        flush_sample_outbox(server_url)


def send_sample_async(server_url, sample):
    """Deliver in a daemon thread so the interface never waits on it."""
    worker = threading.Thread(
        target=_deliver_in_background,
        args=(server_url, sample),
        daemon=True,
    )
    worker.start()


def flush_sample_outbox_async(server_url):
    """Retry what an earlier run could not send, without blocking startup."""
    worker = threading.Thread(
        target=flush_sample_outbox,
        args=(server_url,),
        daemon=True,
    )
    worker.start()


def maybe_send_local_sample(server_url, pgn, analysis, messages, reply, language, version, side=""):
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
        side=side,
    )
    if not sample["pgn"]:
        return None
    send_sample_async(server_url, sample)
    return sample
