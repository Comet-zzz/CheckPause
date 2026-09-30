"""Tests for the prompt-leak guard."""

import unittest

from server.guard import PromptLeakGuard

PROMPT = "You are a chess coach. Always explain the engine's numbers plainly."


class PromptLeakGuardTests(unittest.TestCase):
    def test_ordinary_text_passes_through_unchanged(self):
        screen = PromptLeakGuard(PROMPT)
        pieces = ["Nf3 ", "is ", "better."]
        out = "".join(screen.feed(piece) for piece in pieces) + screen.flush()
        self.assertEqual(out, "Nf3 is better.")
        self.assertFalse(screen.leaked)

    def test_a_verbatim_copy_is_replaced(self):
        screen = PromptLeakGuard(PROMPT, replacement="BLOCKED")
        self.assertEqual(screen.feed(PROMPT), "BLOCKED")
        self.assertTrue(screen.leaked)
        self.assertEqual(screen.flush(), "")

    def test_a_copy_split_across_pieces_is_caught(self):
        screen = PromptLeakGuard(PROMPT, replacement="BLOCKED")
        out = ""
        for index in range(0, len(PROMPT), 5):
            out += screen.feed(PROMPT[index : index + 5])
            if screen.leaked:
                break
        self.assertTrue(screen.leaked)
        self.assertIn("BLOCKED", out)

    def test_reformatting_does_not_hide_a_copy(self):
        screen = PromptLeakGuard(PROMPT, replacement="BLOCKED")
        screen.feed(PROMPT.upper().replace(" ", "\n"))
        self.assertTrue(screen.leaked)

    def test_a_paraphrase_passes(self):
        screen = PromptLeakGuard(PROMPT, replacement="BLOCKED")
        screen.feed("You are a chess coach who explains things clearly.")
        self.assertFalse(screen.leaked)

    def test_text_too_short_to_copy_is_never_flagged(self):
        screen = PromptLeakGuard("short", replacement="BLOCKED")
        screen.feed("short and sweet, over and over. " * 10)
        self.assertFalse(screen.leaked)


if __name__ == "__main__":
    unittest.main()
