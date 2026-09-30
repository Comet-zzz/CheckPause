"""Tests for the in-process rate limiter."""

import unittest

from server import ratelimit


class SlidingWindowTests(unittest.TestCase):
    def setUp(self):
        ratelimit.reset()

    def test_allows_up_to_the_limit_then_refuses(self):
        window = ratelimit.SlidingWindow(limit=3, window_seconds=60)
        self.assertTrue(window.allow("k", now=0))
        self.assertTrue(window.allow("k", now=0))
        self.assertTrue(window.allow("k", now=0))
        self.assertFalse(window.allow("k", now=0))

    def test_the_window_slides(self):
        window = ratelimit.SlidingWindow(limit=2, window_seconds=10)
        window.allow("k", now=0)
        window.allow("k", now=1)
        self.assertFalse(window.allow("k", now=2))
        # The first attempt falls out once ten seconds have passed.
        self.assertTrue(window.allow("k", now=11))

    def test_keys_do_not_share_a_bucket(self):
        window = ratelimit.SlidingWindow(limit=1, window_seconds=60)
        self.assertTrue(window.allow("a", now=0))
        self.assertTrue(window.allow("b", now=0))
        self.assertFalse(window.allow("a", now=0))

    def test_retry_after_counts_down_to_the_oldest_attempt(self):
        window = ratelimit.SlidingWindow(limit=1, window_seconds=10)
        window.allow("k", now=0)
        self.assertEqual(window.retry_after("k", now=0), 10)
        self.assertEqual(window.retry_after("k", now=4), 6)
        self.assertEqual(window.retry_after("missing", now=4), 0)

    def test_named_limiters_are_reused_and_reset(self):
        self.assertTrue(ratelimit.allow("login", "1.2.3.4", 1, 60, now=0))
        self.assertFalse(ratelimit.allow("login", "1.2.3.4", 1, 60, now=0))
        ratelimit.reset()
        self.assertTrue(ratelimit.allow("login", "1.2.3.4", 1, 60, now=0))


if __name__ == "__main__":
    unittest.main()
