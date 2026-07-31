import sys
import time
import io
import os
import chess
import chess.pgn
from config import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from engine import analyze_with_stockfish
from ai import chat_with_deepseek
from profile import load_profile, create_profile, update_profile, get_accuracy_trend, get_avg_accuracy

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
            trend = get_accuracy_trend(profile)
            avg = get_avg_accuracy(profile)
            print(f"\n📊 Your current stats:")
            print(f"   ─ Latest accuracy: {profile['latest_accuracy']}%")
            if trend:
                print(f"   ─ Trend: {trend}")
            if avg:
                print(f"   ─ Average accuracy: {avg:.1f}%")
            print(f"   ─ Total games analyzed: {profile['total_games']}")
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

    profile = update_profile(profile, accuracy, pgn)

    print(f"\n🎯 Username: {profile['username']}")
    print(f"📅 Analysis date: {profile['history'][-1]['date']}")
    print(f"📈 Game accuracy: {accuracy}%")
    if profile['total_games'] > 1:
        trend = get_accuracy_trend(profile)
        if trend:
            print(f"📊 Trend: {trend}")
    print(f"📊 Total games: {profile['total_games']}")
    print()

    first_user_message = USER_PROMPT_TEMPLATE.format(棋谱=pgn, 数据=data)
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
        print("💭 Thinking...")

        full_reply = ""
        print("\n", end="")
        for chunk in chat_with_deepseek(messages):
            for char in chunk:
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(0.03)
            full_reply += chunk
        print("\n")

        messages.append({"role": "assistant", "content": full_reply})

if __name__ == "__main__":
    main()