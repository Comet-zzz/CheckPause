import os
import sys
import threading
import time

from ai import ChatRequestError, chat_with_deepseek


PROFILE_FILE = "profile.json"


def _clear_profile_data():
    confirm = input("⚠️ Confirm delete all user data? This cannot be undone! (y/n): ")
    if confirm.lower() == "y":
        if os.path.exists(PROFILE_FILE):
            os.remove(PROFILE_FILE)
            print("✅ All user data cleared. Please restart the program.")
            sys.exit(0)
        print("⚠️ Profile file not found.")
    else:
        print("✅ Deletion cancelled.")


def run_chat(profile, messages):
    while True:
        user_input = input(f"{profile['username']}: ")
        if user_input.lower() in ["clear", "/reset", "/clear"]:
            _clear_profile_data()
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye~")
            return

        messages.append({"role": "user", "content": user_input})
        print("💭 Thinking... (0.0s)", end="", flush=True)
        start_time = time.time()
        stop_timer = threading.Event()
        first_chunk_received = False

        def update_timer():
            while not stop_timer.is_set():
                elapsed = time.time() - start_time
                sys.stdout.write(f"\r💭 Thinking... ({elapsed:.1f}s)")
                sys.stdout.flush()
                time.sleep(0.1)

        timer_thread = threading.Thread(target=update_timer, daemon=True)
        timer_thread.start()

        full_reply = ""
        try:
            for chunk in chat_with_deepseek(messages):
                if not first_chunk_received:
                    first_chunk_received = True
                    stop_timer.set()
                    timer_thread.join(timeout=0.5)
                    elapsed_first = time.time() - start_time
                    sys.stdout.write(f"\r💭 Thinking... ({elapsed_first:.1f}s)\n")
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
            sys.stdout.write(f"\r💭 Thinking... ({elapsed_first:.1f}s)\n")
            sys.stdout.flush()

        print("\n")
        messages.append({"role": "assistant", "content": full_reply})
