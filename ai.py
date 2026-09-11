from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI
from config import DEEPSEEK_API_KEY, MODEL_NAME


class ChatRequestError(RuntimeError):
    pass


client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=60.0,
    max_retries=0,
)

def chat_with_deepseek(messages):
    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except APITimeoutError as exc:
        raise ChatRequestError("请求超时，请稍后重试。") from exc
    except APIConnectionError as exc:
        raise ChatRequestError("无法连接 DeepSeek，请检查网络连接。") from exc
    except APIStatusError as exc:
        if exc.status_code == 401:
            message = "DeepSeek API 密钥无效，请检查 .env 配置。"
        elif exc.status_code == 429:
            message = "DeepSeek 请求过于频繁，请稍后重试。"
        else:
            message = f"DeepSeek 服务返回错误（HTTP {exc.status_code}）。"
        raise ChatRequestError(message) from exc