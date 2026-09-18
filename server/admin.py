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
from decimal import Decimal, InvalidOperation

from server import alipay, config, store

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


def cmd_open_order(args):
    """Make a payment link to hand to a buyer.

    This is the whole sales flow before the client grows a top-up button: ask
    the buyer for their username, run this, send them the link. The credits
    arrive by themselves once they pay, because Alipay either notifies the
    server or the server asks Alipay.
    """
    user = _who(args.username)
    yuan = int(args.yuan)
    packs = config.topup_packs()
    if yuan not in packs:
        sys.exit(
            "{} is not one of the packs ({}). Use one of those, or change "
            "CHECKPAUSE_TOPUP_PACKS.".format(
                yuan, ", ".join(str(pack) for pack in packs)
            )
        )

    order = store.create_order(
        user["id"], yuan * config.CREDITS_PER_YUAN, yuan * 100
    )
    print(
        "{} buys {} CP credits for CNY {}".format(
            user["username"], order["credits"], yuan
        )
    )
    print()
    print("  {}/pay/{}".format(config.public_url().rstrip("/"), order["id"]))
    print()
    print("Send them that link. Once they pay, check it landed with:")
    print("  .venv/bin/python -m server.admin show {}".format(user["username"]))


def cmd_sweep(_args):
    swept = store.sweep_stale_holds()
    if not swept:
        print("no abandoned reservations")
        return
    for item in swept:
        print("charged {} credits, balance now {}".format(
            item["charge"], item["balance"]
        ))


def _order(order_id):
    order = store.order(order_id)
    if order is None:
        sys.exit("no order with id {!r}".format(order_id))
    return order


def _yuan_to_cents(text):
    try:
        amount = Decimal(str(text))
    except InvalidOperation:
        sys.exit("not an amount: {!r}".format(text))
    if amount <= 0:
        sys.exit("the amount must be positive")
    cents = int((amount * 100).to_integral_value())
    if Decimal(cents) != amount * 100:
        sys.exit("at most two decimal places")
    return cents


def _gateway_or_exit():
    if not config.alipay_settings()["enabled"]:
        sys.exit("alipay is not configured on this server")


def cmd_refund(args):
    """Send a buyer their money back for a paid order.

    The refund row is written before the call, so a timeout leaves a record to
    reconcile instead of an unnoticed refund. A retry must reuse the same
    ``--out-request-no``; that is what keeps it from becoming a second refund.
    """
    _gateway_or_exit()
    order = _order(args.order_id)
    cents = _yuan_to_cents(args.yuan)
    try:
        record = store.open_refund(
            order["id"], cents, out_request_no=args.out_request_no or None,
            note=args.reason,
        )
    except store.StoreError as error:
        sys.exit("{}: {}".format(error.code, error.message))

    try:
        payload = alipay.refund(
            order["id"],
            "{:.2f}".format(cents / 100),
            record["out_request_no"],
            args.reason,
        )
    except alipay.AlipayError as error:
        sys.exit("gateway refused: {}".format(error))

    if alipay.refund_changed_funds(payload):
        store.settle_refund(
            record["out_request_no"], "success", payload.get("trade_no", "")
        )
        print("refunded CNY {:.2f} for {}".format(cents / 100, order["id"]))
    elif alipay.refund_accepted(payload):
        store.settle_refund(
            record["out_request_no"], "pending", payload.get("trade_no", "")
        )
        print("refund accepted but not confirmed; check it with:")
        print("  .venv/bin/python -m server.admin refund-status {} {}".format(
            order["id"], record["out_request_no"]
        ))
    else:
        store.settle_refund(record["out_request_no"], "failed")
        sys.exit("refund not accepted: {} - {}".format(
            payload.get("sub_code"), payload.get("sub_msg")
        ))
    print("  request no            {}".format(record["out_request_no"]))


def cmd_refund_status(args):
    _gateway_or_exit()
    order = _order(args.order_id)
    record = store.refund(args.out_request_no)
    if record is None or record["order_id"] != order["id"]:
        sys.exit("no such refund on that order")
    try:
        payload = alipay.query_refund(order["id"], args.out_request_no)
    except alipay.AlipayError as error:
        sys.exit("gateway refused: {}".format(error))

    if alipay.refund_is_complete(payload):
        store.settle_refund(
            args.out_request_no, "success", payload.get("trade_no", "")
        )
        print("refund complete: CNY {}".format(
            payload.get("refund_amount", "?")
        ))
        return
    print("refund status: {}".format(payload.get("refund_status") or "unknown"))
    print("  keep this request no  {}".format(args.out_request_no))


def cmd_close_order(args):
    _gateway_or_exit()
    order = _order(args.order_id)
    if order["status"] == "paid":
        sys.exit("a paid order cannot be closed")
    try:
        payload = alipay.close_trade(order["id"])
    except alipay.AlipayError as error:
        sys.exit("gateway refused: {}".format(error))
    if not alipay.close_succeeded(payload):
        sys.exit("close not accepted: {} - {}".format(
            payload.get("sub_code"), payload.get("sub_msg")
        ))
    closed = store.close_order(order["id"])
    print("{} is now {}".format(closed["id"], closed["status"]))


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

    open_order = sub.add_parser(
        "open-order", help="make a payment link to hand to a buyer"
    )
    open_order.add_argument("username")
    open_order.add_argument("yuan", type=int)
    open_order.set_defaults(run=cmd_open_order)

    sub.add_parser(
        "sweep", help="charge reservations abandoned by a crash"
    ).set_defaults(run=cmd_sweep)

    refund = sub.add_parser(
        "refund", help="send a buyer their money back for a paid order"
    )
    refund.add_argument("order_id")
    refund.add_argument("yuan")
    refund.add_argument("--reason", default="")
    refund.add_argument(
        "--out-request-no",
        default="",
        help="reuse to retry the same refund instead of making a new one",
    )
    refund.set_defaults(run=cmd_refund)

    refund_status = sub.add_parser(
        "refund-status", help="confirm a refund the gateway did not settle"
    )
    refund_status.add_argument("order_id")
    refund_status.add_argument("out_request_no")
    refund_status.set_defaults(run=cmd_refund_status)

    close_order = sub.add_parser(
        "close-order", help="close an order the buyer never paid"
    )
    close_order.add_argument("order_id")
    close_order.set_defaults(run=cmd_close_order)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.run(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
