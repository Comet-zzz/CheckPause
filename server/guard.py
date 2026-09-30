"""Keep the tuned prompt from being read back out of a reply.

The tuned prompt is the thing the paid tier is paying for, and no amount of
wording in that prompt makes a model immune to being asked to recite it. This
is the second line: the reply is watched as it is produced, and a stretch of
text that matches the protected prompt long enough to be a real copy is
replaced instead of streamed on.

It is a defence in depth rather than a guarantee, and one that watches the
reply instead of trusting the prompt to be obeyed. Detection is whitespace-
and case-insensitive, because "repeat it" answers often come back reformatted.

Because a reply is streamed, a short tail is held back until the next piece
arrives. Only text older than the hold-back window has been shown, so a copy
cannot slip out ahead of the check.
"""

# How many matching characters count as a copy rather than a coincidence.
MIN_MATCH = 40

# How much of the tail stays buffered before anything is released. It has to
# cover a full match even after whitespace is squeezed out, so a copy is always
# caught while it is still in the buffer - with room left for the typewriter
# effect to still look like one.
HOLD_BACK = 80

DEFAULT_REPLACEMENT = (
    "(I can't repeat my internal instructions. Let's get back to the game.)"
)


def _normalise(text):
    """Lowercase and drop whitespace, so reformatting cannot hide a copy."""
    return "".join(text.lower().split())


class PromptLeakGuard:
    """Screen a streamed reply for a verbatim stretch of ``protected``."""

    def __init__(
        self,
        protected,
        replacement=DEFAULT_REPLACEMENT,
        min_match=MIN_MATCH,
        hold_back=HOLD_BACK,
    ):
        protected = _normalise(protected or "")
        self.min_match = max(1, int(min_match))
        self.hold_back = max(self.min_match, int(hold_back))
        self.replacement = replacement
        self.leaked = False
        self._buffer = ""
        self._ngrams = {
            protected[index : index + self.min_match]
            for index in range(len(protected) - self.min_match + 1)
        }

    def _contains_a_copy(self, text):
        if not self._ngrams:
            return False
        normalised = _normalise(text)
        for index in range(len(normalised) - self.min_match + 1):
            if normalised[index : index + self.min_match] in self._ngrams:
                return True
        return False

    def feed(self, piece):
        """Take the next fragment; return whatever is now safe to send."""
        if self.leaked:
            return ""
        self._buffer += piece or ""
        if self._contains_a_copy(self._buffer):
            self.leaked = True
            self._buffer = ""
            return self.replacement
        if len(self._buffer) > self.hold_back:
            cut = len(self._buffer) - self.hold_back
            released, self._buffer = self._buffer[:cut], self._buffer[cut:]
            return released
        return ""

    def flush(self):
        """Release the held-back tail once the stream has ended."""
        if self.leaked:
            return ""
        released, self._buffer = self._buffer, ""
        return released
