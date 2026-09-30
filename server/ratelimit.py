"""In-process rate limiting for the endpoints worth guessing at.

Two things are being protected against here. One is guessing a password. The
other is that signing in is not cheap: every attempt runs scrypt, which
allocates 16 MB and keeps a core busy for a moment, so an endpoint that answers
as fast as it is asked is also a way to make the server spend real resources.

The window is a sliding one, so a burst cannot be timed to straddle two fixed
windows and get twice the allowance.

State lives in the process, which matches the deployment: one uvicorn worker.
The limits are a safety net around that assumption rather than an exact quota,
and a future multi-worker deployment would want to move the counters out.
"""

import math
import threading
import time
from collections import deque


class SlidingWindow:
    """Allow at most ``limit`` attempts per ``window`` seconds, per key."""

    def __init__(self, limit, window_seconds):
        self.limit = max(1, int(limit))
        self.window = max(1.0, float(window_seconds))
        self._events = {}
        self._lock = threading.Lock()

    def allow(self, key, now=None):
        """Record an attempt and say whether it is within the allowance.

        Every attempt is recorded, refusals included, so hammering a key keeps
        its window full instead of letting the caller through a moment later.
        """
        now = time.monotonic() if now is None else now
        with self._lock:
            events = self._events.setdefault(key, deque())
            cutoff = now - self.window
            while events and events[0] <= cutoff:
                events.popleft()
            events.append(now)
            return len(events) <= self.limit

    def retry_after(self, key, now=None):
        """Seconds until the oldest recorded attempt falls out of the window."""
        now = time.monotonic() if now is None else now
        with self._lock:
            events = self._events.get(key)
            if not events:
                return 0
            return max(0, int(math.ceil(events[0] + self.window - now)))

    def clear(self):
        with self._lock:
            self._events.clear()


_limiters = {}
_limiters_lock = threading.Lock()


def _limiter(name, limit, window_seconds):
    """The limiter for a named bucket, rebuilt if its configured size changed."""
    with _limiters_lock:
        existing = _limiters.get(name)
        if (
            existing is None
            or existing.limit != max(1, int(limit))
            or existing.window != max(1.0, float(window_seconds))
        ):
            existing = SlidingWindow(limit, window_seconds)
            _limiters[name] = existing
        return existing


def allow(name, key, limit, window_seconds, now=None):
    return _limiter(name, limit, window_seconds).allow(key, now)


def retry_after(name, key, limit, window_seconds, now=None):
    return _limiter(name, limit, window_seconds).retry_after(key, now)


def reset():
    """Forget every counter. The tests use this; nothing else should."""
    with _limiters_lock:
        _limiters.clear()
