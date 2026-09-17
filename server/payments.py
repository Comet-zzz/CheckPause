"""Buying credits with Alipay.

The shape of the flow, and why each piece is here:

1. The client asks for an order. The price comes from this server's own pack
   list, never from anything the client says, so nobody can buy 1000 credits
   for one cent.
2. The buyer opens ``/pay/{order_id}`` in a browser. That page carries the form
   Alipay's SDK signed, and submits itself - which is why the desktop app never
   has to be a web application to use a web payment product.
3. Alipay reports the payment, either by posting to ``/v1/pay/notify`` or, when
   no public HTTPS address exists yet, by answering the status endpoint with a
   trade query. Both routes end in ``mark_order_paid``, so whichever arrives
   first credits the account and the other changes nothing.
4. Credits land in the ledger, where every movement is already recorded.
"""

import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

from server import accounts, alipay, config, pricing, store

log = logging.getLogger("checkpause.payments")

router = APIRouter(tags=["payments"])

PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  html, body {{ height: 100%; margin: 0; }}
  body {{ display: flex; align-items: center; justify-content: center;
         background: #f5f6f8; color: #2c2c2c;
         font-family: system-ui, "Segoe UI", "Microsoft YaHei", sans-serif; }}
  .card {{ background: #fff; padding: 32px 40px; border-radius: 12px;
          box-shadow: 0 2px 16px rgba(0, 0, 0, .08); text-align: center;
          max-width: 420px; }}
  h1 {{ font-size: 18px; margin: 0 0 12px; }}
  p {{ font-size: 14px; line-height: 1.6; margin: 8px 0; color: #555; }}
  .amount {{ font-size: 28px; font-weight: 600; color: #1677ff; margin: 16px 0; }}
  .btn {{ margin-top: 18px; padding: 12px 30px; border: 0; border-radius: 8px;
         background: #1677ff; color: #fff; font-size: 16px; cursor: pointer; }}
  .btn:hover {{ background: #0f62e0; }}
  .note {{ color: #6b7280; font-size: 13px; }}
</style>
</head>
<body>
<div class="card">
<h1>{title}</h1>
{body}
</div>
{form}
</body>
</html>
"""

WAITING = """
<p>请确认下面的金额，然后点击按钮前往支付宝付款。</p>
"""

# Shown only while the sandbox gateway is in use. Its cashier draws a QR code
# that the real Alipay app cannot read - only the sandbox build can - which
# otherwise looks like a broken page and wastes an afternoon.
SANDBOX_HINT = """
<p style="color:#b45309">沙箱测试环境：请选「登录支付」输入沙箱买家账号，
或者用沙箱版支付宝 APP 扫码。<b>手机上真正的支付宝扫不了这个码</b>，
那是沙箱的限制，不是页面坏了。</p>
"""

PAID = """
<p class="amount">{credits} CP积分</p>
<p>已到账，可以回到 CheckPause 继续使用了。</p>
"""


class Pack(BaseModel):
    yuan: int
    credits: int


class OrderRequest(BaseModel):
    yuan: int


class OrderReply(BaseModel):
    order_id: str
    yuan: int
    credits: int
    pay_url: str
    status: str


class OrderStatus(BaseModel):
    order_id: str
    status: str
    yuan: float
    credits: int
    balance: int


def _page(title, body, form=""):
    return HTMLResponse(PAGE.format(title=title, body=body, form=form))


def _using_sandbox():
    """Whether the payment gateway is the test one, which changes what works."""
    return "sandbox" in config.alipay_settings()["gateway"].lower()


def _sandbox_hint():
    """The sandbox note, but only when this deployment asks for it.

    It explains why the sandbox QR code cannot be scanned, which is useful
    while testing and misleading anywhere else. In particular it must not end
    up in a screenshot sent to a reviewer, which is exactly where it was first
    seen.
    """
    if not config.sandbox_hint_enabled():
        return ""
    return SANDBOX_HINT if _using_sandbox() else ""


def _same_amount(cents, text):
    """Compare money as text, never as floats.

    ``total_amount`` arrives as a string like "10.00", "10" or "10.5", and
    comparing it as a float would be both lossy and a way to be talked out of a
    matching order.
    """
    match = re.fullmatch(r"(\d+)(?:\.(\d{1,2}))?", str(text or "").strip())
    if not match:
        return False
    fraction = (match.group(2) or "").ljust(2, "0")
    return int(match.group(1)) * 100 + int(fraction) == int(cents)


def _describe(order, params):
    """Whether a notification really describes this order and this app."""
    settings = config.alipay_settings()
    if params.get("app_id") != settings["app_id"]:
        return False
    if params.get("out_trade_no") != order["id"]:
        return False
    if not _same_amount(order["amount_cents"], params.get("total_amount")):
        return False
    # Only checked when it is configured: without it, app_id is still doing the
    # work of keeping a stranger's notification out.
    seller_id = settings["seller_id"]
    if seller_id and params.get("seller_id") != seller_id:
        return False
    return True


def _credit(order, trade_no="", notify_id=""):
    """Put the credits in the ledger, idempotently."""
    return store.mark_order_paid(
        order["id"],
        trade_no=trade_no,
        notify_id=notify_id,
        bonus_percent=config.first_topup_bonus_percent(),
        price_version=pricing.PRICE_VERSION,
    )


def _confirm_with_gateway(order):
    """Ask Alipay about an unpaid order, and credit it if the money moved.

    This is the fallback the notification contract requires, and it is what
    makes purchases arrive with no notification address configured at all.
    """
    if order["status"] == "paid" or not config.alipay_settings()["enabled"]:
        return order

    try:
        payload = alipay.query_trade(order["id"])
    except alipay.AlipayError:
        return order

    if not (
        alipay.trade_is_paid(payload)
        and _same_amount(order["amount_cents"], payload.get("total_amount"))
    ):
        return order

    try:
        confirmed = _credit(order, trade_no=payload.get("trade_no", ""))
    except store.StoreError:
        log.exception("could not credit order %s", order["id"])
        return order
    log.info("order %s confirmed by trade query", order["id"])
    return confirmed


@router.get("/v1/pay/packs", response_model=list[Pack])
def packs():
    """What a buyer may choose from."""
    return [
        Pack(yuan=yuan, credits=yuan * config.CREDITS_PER_YUAN)
        for yuan in config.topup_packs()
    ]


@router.post("/v1/pay/orders", response_model=OrderReply)
def create_order(
    request: Request,
    body: OrderRequest,
    user=Depends(accounts.require_user),
):
    """Open an order and hand back the page the browser should open."""
    if not config.alipay_settings()["enabled"]:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "payments_unavailable",
                "message": "this server cannot take payments yet",
            },
        )
    if body.yuan not in config.topup_packs():
        raise HTTPException(
            status_code=400,
            detail={"code": "unknown_pack", "message": "no such pack"},
        )

    order = store.create_order(
        user["id"], body.yuan * config.CREDITS_PER_YUAN, body.yuan * 100
    )
    return OrderReply(
        order_id=order["id"],
        yuan=body.yuan,
        credits=order["credits"],
        pay_url="{}/pay/{}".format(
            str(request.base_url).rstrip("/"), order["id"]
        ),
        status=order["status"],
    )


@router.get("/pay/{order_id}", response_class=HTMLResponse)
def pay_page(order_id: str):
    """The page the buyer's browser lands on.

    The order id is random rather than sequential, so it is not guessable; it
    is the only thing protecting this page, which is why it is never shown
    anywhere but to the buyer who asked for it.
    """
    order = store.order(order_id)
    if order is None:
        return _page("订单不存在", "<p>这个付款链接无效。</p>")

    # Coming back from the cashier lands here, so ask Alipay rather than
    # showing a form again to somebody who has already paid.
    order = _confirm_with_gateway(order)

    if order["status"] == "paid":
        return _page(
            "已支付", PAID.format(credits=order["credits"])
        )

    if not config.alipay_settings()["enabled"]:
        return _page("暂时无法支付", "<p>服务器还没有配置收款。</p>")

    try:
        form = alipay.payment_form(
            order["id"], "{:.2f}".format(order["amount_cents"] / 100)
        )
    except alipay.AlipayError:
        log.exception("could not build a payment form for %s", order_id)
        return _page("暂时无法支付", "<p>生成付款页面失败，请稍后再试。</p>")

    # Alipay's form submits itself the moment the page loads. That is right for
    # a bare redirect, but their onboarding asks for a payment page that shows
    # the Alipay option and waits - and a page that vanishes cannot be looked
    # at, or screenshotted. Removing the automatic submit leaves the same form,
    # submitted by a button instead of by arriving.
    form = form.replace("document.forms[0].submit();", "")

    return _page(
        "CheckPause 充值",
        '<p class="amount">¥{:.2f}</p>'.format(
            order["amount_cents"] / 100
        )
        + "<p>{} CP积分</p>".format(order["credits"])
        + WAITING
        + _sandbox_hint()
        + '<button type="button" class="btn" '
        'onclick="document.forms[0].submit()">用支付宝付款</button>'
        '<p class="note">点击后会跳转到支付宝，可用手机扫码或登录付款。'
        "付款完成后回到 CheckPause，余额会自动到账。</p>",
        form,
    )


@router.post("/v1/pay/notify")
async def notify(request: Request):
    """Alipay's asynchronous notification.

    A form post, not JSON - and every answer is plain text, because that is
    what the sender reads. ``success`` means "stop retrying"; anything else
    means it will try again.
    """
    try:
        form = await request.form()
    except Exception:
        log.warning("a payment notification was not a readable form post")
        return PlainTextResponse("fail")

    params = {key: str(value) for key, value in form.items()}

    if alipay.verified_notification(params) is None:
        # Never log the signature itself, and never act on the rest.
        log.warning(
            "rejected an unverified payment notification for order %s",
            params.get("out_trade_no", "?"),
        )
        return PlainTextResponse("fail")

    order = store.order(params.get("out_trade_no", ""))
    if order is None or not _describe(order, params):
        log.warning(
            "a verified payment notification did not match any order: %s",
            params.get("out_trade_no", "?"),
        )
        return PlainTextResponse("fail")

    if alipay.notification_is_paid(params):
        try:
            _credit(
                order,
                trade_no=params.get("trade_no", ""),
                notify_id=params.get("notify_id", ""),
            )
        except store.StoreError:
            log.exception("could not credit order %s", order["id"])
            return PlainTextResponse("fail")
        log.info("order %s paid", order["id"])
    else:
        # A refund, a closure or a split. Acknowledged so it stops being
        # retried, but it must never mark an order paid.
        log.info(
            "order %s got a non-payment notification: %s",
            order["id"],
            params.get("trade_status"),
        )

    return PlainTextResponse("success")


@router.get("/v1/pay/orders/{order_id}", response_model=OrderStatus)
def order_status(order_id: str, user=Depends(accounts.require_user)):
    """What became of an order, asking Alipay when nobody has told us.

    The trade query is the source of truth the official contract insists on,
    and it is also what lets this work with no notification address at all.
    """
    order = store.order(order_id)
    if order is None or order["user_id"] != user["id"]:
        raise HTTPException(
            status_code=404,
            detail={"code": "no_such_order", "message": "no such order"},
        )

    order = _confirm_with_gateway(order)

    return OrderStatus(
        order_id=order["id"],
        status=order["status"],
        yuan=order["amount_cents"] / 100,
        credits=order["credits"],
        balance=store.balance_of(user["id"]),
    )
