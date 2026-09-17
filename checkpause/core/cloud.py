"""Talk to the CheckPause server.

Two things here are deliberate. The client knows nothing about the prompt: it
sends the game, the engine numbers and the conversation so far, and the server
assembles the rest, which is what keeps the tuned prompt off user machines.
And the password is never kept - signing in returns a token, and only the token
is stored.

Failure messages are built from the server's short error codes rather than its
English text, so a user reads the same wording the rest of the app uses.
"""

import httpx

from checkpause.i18n import t

ENDPOINT = "/v1/analyze"
REGISTER_ENDPOINT = "/v1/accounts/register"
LOGIN_ENDPOINT = "/v1/accounts/login"
LOGOUT_ENDPOINT = "/v1/accounts/logout"
ME_ENDPOINT = "/v1/accounts/me"

REQUEST_TIMEOUT = 180.0
ACCOUNT_TIMEOUT = 30.0

# Server codes that have something better to say than "HTTP 400".
ERROR_KEYS = {
    "username_taken": "cloud_username_taken",
    "username_invalid": "cloud_username_invalid",
    "password_too_short": "cloud_password_too_short",
    "bad_credentials": "cloud_bad_credentials",
    "missing_token": "cloud_signin_required",
    "unknown_token": "cloud_signin_required",
    "no_credits": "cloud_no_credit",
}


class CloudRequestError(RuntimeError):
    """A cloud request could not be completed."""

    def __init__(self, message, code="", detail=None):
        super().__init__(message)
        self.code = code
        self.detail = detail or {}


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


def headers(token):
    token = (token or "").strip()
    return {"Authorization": "Bearer " + token} if token else {}


def _url(server_url, path):
    return (server_url or "").rstrip("/") + path


def _detail(response):
    """The server's structured explanation, if it managed to send one.

    Best effort on purpose: this runs while an error is already being handled,
    so anything that goes wrong reading the body must fall back to the generic
    message rather than replace one failure with another.
    """
    try:
        response.read()
        detail = response.json().get("detail")
    except Exception:
        return {}
    return detail if isinstance(detail, dict) else {}


def _error(response, language):
    detail = _detail(response)
    code = detail.get("code", "")
    if code == "no_credits" and "balance" in detail:
        return CloudRequestError(
            t(
                "cloud_no_credit_detail",
                language,
                balance=detail.get("balance", 0),
                needed=detail.get("needed", 0),
            ),
            code,
            detail,
        )
    key = ERROR_KEYS.get(code)
    if key:
        return CloudRequestError(t(key, language), code, detail)
    return CloudRequestError(
        t("cloud_server_error", language, code=response.status_code), code
    )


def _post(server_url, path, payload, language, token=""):
    try:
        response = httpx.post(
            _url(server_url, path),
            json=payload,
            headers=headers(token),
            timeout=ACCOUNT_TIMEOUT,
        )
    except httpx.TimeoutException as exc:
        raise CloudRequestError(t("cloud_timeout", language)) from exc
    except httpx.RequestError as exc:
        raise CloudRequestError(t("cloud_unreachable", language)) from exc
    if response.status_code >= 400:
        raise _error(response, language)
    return response.json()


def register(server_url, username, password, language="zh-CN"):
    """Create an account. Returns the token and the account it belongs to."""
    return _post(
        server_url,
        REGISTER_ENDPOINT,
        {"username": username, "password": password},
        language,
    )


def sign_in(server_url, username, password, language="zh-CN"):
    return _post(
        server_url,
        LOGIN_ENDPOINT,
        {"username": username, "password": password},
        language,
    )


def sign_out(server_url, token, language="zh-CN"):
    """Best effort: a session that cannot end here can be revoked server-side."""
    try:
        httpx.post(
            _url(server_url, LOGOUT_ENDPOINT),
            headers=headers(token),
            timeout=ACCOUNT_TIMEOUT,
        )
    except httpx.HTTPError:
        return


def fetch_account(server_url, token, language="zh-CN"):
    """Ask the server for the balance instead of trusting a cached number."""
    try:
        response = httpx.get(
            _url(server_url, ME_ENDPOINT),
            headers=headers(token),
            timeout=ACCOUNT_TIMEOUT,
        )
    except httpx.TimeoutException as exc:
        raise CloudRequestError(t("cloud_timeout", language)) from exc
    except httpx.RequestError as exc:
        raise CloudRequestError(t("cloud_unreachable", language)) from exc
    if response.status_code >= 400:
        raise _error(response, language)
    return response.json()


def stream_reply(server_url, token, pgn, analysis, history=None, language="zh-CN"):
    """Yield reply fragments from the server.

    Raises CloudRequestError when the request cannot be completed, since the
    caller wants to show a message rather than a stack trace.
    """
    payload = build_payload(pgn, analysis, history, language)

    try:
        with httpx.stream(
            "POST",
            _url(server_url, ENDPOINT),
            json=payload,
            headers=headers(token),
            timeout=REQUEST_TIMEOUT,
        ) as response:
            if response.status_code >= 400:
                raise _error(response, language)
            for fragment in response.iter_text():
                if fragment:
                    yield fragment
    except CloudRequestError:
        raise
    except httpx.TimeoutException as exc:
        raise CloudRequestError(t("cloud_timeout", language)) from exc
    except httpx.RequestError as exc:
        raise CloudRequestError(t("cloud_unreachable", language)) from exc
