from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from checkpause.data.settings import get_api_config
from checkpause.i18n import t


class ChatRequestError(RuntimeError):
    pass


def _create_client(base_url, api_key):
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=0,
    )


def chat_with_model(messages, language="zh-CN"):
    config = get_api_config()
    if not config["api_key"]:
        raise ChatRequestError(t("api_key_missing", language))

    client = _create_client(config["base_url"], config["api_key"])
    try:
        stream = client.chat.completions.create(
            model=config["model"],
            messages=messages,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except APITimeoutError as exc:
        message = "请求超时，请稍后重试。" if language == "zh-CN" else "Request timed out. Please try again later."
        raise ChatRequestError(message) from exc
    except APIConnectionError as exc:
        message = "无法连接 API 服务，请检查网络或接口地址。" if language == "zh-CN" else "Could not reach the API service. Check your network or base URL."
        raise ChatRequestError(message) from exc
    except APIStatusError as exc:
        if exc.status_code == 401:
            message = "API 密钥无效，请检查设置。" if language == "zh-CN" else "Invalid API key. Please check your settings."
        elif exc.status_code == 429:
            message = "API 请求过于频繁，请稍后重试。" if language == "zh-CN" else "Too many API requests. Please try again later."
        else:
            message = (
                f"API 服务返回错误（HTTP {exc.status_code}）。"
                if language == "zh-CN"
                else f"The API service returned an error (HTTP {exc.status_code})."
            )
        raise ChatRequestError(message) from exc
