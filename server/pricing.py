"""What a request costs, and how much to reserve before running it.

The prices live in one table, in credits per million tokens, because that is
the form the numbers actually have to be in: the ledger counts credits and the
upstream bills per token. An upstream price change is then a single edit plus a
version bump, rather than a formula hunted out of the endpoint.

The version string is copied into every ledger row, so a charge can always be
explained by the table that was in force when it was issued.
"""

import math

# Bump this whenever a number below changes: it is the only record of which
# table produced a given charge.
PRICE_VERSION = "2026-09-17.1"

# User-facing price, in credits per 1M tokens. One credit sells for CNY 0.01 and
# costs roughly CNY 0.005 to deliver, so these are about twice the upstream peak
# rates for deepseek-flash (USD 0.3/M in, USD 1.2/M out, at about 7.1 CNY/USD).
#
# Peak hours are 01:00-04:00 and 06:00-10:00 UTC, Monday to Friday, so users are
# billed as if every request ran at peak. Off-peak upstream rates are half of
# peak, and inputs that hit the context cache are about fifty times cheaper than
# a miss; both differences stay with the platform, which is why the real margin
# lands above the 50% the two rates above imply.
INPUT_CREDITS_PER_MILLION = 400
OUTPUT_CREDITS_PER_MILLION = 1600

# No exchange is free: without a floor, rounding would give tiny prompts away.
MINIMUM_CHARGE = 1

# Reserving credits before the model runs means guessing two things. The size of
# the input is guessed from the text, deliberately on the generous side. The
# answer is guessed at OUTPUT_TOKEN_ALLOWANCE, and callers pass the same cap
# they send to the upstream as ``max_tokens`` - which makes the reservation a
# true upper bound rather than an optimistic one, so a request can never finish
# owing more than was set aside for it.
#
# Both guesses are corrected when the request settles against the real usage, so
# an over-estimate costs the user nothing but a temporary dip in the number that
# has to be available before the request can start.
CHARS_PER_TOKEN = 2
OUTPUT_TOKEN_ALLOWANCE = 3000


def credits_for(input_tokens, output_tokens):
    """The price of one exchange, rounded up so nobody is undercharged."""
    weighted = (
        max(0, int(input_tokens)) * INPUT_CREDITS_PER_MILLION
        + max(0, int(output_tokens)) * OUTPUT_CREDITS_PER_MILLION
    )
    return max(MINIMUM_CHARGE, math.ceil(weighted / 1_000_000))


def estimate_hold(messages, max_output_tokens=OUTPUT_TOKEN_ALLOWANCE):
    """Credits to reserve before the upstream is called.

    Pass the same token cap the upstream is given and the result is an upper
    bound on what the request can cost.
    """
    characters = sum(
        len(message.get("content") or "") for message in messages
    )
    return credits_for(
        math.ceil(characters / CHARS_PER_TOKEN), max_output_tokens
    )
