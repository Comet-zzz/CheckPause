"""Alipay web payment, in the order money moves.

Three jobs:

* :func:`payment_form` returns the HTML that sends a browser to Alipay's
  cashier. The SDK builds and signs it locally, so no request leaves the server
  until the buyer's browser submits it.
* :func:`verified_notification` decides whether a POST claiming to be from
  Alipay really is. Nothing in this service may credit an account on the
  strength of an unverified request.
* :func:`query_trade` asks Alipay what actually became of an order. The official
  notification contract requires this fallback, and it is also what lets the
  whole feature work before a public HTTPS notification address exists.

Key material is read from the server environment and is never logged.
"""

import json
import logging

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import (
    AlipayTradePagePayModel,
)
from alipay.aop.api.domain.AlipayTradeQueryModel import AlipayTradeQueryModel
from alipay.aop.api.request.AlipayTradePagePayRequest import (
    AlipayTradePagePayRequest,
)
from alipay.aop.api.request.AlipayTradeQueryRequest import (
    AlipayTradeQueryRequest,
)
from alipay.aop.api.util.SignatureUtils import (
    get_sign_content,
    verify_with_rsa,
)

from server import config

log = logging.getLogger("checkpause.payments")

# The only two statuses that mean the buyer's money moved.
PAID_STATUSES = ("TRADE_SUCCESS", "TRADE_FINISHED")

# A refund, a closure or a split arrives carrying a successful-looking
# trade_status, and these are what give it away.
REFUND_MARKERS = ("out_biz_no", "gmt_refund", "refund_fee")

# The one product code the PC checkout accepts.
PRODUCT_CODE = "FAST_INSTANT_TRADE_PAY"


class AlipayError(RuntimeError):
    """The gateway refused, or could not be reached or understood."""


def _client():
    settings = config.alipay_settings()
    if not settings["enabled"]:
        raise AlipayError("alipay is not configured on this server")
    client_config = AlipayClientConfig()
    client_config.server_url = settings["gateway"]
    client_config.app_id = settings["app_id"]
    client_config.app_private_key = settings["private_key"]
    client_config.alipay_public_key = settings["alipay_public_key"]
    client_config.charset = "utf-8"
    client_config.sign_type = "RSA2"
    return DefaultAlipayClient(alipay_client_config=client_config)


def payment_form(order_id, amount_yuan, subject=""):
    """The auto-submitting HTML that takes a browser to the cashier.

    ``page_execute`` rather than ``execute``: only the former returns a form,
    and using the wrong one is the mistake Alipay's own guide calls the most
    common integration error.
    """
    settings = config.alipay_settings()
    request = AlipayTradePagePayRequest()
    # Both are optional. An empty notify_url is not the same as a placeholder:
    # the contract says to omit the field entirely rather than send one that
    # points nowhere.
    if settings["notify_url"]:
        request.notify_url = settings["notify_url"]
    if settings["return_url"]:
        request.return_url = settings["return_url"]

    model = AlipayTradePagePayModel()
    model.out_trade_no = order_id
    model.total_amount = amount_yuan
    model.subject = subject or "CheckPause credits"
    model.product_code = PRODUCT_CODE
    request.biz_model = model

    try:
        return _client().page_execute(request, http_method="POST")
    except AlipayError:
        raise
    except Exception as error:
        log.warning("could not build a payment form for %s", order_id)
        raise AlipayError(str(error)) from error


def verified_notification(params):
    """The notification's own fields when the signature checks out, else None.

    Every field is kept exactly as it arrived: the signature covers the raw
    values, so dropping or rewriting any of them would change what is being
    verified.
    """
    settings = config.alipay_settings()
    if not settings["enabled"]:
        return None

    sign = (params.get("sign") or "").strip()
    if not sign:
        return None

    signed = dict(params)
    signed.pop("sign", None)
    signed.pop("sign_type", None)

    try:
        message = get_sign_content(signed).encode("utf-8")
        if not verify_with_rsa(settings["alipay_public_key"], message, sign):
            return None
    except Exception:
        # rsa.verify raises rather than returning False when a signature is
        # wrong, so both outcomes have to be treated as "not genuine".
        return None
    return dict(params)


def notification_is_paid(params):
    """Whether a verified notification means the buyer actually paid."""
    if params.get("trade_status") not in PAID_STATUSES:
        return False
    return not any(params.get(marker) for marker in REFUND_MARKERS)


def query_trade(order_id):
    """Ask the gateway about an order.

    Returns the decoded response body, or ``{}`` when Alipay has never heard of
    the order. A failed signature on the response raises instead of being
    mistaken for a missing trade.
    """
    request = AlipayTradeQueryRequest()
    model = AlipayTradeQueryModel()
    model.out_trade_no = order_id
    request.biz_model = model

    try:
        raw = _client().execute(request)
    except Exception as error:
        log.warning("trade query failed for %s: %s", order_id, error)
        raise AlipayError(str(error)) from error

    try:
        return json.loads(raw)
    except ValueError as error:
        raise AlipayError("unreadable response from alipay") from error


def trade_is_paid(payload):
    """Whether a :func:`query_trade` answer describes a completed payment."""
    if not isinstance(payload, dict):
        return False
    if payload.get("code") != "10000":
        return False
    return payload.get("trade_status") in PAID_STATUSES
