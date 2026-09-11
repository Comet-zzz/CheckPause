import os
import sys
import threading
import time

from ai import ChatRequestError, chat_with_deepseek
from i18n import choose_language, t
from profile import set_language


PROFILE_FILE = "profile.json"


def _clear_profile_data(language):
    confirm = input(t("confirm_delete", language))
    if confirm.lower() == "y":
        if os.path.exists(PROFILE_FILE):
            os.remove(PROFILE_FILE)
            print(t("data_cleared", language))
            sys.exit(0)
        print(t("profile_not_found", language))
    else:
        print("✅ 已取消删除。" if language == "zh-CN" else "✅ Deletion cancelled.")


def run_chat(profile, messages):
    language = profile.get("language", "zh-CN")
    while True:
        user_input = input(f"{profile['username']}: ")
        if user_input.lower() in ["clear", "/reset", "/clear"]:
            _clear_profile_data(language)
            continue

        if user_input.lower() in ["/language", "/lang"]:
            language = choose_language()
            set_language(profile, language)
            print(t("language_changed", language))
            continue

        if user_input.lower() in ["exit", "quit"]:
            print(t("goodbye", language))
            return

        messages.append({"role": "user", "content": user_input})
        print(t("thinking", language, seconds=0.0), end="", flush=True)
        start_time = time.time()
        stop_timer = threading.Event()
        first_chunk_received = False

        def update_timer():
            while not stop_timer.is_set():
                elapsed = time.time() - start_time
                sys.stdout.write(f"\r{t('thinking', language, seconds=elapsed)}")
                sys.stdout.flush()
                time.sleep(0.1)

        timer_thread = threading.Thread(target=update_timer, daemon=True)
        timer_thread.start()

        full_reply = ""
        try:
            for chunk in chat_with_deepseek(messages, language):
                if not first_chunk_received:
                    first_chunk_received = True
                    stop_timer.set()
                    timer_thread.join(timeout=0.5)
                    elapsed_first = time.time() - start_time
                    sys.stdout.write(f"\r{t('thinking', language, seconds=elapsed_first)}\n")
                    sys.stdout.flush()
                for char in chunk:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(0.03)
                full_reply += chunk
        except ChatRequestError as exc:
            sys.stdout.write(f"\r❌ {exc}\n")
            sys.stdout.flush()
            continue
        finally:
            stop_timer.set()
            timer_thread.join(timeout=0.5)

        if not first_chunk_received:
            elapsed_first = time.time() - start_time
            sys.stdout.write(f"\r{t('thinking', language, seconds=elapsed_first)}\n")
            sys.stdout.flush()

        print("\n")
        messages.append({"role": "assistant", "content": full_reply})
