import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"缺少必要的环境变量 '{name}'，请在 .env 文件或系统环境变量中设置。"
        )
    return value


DEEPSEEK_API_KEY = get_required_env("DEEPSEEK_API_KEY")

configured_stockfish_path = os.getenv("STOCKFISH_PATH", "").strip()
local_stockfish_path = os.path.join(
    BASE_DIR, "stockfish", "stockfish", "stockfish-windows-x86-64-universal.exe"
)
STOCKFISH_PATH = configured_stockfish_path or local_stockfish_path
if not os.path.isfile(STOCKFISH_PATH):
    if os.path.isfile(local_stockfish_path):
        STOCKFISH_PATH = local_stockfish_path
    else:
        raise RuntimeError(
            "未找到 Stockfish 可执行文件。请在 .env 中设置 STOCKFISH_PATH，"
            "或将 Stockfish 放入项目的 stockfish 文件夹。"
        )

import chess.engine
ENGINE_LIMIT = chess.engine.Limit(depth=18, time=2.0)

ACCURACY_THRESHOLDS = {
    "perfect": 50,
    "good": 150,
    "miss": 150
}

SYSTEM_PROMPT = "Please answer user's questions based on the provided PGN game and Stockfish analysis data."

USER_PROMPT_TEMPLATE = """This is the PGN game and Stockfish analysis data:

PGN Game:
{棋谱}

Stockfish Analysis Data per move:
{数据}"""

MODEL_NAME = "deepseek-flash"