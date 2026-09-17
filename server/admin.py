"""Admin commands, run on the server as the service account.

    cd /srv/checkpause
    .venv/bin/python -m server.admin users
    .venv/bin/python -m server.admin show <username>
    .venv/bin/python -m server.admin add-credits <username> 1000 --note "wechat"
    .venv/bin/python -m server.admin grant <username> 100 --note "apology"
    .venv/bin/python -m server.admin set-password <username>
    .venv/bin/python -m server.admin sweep

``add-credits`` records a purchase, so the first one on an account also earns
the first-purchase bonus. ``grant`` never does: it is for gifts, apologies and
corrections, where no money changed hands.

There is deliberately no HTTP admin endpoint. Reaching this requires a shell on
the server, which is a much smaller thing to protect than a URL.
"""

import argparse
import getpass
import sys
from datetime import datetime, timezone

from server import config, store

REASONS = {
    "topup": "purchase",
    "topup_bonus": "first-purchase bonus",
    "grant": "granted by admin",
    "adjustment": "correction",
    "analyze": "analysis",
    "analyze_interrupted": "analysis (interrupted)",
}


def _who(username):
    user = store.find_user(username)
    if user is None:
        sys.exit("no account called {!r}".format(username))
    return user


def _stamp():
    return datetime.now(timezone.utc).strftime("manual-%Y%m%dT%H%M%SZ")


def cmd_users(_args):
    users = store.list_users()
    if not users:
        print("no accounts yet")
        return
    print("{:<24} {:>10}  {:<20}  {}".format(
        "USERNAME", "BALANCE", "CREATED", "FIRST PURCHASE"
    ))
    for user in users:
        print("{:<24} {:>10}  {:<20}  {}".format(
            user["username"],
            user["balance"],
            user["created_at"][:19],
            (user["first_topup_at"] or "-")[:19],
        ))


def cmd_show(args):
    user = _who(args.username)
    print("account   {}".format(user["username"]))
    print("balance   {} credits".format(user["balance"]))
    print("created   {}".format(user["created_at"][:19]))
    print("first buy {}".format((user["first_topup_at"] or "never")[:19]))
    rows = store.ledger_for(user["id"], args.limit)
    if not rows:
        print("\nno movements yet")
        return
    print("\n{:>8}  {:>8}  {:<20}  {:<22}  {}".format(
        "CHANGE", "BALANCE", "REASON", "TOKENS IN/OUT", "WHEN"
    ))
    for row in rows:
        tokens = "-"
        if row["input_tokens"] or row["output_tokens"]:
            tokens = "{}/{}".format(row["input_tokens"], row["output_tokens"])
        print("{:>+8}  {:>8}  {:<20}  {:<22}  {}".format(
            row["delta"],
            row["balance_after"],
            REASONS.get(row["reason"], row["reason"]),
            tokens,
            row["created_at"][:19],
        ))


def cmd_add_credits(args):
    user = _who(args.username)
    reference = args.reference or _stamp()
    try:
        added = store.top_up(
            user["id"],
            args.credits,
            reference=reference,
            note=args.note,
            bonus_percent=config.first_topup_bonus_percent(),
            price_version="manual",
        )
    except store.StoreError as error:
        sys.exit("{}: {}".format(error.code, error.message))
    bonus = added - args.credits
    print("{} bought {} credits".format(user["username"], args.credits))
    if bonus:
        print("  first purchase bonus  +{}".format(bonus))
    print("  reference             {}".format(reference))
    print("  new balance           {}".format(store.balance_of(user["id"])))


def cmd_grant(args):
    user = _who(args.username)
    try:
        store.add_credits(
            user["id"],
            args.credits,
            reason="grant",
            reference=args.reference or _stamp(),
            note=args.note,
        )
    except store.StoreError as error:
        sys.exit("{}: {}".format(error.code, error.message))
    print("{} granted {} credits".format(user["username"], args.credits))
    print("  new balance           {}".format(store.balance_of(user["id"])))


def cmd_set_password(args):
    user = _who(args.username)
    password = args.password or getpass.getpass("new password: ")
    if not args.password:
        again = getpass.getpass("repeat: ")
        if password != again:
            sys.exit("the two passwords differ")
    try:
        store.set_password(user["id"], password)
    except store.StoreError as error:
        sys.exit("{}: {}".format(error.code, error.message))
    print("password changed for {}; every session was signed out".format(
        user["username"]
    ))


def cmd_rename(args):
    user = _who(args.username)
    try:
        store.set_username(user["id"], args.new_username)
    except store.StoreError as error:
        sys.exit("{}: {}".format(error.code, error.message))
    print("{} is now {}".format(user["username"], args.new_username.strip()))
    print("  balance unchanged     {}".format(store.balance_of(user["id"])))
    print("  sessions stay signed in (they follow the account, not the name)")


def cmd_sweep(_args):
    swept = store.sweep_stale_holds()
    if not swept:
        print("no abandoned reservations")
        return
    for item in swept:
        print("charged {} credits, balance now {}".format(
            item["charge"], item["balance"]
        ))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m server.admin",
        description="CheckPause account and credit administration.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("users", help="list accounts").set_defaults(
        run=cmd_users
    )

    show = sub.add_parser("show", help="one account and its recent ledger")
    show.add_argument("username")
    show.add_argument("--limit", type=int, default=20)
    show.set_defaults(run=cmd_show)

    buy = sub.add_parser(
        "add-credits", help="record a purchase (earns the first-buy bonus)"
    )
    buy.add_argument("username")
    buy.add_argument("credits", type=int)
    buy.add_argument("--note", default="")
    buy.add_argument(
        "--reference",
        default="",
        help="reuse one to make a repeat run fail instead of double-crediting",
    )
    buy.set_defaults(run=cmd_add_credits)

    grant = sub.add_parser("grant", help="give credits without a purchase")
    grant.add_argument("username")
    grant.add_argument("credits", type=int)
    grant.add_argument("--note", default="")
    grant.add_argument("--reference", default="")
    grant.set_defaults(run=cmd_grant)

    password = sub.add_parser("set-password", help="reset a forgotten password")
    password.add_argument("username")
    password.add_argument("password", nargs="?", default="")
    password.set_defaults(run=cmd_set_password)

    rename = sub.add_parser(
        "rename-user", help="fix a username somebody mistyped"
    )
    rename.add_argument("username")
    rename.add_argument("new_username")
    rename.set_defaults(run=cmd_rename)

    sub.add_parser(
        "sweep", help="charge reservations abandoned by a crash"
    ).set_defaults(run=cmd_sweep)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
