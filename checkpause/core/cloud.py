"""Talk to the CheckPause server.

This path deliberately knows nothing about the prompt: it sends the game, the
engine numbers and the conversation so far, and the server assembles the rest.
That is what keeps the tuned prompt off user machines.
"""

import httpx

from checkpause.i18n import t

ENDPOINT = "/v1/analyze"
REQUEST_TIMEOUT = 180.0


class CloudRequestError(RuntimeError):
    """A cloud request could not be completed."""


def build_payload(pgn, analysis, history=None, language=""):
    """The only material a client is allowed to send."""
    return {
        "pgn": (pgn or "").strip(),
        "analysis": (analysis or "").strip(),
        "history": [
            {"role": item.get("role"), "content": item.get("content")}
            for item in (history or [])
            if isinstance(item, dict) and item.get("role") in ("user", "assistant")
        ],
        "language": (language or "").strip(),
    }


def _raise_for_status(status, language):
    if status == 401:
        raise CloudRequestError(t("cloud_unauthorized", language))
    if status == 402:
        raise CloudRequestError(t("cloud_no_credit", language))
    if status >= 400:
        raise CloudRequestError(t("cloud_server_error", language, code=status))


def stream_reply(server_url, pgn, analysis, history=None, language="zh-CN"):
    """Yield reply fragments from the server.

    Raises CloudRequestError when the request cannot be completed, since the
    caller wants to show a message rather than a stack trace.
    """
    url = (server_url or "").rstrip("/") + ENDPOINT
    payload = build_payload(pgn, analysis, history, language)

    try:
        with httpx.stream(
            "POST", url, json=payload, timeout=REQUEST_TIMEOUT
        ) as response:
            _raise_for_status(response.status_code, language)
            for fragment in response.iter_text():
                if fragment:
                    yield fragment
    except CloudRequestError:
        raise
    except httpx.TimeoutException as exc:
        raise CloudRequestError(t("cloud_timeout", language)) from exc
    except httpx.RequestError as exc:
        raise CloudRequestError(t("cloud_unreachable", language)) from exc
