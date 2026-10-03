"""Server configuration: the tuned prompt, the API key, and where they live.

Nothing sensitive is kept in this repository. The tuned prompt, the upstream
API key and the access token are read from a directory outside the checkout -
``/etc/checkpause`` by default - so they can never be committed, and so the
public copy of this code contains only placeholders.

``CHECKPAUSE_CONFIG_DIR`` overrides that location, which is how the tests point
the code at a temporary directory.
"""

import os
import pathlib

DEFAULT_CONFIG_DIR = "/etc/checkpause"

# Where the release installers and the version manifest are mirrored, as laid
# out by server/deploy/install.sh (nginx serves the same directory at /download/).
DEFAULT_DOWNLOAD_DIR = "/srv/downloads"

# Only used when the real prompt file is missing, so a fresh checkout still
# runs and so tests do not need one. Deliberately plain: the tuned prompt is
# what the paid tier is paying for, and it lives on the server.
FALLBACK_SYSTEM_PROMPT = (
    "You are a chess coach. Using the engine data you are given, explain the "
    "player's mistakes in plain, encouraging language."
)

FALLBACK_USER_TEMPLATE = """PGN:
{pgn}

Engine analysis:
{analysis}"""

# Answers are billed by the token, so one reply must not be able to cost an
# unbounded amount. The upstream default is far higher than a coaching answer
# needs; this cap is still comfortably above a normal one.
DEFAULT_MAX_ANSWER_TOKENS = 3000

# Share of a first purchase handed back as bonus credits. Ten percent of a
# CNY 10 top-up means 1100 credits for CNY 10. Zero switches the offer off.
DEFAULT_FIRST_TOPUP_BONUS_PERCENT = 10


def config_dir():
    override = os.environ.get("CHECKPAUSE_CONFIG_DIR", "").strip()
    return pathlib.Path(override or DEFAULT_CONFIG_DIR)


def downloads_dir():
    """Where release installers and the version manifest live."""
    override = os.environ.get("CHECKPAUSE_DOWNLOAD_DIR", "").strip()
    return pathlib.Path(override or DEFAULT_DOWNLOAD_DIR)


def _read(name):
    try:
        return (config_dir() / name).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def system_prompt():
    """The tuned coaching prompt, or the plain fallback."""
    return _read("system_prompt.txt") or FALLBACK_SYSTEM_PROMPT


def user_template():
    """The template that wraps the game and the engine numbers."""
    return _read("user_template.txt") or FALLBACK_USER_TEMPLATE


def using_placeholder_prompt():
    """True when no tuned prompt has been installed yet."""
    return not _read("system_prompt.txt")


def identity_policy():
    """Deployment-specific wording for the model-disclosure rule.

    Empty unless somebody wants different words from the built-in one in
    ``prompting``.
    """
    return _read("identity_policy.txt")


def api_key():
    """The upstream provider's key. Read from the server, never logged."""
    return os.environ.get("UPSTREAM_API_KEY", "").strip()


def base_url():
    """Where the upstream provider lives. Supplied by the deployment.

    There is no default on purpose: an unconfigured deployment must fail loudly
    rather than quietly send traffic somewhere unintended.
    """
    return os.environ.get("UPSTREAM_BASE_URL", "").strip()


def model():
    """Which model to ask for. Named by the deployment, not by the code."""
    return os.environ.get("UPSTREAM_MODEL", "").strip()


def _positive_int(name, default):
    try:
        value = int(os.environ.get(name, "").strip())
    except ValueError:
        return default
    return value if value > 0 else default


def max_answer_tokens():
    """Upper bound on one reply, so a request cannot cost without limit."""
    return _positive_int("CHECKPAUSE_MAX_ANSWER_TOKENS", DEFAULT_MAX_ANSWER_TOKENS)


def first_topup_bonus_percent():
    """Extra credits given on a first purchase, as a percentage."""
    try:
        return max(
            0,
            int(os.environ.get("CHECKPAUSE_FIRST_TOPUP_BONUS_PERCENT", "").strip()),
        )
    except ValueError:
        return DEFAULT_FIRST_TOPUP_BONUS_PERCENT


# --- sessions --------------------------------------------------------------

# How long a session survives without being used. Each request pushes the
# deadline forward, so a token in daily use keeps working while an idle one
# lapses. A month is long enough to feel like "no sign-in" and short enough
# that a leaked token is not a permanent key.
DEFAULT_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60


def token_ttl_seconds():
    """How long a sign-in lasts between uses."""
    return _positive_int("CHECKPAUSE_TOKEN_TTL_SECONDS", DEFAULT_TOKEN_TTL_SECONDS)


def confidentiality_policy():
    """Deployment wording for the rule against reciting the tuned prompt.

    Empty unless somebody wants different words from the one built into
    ``prompting``. Like the identity rule, it is kept out of the tuned prompt
    file so replacing that file cannot quietly drop it.
    """
    return _read("confidentiality_policy.txt")


# --- rate limits -----------------------------------------------------------

# Signing in runs scrypt, so an endpoint that answers as fast as it is asked is
# also a way to make the server spend real memory and CPU. These bounds cover
# both password guessing and that cost: per client address, and - for sign-in -
# per account, so guessing one name cannot be spread across many addresses.
DEFAULT_LOGIN_ATTEMPTS = 10
DEFAULT_LOGIN_WINDOW_SECONDS = 60
DEFAULT_REGISTER_ATTEMPTS = 10
DEFAULT_REGISTER_WINDOW_SECONDS = 3600


def login_rate_limit():
    """(attempts, window seconds) for sign-in, per address and per account."""
    return (
        _positive_int("CHECKPAUSE_LOGIN_ATTEMPTS", DEFAULT_LOGIN_ATTEMPTS),
        _positive_int("CHECKPAUSE_LOGIN_WINDOW_SECONDS", DEFAULT_LOGIN_WINDOW_SECONDS),
    )


def register_rate_limit():
    """(attempts, window seconds) for sign-up, per address."""
    return (
        _positive_int("CHECKPAUSE_REGISTER_ATTEMPTS", DEFAULT_REGISTER_ATTEMPTS),
        _positive_int(
            "CHECKPAUSE_REGISTER_WINDOW_SECONDS",
            DEFAULT_REGISTER_WINDOW_SECONDS,
        ),
    )


# --- payments --------------------------------------------------------------

DEFAULT_ALIPAY_GATEWAY = "https://openapi.alipay.com/gateway.do"

# CNY 10 buys 1000 credits, so one yuan is a hundred credits.
CREDITS_PER_YUAN = 100

# What a buyer may choose, in yuan. The price is looked up here rather than
# taken from the request, so a client cannot name its own amount. The tiers are
# deliberately impulse-sized: one yuan to try it, and two familiar steps above.
DEFAULT_TOPUP_PACKS = (1, 6, 18)


def topup_packs():
    """The amounts a buyer may pay, in yuan, cheapest first."""
    raw = os.environ.get("CHECKPAUSE_TOPUP_PACKS", "").strip()
    if not raw:
        return list(DEFAULT_TOPUP_PACKS)
    packs = []
    for piece in raw.split(","):
        try:
            amount = int(piece.strip())
        except ValueError:
            continue
        if amount > 0:
            packs.append(amount)
    return packs or list(DEFAULT_TOPUP_PACKS)


DEFAULT_PUBLIC_URL = "https://checkpause.com"


def public_url():
    """Where buyers reach this server, used to build payment links."""
    return os.environ.get("CHECKPAUSE_PUBLIC_URL", "").strip() or DEFAULT_PUBLIC_URL


def sandbox_hint_enabled():
    """Whether the payment page may explain the sandbox's unreadable QR code.

    Off by default. It is useful while testing the sandbox and wrong
    everywhere else - notably in a screenshot sent to a reviewer, which is how
    it was first noticed.
    """
    return os.environ.get("CHECKPAUSE_SANDBOX_HINT", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def alipay_settings():
    """Everything the payment gateway needs.

    ``private_key`` is the non-Java key: the official SDK example states that
    Python takes PKCS#1 and Java takes PKCS#8, and mixing them up fails every
    signature. Alipay's console labels the PKCS#1 one "非 JAVA 语言私钥", which
    is why it is read from ``AIPAY_PRIVATE_PKCS_KEY`` despite the name.
    """
    app_id = os.environ.get("AIPAY_APP_ID", "").strip()
    private_key = os.environ.get("AIPAY_PRIVATE_PKCS_KEY", "").strip()
    alipay_public_key = os.environ.get("AIPAY_ALIPAY_PUBLIC_KEY", "").strip()
    return {
        "app_id": app_id,
        "private_key": private_key,
        "alipay_public_key": alipay_public_key,
        "gateway": (os.environ.get("AIPAY_GATEWAY", "").strip() or DEFAULT_ALIPAY_GATEWAY),
        # Both may be empty. The notification contract allows omitting
        # notify_url when there is no public HTTPS address yet, provided the
        # trade query fallback is implemented - and it is.
        "notify_url": os.environ.get("AIPAY_NOTIFY_URL", "").strip(),
        # The synchronous return lands on a real GET route in this service.
        # Sync parameters are only a hint about where to look: the page asks
        # the gateway, so a forged return cannot pretend to be a payment.
        "return_url": (
            os.environ.get("AIPAY_RETURN_URL", "").strip()
            or public_url().rstrip("/") + "/v1/pay/return"
        ),
        # Checked against the notification so a stranger's app_id cannot be
        # used to pay into this account.
        "seller_id": os.environ.get("AIPAY_SELLER_ID", "").strip(),
        "enabled": bool(app_id and private_key and alipay_public_key),
    }
