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


def _system_prompt(language=""):
    prompt = config.system_prompt()
    instruction = LANGUAGE_INSTRUCTIONS.get(language)
    if instruction:
        return f"{prompt}\n\n{instruction}"
    return prompt


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
