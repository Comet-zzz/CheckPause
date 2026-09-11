import io
import sys
import chess
import chess.pgn
from chat_ui import run_chat
from config import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from engine import analyze_with_stockfish
from input_handler import read_pgn
from profile import load_profile, create_profile, update_profile, get_avg_accuracy


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

    pgn = read_pgn()

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

    run_chat(profile, messages)


if __name__ == "__main__":
    main()