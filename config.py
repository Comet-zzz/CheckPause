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

SYSTEM_PROMPT = "请根据用户提供的棋谱和Stockfish分析数据，回答用户的问题。"

USER_PROMPT_TEMPLATE = """这是棋谱和Stockfish分析数据：

棋谱：
{棋谱}

Stockfish 每步分析数据：
{数据}"""

ISSUE_EXTRACTION_PROMPT = """基于以上棋谱和Stockfish分析数据，请用一句简洁的中文（不超过20个字）概括：这盘棋中用户最需要改进的问题是什么？只输出那一句话，不要其他内容。"""

MODEL_NAME = "deepseek-v4-flash"