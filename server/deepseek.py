"""Streaming client for the upstream model.

DeepSeek speaks the OpenAI protocol, so the official SDK is enough. Opening
the stream and reading it are separated on purpose: a refused request should
become a proper HTTP error before any bytes are sent, while a failure in the
middle of a reply can only end the stream.
"""

from openai import AsyncOpenAI

from server import config


class UpstreamError(RuntimeError):
    """The upstream API refused the request or is not configured."""


def _client():
    key = config.api_key()
    if not key:
        raise UpstreamError("no upstream API key is configured on the server")
    return AsyncOpenAI(api_key=key, base_url=config.base_url())


async def open_stream(messages):
    """Start a completion. Raises UpstreamError before anything is streamed."""
    client = _client()
    try:
        return await client.chat.completions.create(
            model=config.model(),
            messages=messages,
            stream=True,
        )
    except Exception as error:
        raise UpstreamError(str(error)) from error


async def iter_text(stream):
    """Yield reply fragments as they arrive; stop quietly if the stream breaks."""
    try:
        async for chunk in stream:
            if not chunk.choices:
                continue
            piece = chunk.choices[0].delta.content
            if piece:
                yield piece
    except Exception:
        # The client already has a partial answer, which is more useful than an
        # exception at this point. Accounts and billing arrive next milestone
        # and will decide how an interrupted reply is charged.
        return
