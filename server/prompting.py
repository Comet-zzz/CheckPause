"""Assemble the message list sent to the model.

The prompt is built here, on the server, so the tuned version never reaches a
user's machine. Clients send raw material only: the game, the engine numbers,
and the conversation so far.
"""

from server import config

# Each request resends the conversation, so an unbounded history would make
# every follow-up more expensive than the last. Keeping the tail is enough for
# a coaching dialogue and keeps input cost predictable.
MAX_HISTORY_MESSAGES = 12

# The tuned prompt decides how coaching sounds; this only pins the language so
# a Chinese user does not get an English answer from an English prompt.
LANGUAGE_INSTRUCTIONS = {
    "zh-CN": "Always answer in Simplified Chinese.",
    "en-US": "Always answer in English.",
}

# What the model says when somebody asks what it is.
#
# This is a refusal to disclose, not a claim about itself, and the difference
# is the whole point. A refusal holds: the model simply declines, and there is
# nothing to keep consistent. An invented identity has to be maintained, is
# contradicted by some question eventually, and - for a service that charges
# money - amounts to passing off another company's product as your own.
#
# It lives here rather than in the tuned prompt so that replacing the tuned
# prompt cannot quietly drop it. A deployment that wants other words can put
# an identity_policy.txt next to the prompt file and this is skipped.
IDENTITY_POLICY = (
    "如果被问到使用的是什么模型、哪家公司，或者是不是某个具体产品："
    "不要猜测，不要编造，也不要顺着对方给出的前提往下答。"
    "只回一句：CheckPause 会根据任务挑选合适的模型，具体实现不便透露。"
    "然后立刻把话题带回棋局本身。"
)


def _system_prompt(language=""):
    parts = [
        config.system_prompt(),
        config.identity_policy() or IDENTITY_POLICY,
    ]
    instruction = LANGUAGE_INSTRUCTIONS.get(language)
    if instruction:
        parts.append(instruction)
    return "\n\n".join(parts)


def render_context(pgn, analysis=""):
    """Wrap the game and the engine data in the server-side template.

    A template with stray braces should not take the whole endpoint down, so a
    broken template falls back to the plain one.
    """
    template = config.user_template()
    try:
        return template.format(pgn=pgn.strip(), analysis=(analysis or "").strip())
    except (KeyError, IndexError, ValueError):
        return config.FALLBACK_USER_TEMPLATE.format(
            pgn=pgn.strip(), analysis=(analysis or "").strip()
        )


def build_messages(pgn, analysis="", history=None, language=""):
    """Return the messages for one request.

    Layout: the tuned system prompt, one user turn carrying the game and the
    engine data, then the conversation so far.
    """
    messages = [
        {"role": "system", "content": _system_prompt(language)},
        {"role": "user", "content": render_context(pgn, analysis)},
    ]

    for entry in (history or [])[-MAX_HISTORY_MESSAGES:]:
        if isinstance(entry, dict):
            role = entry.get("role")
            content = entry.get("content")
        else:
            role = getattr(entry, "role", None)
            content = getattr(entry, "content", None)
        content = str(content or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    return messages
