"""Accounts, credits and the ledger, kept in SQLite on the server.

All the money lives here so the endpoint stays readable: it reserves credits
before calling the model, then settles the reservation afterwards.

Two invariants are enforced by the schema rather than by discipline:

* ``users.balance`` can never go negative. The CHECK constraint plus the
  ``WHERE balance >= ?`` in :func:`open_hold` mean two concurrent requests
  cannot spend the same credits twice.
* Every change to a balance has a ledger row recording the balance it produced
  and the price table that was in force, so a receipt can always be explained.

Reservations are deliberately *not* ledger rows. A request writes exactly one
row when it finishes, whether it finished cleanly or was cut off mid-stream, so
one exchange is always one line in the history.

``CHECKPAUSE_DB`` overrides the database location, which is how the tests point
the code at a temporary file.
"""

import hashlib
import hmac
import os
import pathlib
import re
import secrets
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

DEFAULT_DB_PATH = "/var/lib/checkpause/checkpause.db"

USERNAME_PATTERN = re.compile(r"^[\w.-]{3,32}$")
MIN_PASSWORD_LENGTH = 6
TOKEN_BYTES = 32

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash  TEXT    NOT NULL,
    balance        INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT    NOT NULL,
    first_topup_at TEXT
);

CREATE TABLE IF NOT EXISTS tokens (
    token        TEXT PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TEXT NOT NULL,
    last_seen_at TEXT
);

-- Credits taken out of a balance while a request runs, so the same credits
-- cannot be reserved twice. Closed by settle_hold or refund_hold.
CREATE TABLE IF NOT EXISTS holds (
    id         TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount     INTEGER NOT NULL CHECK (amount >= 0),
    note       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    settled_at TEXT
);

CREATE TABLE IF NOT EXISTS ledger (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delta         INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    reason        TEXT    NOT NULL,
    reference     TEXT    NOT NULL DEFAULT '',
    price_version TEXT    NOT NULL DEFAULT '',
    input_tokens  INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    note          TEXT    NOT NULL DEFAULT '',
    created_at    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS ledger_by_user ON ledger(user_id, id);

-- A reference may not be credited twice, which is what makes a retried top-up
-- or a replayed payment notification safe to process.
CREATE UNIQUE INDEX IF NOT EXISTS ledger_once ON ledger(reference, reason)
    WHERE reference <> '';

-- One row per attempt to buy credits. The id is what the buyer pays against,
-- so it doubles as the out_trade_no Alipay sees.
CREATE TABLE IF NOT EXISTS orders (
    id           TEXT PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credits      INTEGER NOT NULL CHECK (credits > 0),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    status       TEXT    NOT NULL DEFAULT 'created',
    trade_no     TEXT    NOT NULL DEFAULT '',
    notify_id    TEXT    NOT NULL DEFAULT '',
    created_at   TEXT    NOT NULL,
    paid_at      TEXT
);

CREATE INDEX IF NOT EXISTS orders_by_user ON orders(user_id, id);

-- One row per refund attempt. ``out_request_no`` is the id the gateway sees
-- and the key that makes asking twice safe: a retry reuses it and the gateway
-- answers with the original result instead of refunding twice.
CREATE TABLE IF NOT EXISTS refunds (
    out_request_no TEXT PRIMARY KEY,
    order_id       TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    amount_cents   INTEGER NOT NULL CHECK (amount_cents > 0),
    status         TEXT NOT NULL DEFAULT 'pending',
    trade_no       TEXT NOT NULL DEFAULT '',
    note           TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL,
    updated_at     TEXT
);

CREATE INDEX IF NOT EXISTS refunds_by_order ON refunds(order_id, created_at);
"""


class StoreError(RuntimeError):
    """Something the API should report rather than turn into a 500."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class NoCredits(StoreError):
    """The balance does not cover the reservation."""

    def __init__(self, balance, needed):
        super().__init__(
            "no_credits", "the balance does not cover this request"
        )
        self.balance = balance
        self.needed = needed


_lock = threading.RLock()
_connection = None
_connection_path = None


def db_path():
    override = os.environ.get("CHECKPAUSE_DB", "").strip()
    return pathlib.Path(override or DEFAULT_DB_PATH)


def connection():
    """The one connection, reopened if the configured path has changed."""
    global _connection, _connection_path
    path = db_path()
    if _connection is not None and _connection_path == path:
        return _connection
    if _connection is not None:
        _connection.close()
        _connection = None
    path.parent.mkdir(parents=True, exist_ok=True)
    fresh = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    fresh.row_factory = sqlite3.Row
    fresh.execute("PRAGMA journal_mode=WAL")
    fresh.execute("PRAGMA foreign_keys=ON")
    fresh.execute("PRAGMA busy_timeout=5000")
    fresh.executescript(SCHEMA)
    _connection = fresh
    _connection_path = path
    return fresh


def close():
    """Drop the connection; the next call opens a fresh one."""
    global _connection, _connection_path
    with _lock:
        if _connection is not None:
            _connection.close()
        _connection = None
        _connection_path = None


@contextmanager
def transaction():
    """Serialise writers and make each change all-or-nothing."""
    with _lock:
        conn = connection()
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
        except Exception:
            conn.execute("ROLLBACK")
            raise
        conn.execute("COMMIT")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- passwords -------------------------------------------------------------


def _hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
    )
    return "scrypt${}${}${}${}${}".format(
        2**14, 8, 1, salt.hex(), digest.hex()
    )


def _verify_password(password, stored):
    try:
        scheme, n, r, p, salt, digest = (stored or "").split("$")
        if scheme != "scrypt":
            return False
        expected = bytes.fromhex(digest)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (AttributeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)


# --- users -----------------------------------------------------------------


def _user(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "balance": row["balance"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "first_topup_at": row["first_topup_at"],
    }


def _clean_username(username):
    username = (username or "").strip()
    if not USERNAME_PATTERN.match(username):
        raise StoreError(
            "username_invalid",
            "use 3-32 letters, digits, underscores, dots or dashes",
        )
    return username


def create_user(username, password):
    """Register an account. Raises StoreError if the name is taken."""
    username = _clean_username(username)
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise StoreError(
            "password_too_short",
            "the password needs at least {} characters".format(
                MIN_PASSWORD_LENGTH
            ),
        )
    with transaction() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, created_at)"
                " VALUES (?, ?, ?)",
                (username, _hash_password(password), _now()),
            )
        except sqlite3.IntegrityError as error:
            raise StoreError(
                "username_taken", "that username is already registered"
            ) from error
        return _user(
            conn.execute(
                "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        )


def set_username(user_id, username):
    """Change an account's login name.

    Nothing else moves: tokens, balances and history all hang off the user id,
    so a corrected name changes only what somebody types to sign in. That is
    also why this is a fix for a typo rather than anything to be nervous about.
    """
    username = _clean_username(username)
    with transaction() as conn:
        try:
            cursor = conn.execute(
                "UPDATE users SET username = ? WHERE id = ?",
                (username, user_id),
            )
        except sqlite3.IntegrityError as error:
            raise StoreError(
                "username_taken", "that username is already registered"
            ) from error
        if cursor.rowcount == 0:
            raise StoreError("no_such_user", "no user with that id")


def verify_login(username, password):
    """The user row when the credentials match, otherwise None."""
    with _lock:
        row = connection().execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
            ((username or "").strip(),),
        ).fetchone()
    if row is None or not row["is_active"]:
        # Hash anyway, so a missing account and a wrong password take about
        # the same time to answer.
        _verify_password(password or "", _hash_password("decoy"))
        return None
    if not _verify_password(password or "", row["password_hash"]):
        return None
    return _user(row)


def set_password(user_id, password):
    """Set a new password and drop every session, for admin recovery."""
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise StoreError(
            "password_too_short",
            "the password needs at least {} characters".format(
                MIN_PASSWORD_LENGTH
            ),
        )
    with transaction() as conn:
        cursor = conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_hash_password(password), user_id),
        )
        if cursor.rowcount == 0:
            raise StoreError("no_such_user", "no user with that id")
        conn.execute("DELETE FROM tokens WHERE user_id = ?", (user_id,))


def get_user(user_id):
    with _lock:
        row = connection().execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return _user(row)


def find_user(username):
    with _lock:
        row = connection().execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
            ((username or "").strip(),),
        ).fetchone()
    return _user(row)


def list_users():
    with _lock:
        rows = connection().execute(
            "SELECT * FROM users ORDER BY id"
        ).fetchall()
    return [_user(row) for row in rows]


# --- sessions --------------------------------------------------------------


def issue_token(user_id):
    token = secrets.token_urlsafe(TOKEN_BYTES)
    with transaction() as conn:
        conn.execute(
            "INSERT INTO tokens (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, _now()),
        )
    return token


def user_for_token(token):
    """The user behind a bearer token, or None. Touches last_seen_at."""
    token = (token or "").strip()
    if not token:
        return None
    with _lock:
        conn = connection()
        row = conn.execute(
            "SELECT * FROM users WHERE id ="
            " (SELECT user_id FROM tokens WHERE token = ?)",
            (token,),
        ).fetchone()
        if row is not None:
            conn.execute(
                "UPDATE tokens SET last_seen_at = ? WHERE token = ?",
                (_now(), token),
            )
    user = _user(row)
    if user is not None and not user["is_active"]:
        return None
    return user


def revoke_token(token):
    with transaction() as conn:
        conn.execute("DELETE FROM tokens WHERE token = ?", (token,))


# --- credits ---------------------------------------------------------------


def _move(conn, user_id, amount, reason, reference="", note="", **extra):
    """Change a balance and write the ledger row that explains it."""
    row = conn.execute(
        "SELECT balance FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        raise StoreError("no_such_user", "no user with that id")
    balance = row["balance"] + int(amount)
    if balance < 0:
        raise StoreError(
            "below_zero", "that would push the balance below zero"
        )
    conn.execute(
        "UPDATE users SET balance = ? WHERE id = ?", (balance, user_id)
    )
    try:
        conn.execute(
            "INSERT INTO ledger (user_id, delta, balance_after, reason,"
            " reference, price_version, input_tokens, output_tokens, note,"
            " created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                int(amount),
                balance,
                reason,
                reference,
                extra.get("price_version", ""),
                int(extra.get("input_tokens", 0)),
                int(extra.get("output_tokens", 0)),
                note,
                _now(),
            ),
        )
    except sqlite3.IntegrityError as error:
        raise StoreError(
            "duplicate_reference", "that reference was already credited"
        ) from error
    return balance


def balance_of(user_id):
    with _lock:
        row = connection().execute(
            "SELECT balance FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return row["balance"] if row else 0


def add_credits(user_id, amount, reason="grant", reference="", note=""):
    """Adjust a balance by hand: a gift, a refund or a correction."""
    amount = int(amount)
    if amount == 0:
        raise StoreError("bad_amount", "nothing to do for zero credits")
    with transaction() as conn:
        return _move(conn, user_id, amount, reason, reference, note)


def _credit_purchase(
    conn, user_id, credits, reference, note, bonus_percent, price_version
):
    """Credit a purchase, and once per account its first-purchase bonus."""
    row = conn.execute(
        "SELECT first_topup_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        raise StoreError("no_such_user", "no user with that id")
    first = row["first_topup_at"] is None

    _move(
        conn,
        user_id,
        credits,
        "topup",
        reference,
        note,
        price_version=price_version,
    )

    bonus = 0
    if first:
        if bonus_percent:
            bonus = credits * int(bonus_percent) // 100
            if bonus:
                _move(
                    conn,
                    user_id,
                    bonus,
                    "topup_bonus",
                    reference,
                    note,
                    price_version=price_version,
                )
        conn.execute(
            "UPDATE users SET first_topup_at = ? WHERE id = ?",
            (_now(), user_id),
        )
    return credits + bonus


def top_up(
    user_id, credits, reference="", note="", bonus_percent=0, price_version=""
):
    """Record a purchase made outside the payment gateway.

    Returns the total credits added, so the caller can show a receipt. A caller
    that has more than one way to be told about the same purchase can pass the
    same ``reference`` again and the second attempt will be refused rather than
    credited twice.
    """
    credits = int(credits)
    if credits <= 0:
        raise StoreError("bad_amount", "a top-up must be positive")
    with transaction() as conn:
        return _credit_purchase(
            conn,
            user_id,
            credits,
            reference,
            note,
            bonus_percent,
            price_version,
        )


# --- reservations ----------------------------------------------------------


def open_hold(user_id, amount, note="", hold_id=None):
    """Reserve credits for a request; raises NoCredits if they are not there.

    The UPDATE is the only place a balance is checked, so it is also the only
    place that needs to be atomic: it either takes the credits or matches no
    rows, and two requests can never both win.
    """
    amount = max(0, int(amount))
    hold_id = hold_id or uuid.uuid4().hex
    with transaction() as conn:
        cursor = conn.execute(
            "UPDATE users SET balance = balance - ?"
            " WHERE id = ? AND balance >= ?",
            (amount, user_id, amount),
        )
        if cursor.rowcount == 0:
            row = conn.execute(
                "SELECT balance FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if row is None:
                raise StoreError("no_such_user", "no user with that id")
            raise NoCredits(row["balance"], amount)
        conn.execute(
            "INSERT INTO holds (id, user_id, amount, note, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (hold_id, user_id, amount, note, _now()),
        )
    return hold_id


def refund_hold(hold_id, note=""):
    """Cancel a reservation untouched. Nothing was billed, so no ledger row."""
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM holds WHERE id = ? AND settled_at IS NULL",
            (hold_id,),
        ).fetchone()
        if row is None:
            return False
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE id = ?",
            (row["amount"], row["user_id"]),
        )
        conn.execute(
            "UPDATE holds SET settled_at = ?, note = ? WHERE id = ?",
            (_now(), note, hold_id),
        )
    return True


def settle_hold(
    hold_id,
    input_tokens=0,
    output_tokens=0,
    cost=None,
    price_version="",
    note="",
):
    """Close a reservation and write the one ledger row it produces.

    ``cost`` is what the exchange really cost in credits. A caller that never
    learned the upstream usage passes ``None``: the reservation then stands as
    the charge, so an interrupted reply is not given away for free.
    """
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM holds WHERE id = ? AND settled_at IS NULL",
            (hold_id,),
        ).fetchone()
        if row is None:
            raise StoreError("no_reservation", "no open reservation with that id")

        user_id = row["user_id"]
        reserved = row["amount"]
        balance = conn.execute(
            "SELECT balance FROM users WHERE id = ?", (user_id,)
        ).fetchone()["balance"]

        if cost is None:
            charge = reserved
            reason = "analyze_interrupted"
        else:
            charge = max(0, int(cost))
            reason = "analyze"

        if charge <= reserved:
            new_balance = balance + (reserved - charge)
        else:
            # An under-estimate is rare, and the shortfall is capped by what is
            # actually there: a user is never pushed into debt.
            new_balance = max(0, balance - (charge - reserved))
            charge = reserved + (balance - new_balance)

        conn.execute(
            "UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id)
        )
        conn.execute(
            "UPDATE holds SET settled_at = ?, note = ? WHERE id = ?",
            (_now(), note, hold_id),
        )
        conn.execute(
            "INSERT INTO ledger (user_id, delta, balance_after, reason,"
            " reference, price_version, input_tokens, output_tokens, note,"
            " created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                -charge,
                new_balance,
                reason,
                hold_id,
                price_version,
                int(input_tokens),
                int(output_tokens),
                note,
                _now(),
            ),
        )
        return {"charge": charge, "balance": new_balance, "reason": reason}


def sweep_stale_holds(older_than_seconds=900):
    """Charge for reservations whose request never came back.

    A crash mid-stream can leave a reservation that nothing will ever settle.
    Charging it, rather than deleting it, matches the rule for an interrupted
    reply: the upstream did the work, so it does not come free.
    """
    cutoff = (
        datetime.now(timezone.utc) - timedelta(seconds=older_than_seconds)
    ).isoformat(timespec="seconds")
    with _lock:
        rows = connection().execute(
            "SELECT id FROM holds WHERE settled_at IS NULL AND created_at < ?",
            (cutoff,),
        ).fetchall()
    swept = []
    for row in rows:
        try:
            swept.append(settle_hold(row["id"], note="abandoned"))
        except StoreError:
            continue
    return swept


# --- reporting -------------------------------------------------------------


def ledger_for(user_id, limit=20):
    with _lock:
        rows = connection().execute(
            "SELECT * FROM ledger WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, int(limit)),
        ).fetchall()
    return [dict(row) for row in rows]


# --- orders ----------------------------------------------------------------


def _order(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "credits": row["credits"],
        "amount_cents": row["amount_cents"],
        "status": row["status"],
        "trade_no": row["trade_no"],
        "created_at": row["created_at"],
        "paid_at": row["paid_at"],
    }


def create_order(user_id, credits, amount_cents):
    """Open an order. Its id is what the buyer pays against."""
    credits = int(credits)
    amount_cents = int(amount_cents)
    if credits <= 0 or amount_cents <= 0:
        raise StoreError("bad_amount", "an order needs a positive price")
    # Random rather than sequential: the id travels to Alipay and back, and it
    # is also the only thing protecting the payment page from being guessed.
    order_id = "CP" + secrets.token_hex(10).upper()
    with transaction() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            raise StoreError("no_such_user", "no user with that id")
        conn.execute(
            "INSERT INTO orders (id, user_id, credits, amount_cents,"
            " created_at) VALUES (?, ?, ?, ?, ?)",
            (order_id, user_id, credits, amount_cents, _now()),
        )
    return order(order_id)


def order(order_id):
    with _lock:
        row = connection().execute(
            "SELECT * FROM orders WHERE id = ?", ((order_id or "").strip(),)
        ).fetchone()
    return _order(row)


def orders_for_user(user_id, limit=20):
    with _lock:
        rows = connection().execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, int(limit)),
        ).fetchall()
    return [_order(row) for row in rows]


def mark_order_paid(
    order_id, trade_no="", notify_id="", bonus_percent=0, price_version=""
):
    """Credit the buyer for an order, exactly once.

    Safe to call again. An order already marked paid comes back untouched, and
    even without that check the ledger's unique index on the reference would
    refuse the second credit. So a retried notification, or a notification
    arriving alongside the query fallback, cannot pay a buyer twice.
    """
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if row is None:
            raise StoreError("no_such_order", "no order with that id")
        current = _order(row)
        if current["status"] == "paid":
            return current

        _credit_purchase(
            conn,
            current["user_id"],
            current["credits"],
            order_id,
            "alipay",
            bonus_percent,
            price_version,
        )
        conn.execute(
            "UPDATE orders SET status = 'paid', trade_no = ?, notify_id = ?,"
            " paid_at = ? WHERE id = ?",
            (trade_no, notify_id, _now(), order_id),
        )
        return _order(
            conn.execute(
                "SELECT * FROM orders WHERE id = ?", (order_id,)
            ).fetchone()
        )


def close_order(order_id):
    """Mark an unpaid order closed. A paid order may not be closed this way."""
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if row is None:
            raise StoreError("no_such_order", "no order with that id")
        current = _order(row)
        if current["status"] == "paid":
            raise StoreError(
                "order_paid", "a paid order cannot be closed"
            )
        if current["status"] != "closed":
            conn.execute(
                "UPDATE orders SET status = 'closed' WHERE id = ?", (order_id,)
            )
    return order(order_id)


# --- refunds ---------------------------------------------------------------


def _refund(row):
    if row is None:
        return None
    return {
        "out_request_no": row["out_request_no"],
        "order_id": row["order_id"],
        "amount_cents": row["amount_cents"],
        "status": row["status"],
        "trade_no": row["trade_no"],
        "note": row["note"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def refunded_cents(order_id):
    """How much of an order has already gone back for certain."""
    with _lock:
        row = connection().execute(
            "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM refunds"
            " WHERE order_id = ? AND status = 'success'",
            ((order_id or "").strip(),),
        ).fetchone()
    return int(row["total"])


def refunds_for_order(order_id):
    with _lock:
        rows = connection().execute(
            "SELECT * FROM refunds WHERE order_id = ? ORDER BY created_at",
            ((order_id or "").strip(),),
        ).fetchall()
    return [_refund(row) for row in rows]


def refund(out_request_no):
    with _lock:
        row = connection().execute(
            "SELECT * FROM refunds WHERE out_request_no = ?",
            ((out_request_no or "").strip(),),
        ).fetchone()
    return _refund(row)


def open_refund(order_id, amount_cents, out_request_no=None, note=""):
    """Register an intended refund before the gateway is asked.

    Writing the row first means a crash between the call and the answer leaves
    a record to reconcile against, rather than a refund nobody knows about.
    """
    order_id = (order_id or "").strip()
    amount_cents = int(amount_cents)
    if amount_cents <= 0:
        raise StoreError("bad_amount", "a refund must be positive")
    out_request_no = out_request_no or "RF" + secrets.token_hex(8).upper()

    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if row is None:
            raise StoreError("no_such_order", "no order with that id")
        current = _order(row)
        if current["status"] != "paid":
            raise StoreError(
                "order_not_paid", "only a paid order can be refunded"
            )
        already = conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM refunds"
            " WHERE order_id = ? AND status = 'success'",
            (order_id,),
        ).fetchone()["total"]
        if int(already) + amount_cents > current["amount_cents"]:
            raise StoreError(
                "refund_too_much",
                "the refunds would exceed what was paid",
            )
        existing = conn.execute(
            "SELECT 1 FROM refunds WHERE out_request_no = ?",
            (out_request_no,),
        ).fetchone()
        if existing is not None:
            raise StoreError(
                "duplicate_reference", "that refund id was already used"
            )
        conn.execute(
            "INSERT INTO refunds (out_request_no, order_id, amount_cents,"
            " note, created_at) VALUES (?, ?, ?, ?, ?)",
            (out_request_no, order_id, amount_cents, note, _now()),
        )
    return refund(out_request_no)


def settle_refund(out_request_no, status, trade_no=""):
    """Record what the gateway said about a refund. Safe to repeat."""
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM refunds WHERE out_request_no = ?",
            (out_request_no,),
        ).fetchone()
        if row is None:
            raise StoreError("no_such_refund", "no refund with that id")
        conn.execute(
            "UPDATE refunds SET status = ?, trade_no = ?, updated_at = ?"
            " WHERE out_request_no = ?",
            (status, trade_no, _now(), out_request_no),
        )
    return refund(out_request_no)
