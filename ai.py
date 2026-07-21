from openai import OpenAI
from config import DEEPSEEK_API_KEY, MODEL_NAME, ISSUE_EXTRACTION_PROMPT

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def chat_with_deepseek(messages):
    """发送消息流，返回生成器"""
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content

def extract_issues(pgn, data):
    """基于棋谱和Stockfish数据，提取当前主要问题"""
    messages = [
        {"role": "system", "content": ISSUE_EXTRACTION_PROMPT},
        {"role": "user", "content": f"棋谱：\n{pgn}\n\nStockfish数据：\n{data}"}
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content.strip()
    except:
        return "暂时无法提取问题，请查看分析详情"