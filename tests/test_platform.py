import unittest

from checkpause.config import STOCKFISH_DIRECTORY, stockfish_executable_name


class StockfishNameTests(unittest.TestCase):
    def test_windows_uses_the_bundled_exe(self):
        self.assertEqual(
            stockfish_executable_name("win32"),
            "stockfish-windows-x86-64-universal.exe",
        )

    def test_macos_uses_the_universal_binary(self):
        self.assertEqual(
            stockfish_executable_name("darwin"), "stockfish-macos-universal"
        )

    def test_linux_uses_the_bare_name(self):
        self.assertEqual(stockfish_executable_name("linux"), "stockfish")

    def test_the_directory_matches_the_bundled_layout(self):
        self.assertEqual(STOCKFISH_DIRECTORY, ("stockfish", "stockfish"))


if __name__ == "__main__":
    unittest.main()
