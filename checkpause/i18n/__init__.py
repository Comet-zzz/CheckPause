from checkpause.i18n.en_US import MESSAGES as _EN_US
from checkpause.i18n.zh_CN import MESSAGES as _ZH_CN

MESSAGES = {
    "zh-CN": _ZH_CN,
    "en-US": _EN_US,
}


def t(key, language="zh-CN", **values):
    messages = MESSAGES.get(language, MESSAGES["zh-CN"])
    text = messages.get(key) or MESSAGES["zh-CN"].get(key, key)
    if values:
        return text.format(**values)
    return text


def choose_language():
    print(MESSAGES["zh-CN"]["choose_language"])
    choice = input(MESSAGES["zh-CN"]["language_choice"]).strip()
    if choice == "2":
        return "en-US"
    if choice != "1":
        print(MESSAGES["zh-CN"]["invalid_language"])
    return "zh-CN"
