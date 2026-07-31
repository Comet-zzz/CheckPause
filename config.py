import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")

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

MODEL_NAME = "deepseek-v4-flash"