"""Streaming client for the upstream model.

The provider speaks the OpenAI protocol, so the official SDK is enough. Which
provider that is happens to be this deployment's business and nobody else's, so
it is read from the environment and never named here. Opening the stream and
reading it are separated on purpose: a refused request should become a proper
HTTP error before any bytes are sent, while a failure in the middle of a reply
can only end the stream.

Token counts are requested explicitly. Without ``stream_options`` the reply
arrives with no usage at all, which leaves nothing to bill, and this provider's
placement of those counts differs from OpenAI's: it attaches them to the final
content chunk instead of sending a bare usage-only chunk. Collecting usage
before looking at ``choices`` handles both shapes.
"""

from openai import AsyncOpenAI

from server import config


class UpstreamError(RuntimeError):
    """The upstream API refused the request or is not configured."""


class Usage:
    """Token counts for one exchange, filled in as its stream ends."""

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.counted = False
        self.finished = False

    def record(self, chunk):
        """Take the counts off a chunk if it carries any."""
        usage = getattr(chunk, "usage", None)
        if usage is None:
            return
        prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion = int(getattr(usage, "completion_tokens", 0) or 0)
        if prompt or completion:
            self.input_tokens = prompt
            self.output_tokens = completion
            self.counted = True


def _client():
    key = config.api_key()
    if not key:
        raise UpstreamError("no upstream API key is configured on the server")
    base_url = config.base_url()
    if not base_url:
        # Refusing beats falling back: the SDK has its own default address, and
        # silently posting a paying customer's game to the wrong provider is a
        # worse outcome than an error.
        raise UpstreamError("no upstream base URL is configured on the server")
    return AsyncOpenAI(api_key=key, base_url=base_url)


async def open_stream(messages):
    """Start a completion. Raises UpstreamError before anything is streamed."""
    client = _client()
    request = {
        "model": config.model(),
        "messages": messages,
        "stream": True,
        # Ask for the token counts that the charge is computed from.
        "stream_options": {"include_usage": True},
        # Answers are billed by the token, so an unbounded one is an unbounded
        # cost. The cap is far above a normal coaching reply.
        "max_tokens": config.max_answer_tokens(),
    }
    try:
        return await client.chat.completions.create(**request)
    except Exception as error:
        raise UpstreamError(str(error)) from error


async def iter_text(stream, usage=None):
    """Yield reply fragments as they arrive; stop quietly if the stream breaks.

    Pass a :class:`Usage` to have it filled in with the token counts that
    arrive on the last chunk.
    """
    try:
        async for chunk in stream:
            if usage is not None:
                usage.record(chunk)
            choices = getattr(chunk, "choices", None)
            if not choices:
                continue
            piece = choices[0].delta.content
            if piece:
                yield piece
        if usage is not None:
            usage.finished = True
    except Exception:
        # The client already has a partial answer, which is more useful than an
        # exception at this point. The caller settles the reservation either
        # way, so an interrupted reply is still paid for.
        return
