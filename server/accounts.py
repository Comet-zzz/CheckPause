"""Account endpoints: sign up, sign in, and see the balance.

The client keeps the token it gets back and sends it as a bearer token on every
later request. Nothing here knows about prompts or the model, and nothing here
trusts the client: a balance shown to a user is read from the ledger.

Errors carry a short ``code`` so the client can pick its own wording instead of
showing the server's English to a user.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from server import config, ratelimit, store

router = APIRouter(tags=["accounts"])


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class Account(BaseModel):
    username: str
    balance: int
    created_at: str
    first_topup_at: str | None = None


class Session(BaseModel):
    token: str
    account: Account


class LedgerEntry(BaseModel):
    delta: int
    balance_after: int
    reason: str
    input_tokens: int
    output_tokens: int
    price_version: str
    created_at: str


def _account(user):
    return Account(
        username=user["username"],
        balance=user["balance"],
        created_at=user["created_at"],
        first_topup_at=user["first_topup_at"],
    )


def _reject(error):
    """Turn a store error into the status this API promises for it."""
    status = {
        "username_invalid": 400,
        "password_too_short": 400,
        "username_taken": 409,
        "bad_credentials": 401,
    }.get(error.code, 500)
    raise HTTPException(
        status_code=status, detail={"code": error.code, "message": error.message}
    ) from error


def _client_ip(request):
    """The address to rate limit on.

    The deployment sits behind nginx, which sets X-Real-IP to the peer it saw
    and overwrites whatever arrived, so it is the one header a caller cannot
    forge. The socket address is the fallback for a direct connection (as in
    the tests).
    """
    forwarded = (request.headers.get("x-real-ip") or "").strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def _too_many(retry_after):
    raise HTTPException(
        status_code=429,
        detail={
            "code": "too_many_attempts",
            "message": "too many attempts; wait a moment and try again",
        },
        headers={"Retry-After": str(max(1, retry_after))},
    )


def _check_rate(name, key, limit, window):
    if not ratelimit.allow(name, key, limit, window):
        _too_many(ratelimit.retry_after(name, key, limit, window))


def require_user(authorization: str = Header(default="")):
    """The account behind the bearer token, or a 401."""
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail={"code": "missing_token", "message": "sign in first"},
        )
    user = store.user_for_token(token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unknown_token",
                "message": "this session is no longer valid",
            },
        )
    return user


@router.post("/v1/accounts/register", response_model=Session)
def register(credentials: Credentials, request: Request):
    """Create an account. New accounts start with no credits at all."""
    _check_rate(
        "register", _client_ip(request), *config.register_rate_limit()
    )
    try:
        user = store.create_user(credentials.username, credentials.password)
    except store.StoreError as error:
        _reject(error)
    return Session(token=store.issue_token(user["id"]), account=_account(user))


@router.post("/v1/accounts/login", response_model=Session)
def login(credentials: Credentials, request: Request):
    limit, window = config.login_rate_limit()
    _check_rate("login-address", _client_ip(request), limit, window)
    account_key = (credentials.username or "").strip().lower()
    if account_key:
        _check_rate("login-account", account_key, limit, window)
    try:
        user = store.verify_login(credentials.username, credentials.password)
    except store.StoreError as error:
        _reject(error)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "bad_credentials",
                "message": "wrong username or password",
            },
        )
    return Session(token=store.issue_token(user["id"]), account=_account(user))


@router.post("/v1/accounts/logout")
def logout(authorization: str = Header(default="")):
    """Drop the session this request used. Logging out twice is fine."""
    _, _, token = (authorization or "").partition(" ")
    store.revoke_token(token.strip())
    return {"status": "ok"}


@router.get("/v1/accounts/me", response_model=Account)
def me(user=Depends(require_user)):
    """The balance, read from the ledger rather than remembered by a client."""
    return _account(user)


@router.get("/v1/accounts/ledger", response_model=list[LedgerEntry])
def ledger(user=Depends(require_user), limit: int = 20):
    """Recent movements, newest first, for the user's own eyes."""
    limit = max(1, min(int(limit), 200))
    return [
        LedgerEntry(
            delta=row["delta"],
            balance_after=row["balance_after"],
            reason=row["reason"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            price_version=row["price_version"],
            created_at=row["created_at"],
        )
        for row in store.ledger_for(user["id"], limit)
    ]
