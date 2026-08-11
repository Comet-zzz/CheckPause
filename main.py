import sys
import time
import io
import os
import threading
import chess
import chess.pgn
from config import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from engine import analyze_with_stockfish
from ai import chat_with_deepseek
from profile import load_profile, create_profile, update_profile, get_accuracy_trend, get_avg_accuracy


def compact_analysis(results):
    lines = []
    for r in results:
        move = r['move']
        score = r['engine_score']
        best = r.get('best_move')
        if best and best != move:
            lines.append(f"{move}(score:{score}, best:{best})")
        else:
            lines.append(f"{move}(score:{score})")
    return "; ".join(lines)


def main():
    profile = load_profile()
    if profile is None:
        print("🎯 Welcome to CheckPause!")
        print("First-time setup. Please enter your username")
        username = input("Username: ").strip()
        if not username:
            username = "Player"
        profile = create_profile(username)
        print(f"✅ Profile created! Welcome, {username}!\n")
    else:
        print(f"🎯 Welcome back, {profile['username']}!")
        if profile["latest_accuracy"] is not None:
            avg = get_avg_accuracy(profile)
            last_date = profile['history'][-1]['date'] if profile['history'] else "N/A"
            print(f"\n📊 Your stats:")
            print(f"   ─ Last game: {last_date}")
            if avg:
                print(f"   ─ Average accuracy: {avg:.1f}%")
            print(f"   ─ Total games: {profile['total_games']}")
        print()

    print("Please paste your PGN game, then enter END on a new line:")
    lines = []
    while True:
        line = input()
        if line.lower() in ["clear", "/reset"]:
            confirm = input("⚠️ Confirm delete all user data? This cannot be undone! (y/n): ")
            if confirm.lower() == 'y':
                if os.path.exists("profile.json"):
                    os.remove("profile.json")
                    print("✅ All user data cleared. Please restart the program.")
                    sys.exit(0)
                else:
                    print("⚠️ Profile file not found.")
            else:
                print("✅ Deletion cancelled.")
            continue
        if line == "END":
            break
        lines.append(line)
    pgn = "\n".join(lines)

    print("📥 Parsing PGN...", end="")
    try:
        test_game = chess.pgn.read_game(io.StringIO(pgn))
        if test_game is None:
            print(" Failed")
            sys.exit("❌ Invalid PGN format.")
        print(" Success")
    except Exception as e:
        print(" Failed")
        sys.exit(f"❌ Parse error: {e}")

    data, err, accuracy = analyze_with_stockfish(pgn)
    if err:
        print("❌ Error:", err)
        sys.exit()

    avg_before = get_avg_accuracy(profile)
    prev_accuracy = profile.get("latest_accuracy")
    profile = update_profile(profile, accuracy, pgn)
    avg_after = get_avg_accuracy(profile)

    print(f"\n🎯 Username: {profile['username']}")
    print(f"📅 Analysis date: {profile['history'][-1]['date']}")
    print(f"📈 Latest accuracy: {accuracy}%")

    if avg_after is not None:
        trend_str = ""
        if avg_before is not None:
            diff = avg_after - avg_before
            if diff > 0:
                trend_str = f" (↑+{diff:.1f}%)"
            elif diff < 0:
                trend_str = f" (↓{diff:.1f}%)"
            else:
                trend_str = " (持平)"
        print(f"📊 Average accuracy: {avg_after:.1f}%{trend_str}")

    print(f"📊 Total games: {profile['total_games']}")
    print()

    compact_data = compact_analysis(data)
    first_user_message = USER_PROMPT_TEMPLATE.format(棋谱=pgn, 数据=compact_data)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": first_user_message}
    ]

    while True:
        user_input = input(f"{profile['username']}: ")
        if user_input.lower() in ["clear", "/reset", "/clear"]:
            confirm = input("⚠️ Confirm delete all user data? This cannot be undone! (y/n): ")
            if confirm.lower() == 'y':
                if os.path.exists("profile.json"):
                    os.remove("profile.json")
                    print("✅ All user data cleared. Please restart the program.")
                    sys.exit(0)
                else:
                    print("⚠️ Profile file not found.")
            else:
                print("✅ Deletion cancelled.")
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye~")
            break

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

        if not first_chunk_received:
            stop_timer.set()
            timer_thread.join(timeout=0.5)
            elapsed_first = time.time() - start_time
            sys.stdout.write(f"\r💭 Thinking... ({elapsed_first:.1f}s)\n")
            sys.stdout.flush()

        print("\n")

        messages.append({"role": "assistant", "content": full_reply})


if __name__ == "__main__":
    main()