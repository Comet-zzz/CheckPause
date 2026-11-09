"""Talk to the CheckPause server.

Two things here are deliberate. The client knows nothing about the prompt: it
sends the game, the engine numbers and the conversation so far, and the server
assembles the rest, which is what keeps the tuned prompt off user machines.
And the password is never kept - signing in returns a token, and only the token
is stored.

Failure messages are built from the server's short error codes rather than its
English text, so a user reads the same wording the rest of the app uses.
"""

from urllib.parse import quote, urlencode

import httpx

from checkpause.i18n import t

ENDPOINT = "/v1/analyze"
REGISTER_ENDPOINT = "/v1/accounts/register"
LOGIN_ENDPOINT = "/v1/accounts/login"
LOGOUT_ENDPOINT = "/v1/accounts/logout"
ME_ENDPOINT = "/v1/accounts/me"
RENAME_ENDPOINT = "/v1/accounts/rename"
CLOSE_ACCOUNT_ENDPOINT = "/v1/accounts/me"
PACKS_ENDPOINT = "/v1/pay/packs"
ORDERS_ENDPOINT = "/v1/pay/orders"
PUZZLE_NEXT_ENDPOINT = "/v1/puzzles/next"
PUZZLE_RETRY_ENDPOINT = "/v1/puzzles/retry"
PUZZLE_DAILY_ENDPOINT = "/v1/puzzles/daily"
PUZZLE_SOLVED_ENDPOINT = "/v1/puzzles/solved"
PUZZLE_ATTEMPT_ENDPOINT = "/v1/puzzles/attempt"
PUZZLE_STATS_ENDPOINT = "/v1/puzzles/stats"
PUZZLE_PROFILE_ENDPOINT = "/v1/puzzles/profile"

REQUEST_TIMEOUT = 180.0
ACCOUNT_TIMEOUT = 30.0

# Server codes that have something better to say than "HTTP 400".
ERROR_KEYS = {
    "username_taken": "cloud_username_taken",
    "username_invalid": "cloud_username_invalid",
    "username_unchanged": "cloud_username_unchanged",
    "password_too_short": "cloud_password_too_short",
    "bad_credentials": "cloud_bad_credentials",
    "missing_token": "cloud_signin_required",
    "unknown_token": "cloud_signin_required",
    "no_credits": "cloud_no_credit",
    "too_many_attempts": "cloud_too_many_attempts",
    "no_puzzles": "cloud_no_puzzles",
    "no_mistakes": "cloud_no_mistakes",
    "puzzle_not_found": "cloud_puzzle_not_found",
}


class CloudRequestError(RuntimeError):
    """A cloud request could not be completed."""

    def __init__(self, message, code="", detail=None):
        super().__init__(message)
        self.code = code
        self.detail = detail or {}


def build_payload(pgn, analysis, history=None, language="", side=""):
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
        # Which side the user played, when the game's tag pairs made that
        # clear; the server tells the model so "my 5th move" is not guessed.
        "side": side if side in ("white", "black") else "",
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
    return CloudRequestError(t("cloud_server_error", language, code=response.status_code), code)


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


def _get(server_url, path, token="", language="zh-CN"):
    try:
        response = httpx.get(
            _url(server_url, path),
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
    return _get(server_url, ME_ENDPOINT, token, language)


def close_account(server_url, token, language="zh-CN"):
    """Delete the account and its practice history. Irreversible."""
    try:
        response = httpx.delete(
            _url(server_url, CLOSE_ACCOUNT_ENDPOINT),
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


def rename(server_url, token, username, language="zh-CN"):
    """Change the login name. Costs credits; the server decides how many."""
    return _post(
        server_url,
        RENAME_ENDPOINT,
        {"username": username},
        language,
        token=token,
    )


def fetch_packs(server_url, language="zh-CN"):
    """What the server is willing to sell, and for how much."""
    return _get(server_url, PACKS_ENDPOINT, "", language)


def create_order(server_url, token, yuan, language="zh-CN"):
    """Open an order; the reply carries the page the browser should open."""
    return _post(server_url, ORDERS_ENDPOINT, {"yuan": int(yuan)}, language, token=token)


def order_status(server_url, token, order_id, language="zh-CN"):
    """Whether an order has been paid.

    Asking is what makes a purchase arrive: Alipay either notifies the server
    or, as here, the server asks Alipay.
    """
    return _get(server_url, ORDERS_ENDPOINT + "/" + str(order_id), token, language)


def stream_reply(server_url, token, pgn, analysis, history=None, language="zh-CN", side=""):
    """Yield reply fragments from the server.

    Raises CloudRequestError when the request cannot be completed, since the
    caller wants to show a message rather than a stack trace.
    """
    payload = build_payload(pgn, analysis, history, language, side)

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


def next_puzzle(server_url, token, theme="", difficulty="normal", language="zh-CN"):
    """One puzzle near the account's rating."""
    query = urlencode({"theme": theme, "difficulty": difficulty})
    return _get(server_url, PUZZLE_NEXT_ENDPOINT + "?" + query, token, language)


def retry_puzzle(server_url, token, language="zh-CN"):
    """A failed puzzle that has not been solved since."""
    return _get(server_url, PUZZLE_RETRY_ENDPOINT, token, language)


def fetch_daily_puzzle(server_url, token, difficulty="normal", language="zh-CN"):
    """The same puzzle for this account for the whole UTC day."""
    query = urlencode({"difficulty": difficulty})
    return _get(server_url, PUZZLE_DAILY_ENDPOINT + "?" + query, token, language)


def fetch_solved_puzzles(server_url, token, limit=30, language="zh-CN"):
    """Recently solved puzzles, newest first, for review practice."""
    query = urlencode({"limit": int(limit)})
    return _get(server_url, PUZZLE_SOLVED_ENDPOINT + "?" + query, token, language)


def vote_puzzle(server_url, token, puzzle_id, vote, language="zh-CN"):
    """Mark a puzzle as helpful or broken; a down vote also hides it."""
    path = "/v1/puzzles/" + quote(str(puzzle_id), safe="") + "/vote"
    return _post(server_url, path, {"vote": int(vote)}, language, token=token)


def submit_puzzle_attempt(
    server_url,
    token,
    puzzle_id,
    result,
    duration_ms=0,
    hinted=False,
    rated=True,
    client_attempt_id="",
    language="zh-CN",
):
    """Record a session. The reply carries the rating after it."""
    return _post(
        server_url,
        PUZZLE_ATTEMPT_ENDPOINT,
        {
            "puzzle_id": puzzle_id,
            "result": result,
            "duration_ms": int(duration_ms),
            "hinted": bool(hinted),
            "rated": bool(rated),
            "client_attempt_id": client_attempt_id,
        },
        language,
        token=token,
    )


def fetch_puzzle_stats(server_url, token, days=30, language="zh-CN"):
    query = urlencode({"days": int(days)})
    return _get(server_url, PUZZLE_STATS_ENDPOINT + "?" + query, token, language)


def fetch_puzzle_profile(server_url, token, language="zh-CN"):
    return _get(server_url, PUZZLE_PROFILE_ENDPOINT, token, language)
