import os
import sys

from i18n import t

PROFILE_FILE = "profile.json"


def clear_profile_data(language="zh-CN"):
    confirm = input(t("confirm_delete", language))
    if confirm.lower() == "y":
        if os.path.exists(PROFILE_FILE):
            os.remove(PROFILE_FILE)
            print(t("data_cleared", language))
            sys.exit(0)
        print(t("profile_not_found", language))
    else:
        print(t("deletion_cancelled", language))


def read_pgn(language="zh-CN"):
    print(t("paste_pgn", language))
    lines = []
    while True:
        line = input()
        if line.lower() in ["clear", "/reset"]:
            clear_profile_data(language)
            continue
        if line == "END":
            return "\n".join(lines)
        lines.append(line)
