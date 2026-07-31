from openai import OpenAI
from config import DEEPSEEK_API_KEY, MODEL_NAME

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def chat_with_deepseek(messages):
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content