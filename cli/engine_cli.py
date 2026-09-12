from checkpause.core.engine import StockfishAnalyzer
from checkpause.i18n import t


def analyze_with_stockfish(pgn_text, language="zh-CN"):
    print(t("engine_analyzing", language))

    def on_progress(percent):
        bar_length = 20
        filled = int(percent / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r  progress: [{bar}] {percent}%", end="")

    analyzer = StockfishAnalyzer()
    results, err, accuracy = analyzer.analyze(
        pgn_text, language, on_progress=on_progress
    )
    if err is None:
        print(t("ready", language))
    return results, err, accuracy
