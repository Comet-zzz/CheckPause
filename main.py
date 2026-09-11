import io
import sys
import chess
import chess.pgn
from chat_ui import run_chat
from config import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from engine import analyze_with_stockfish
from input_handler import read_pgn
from i18n import choose_language, t
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
        language = choose_language()
        print(t("welcome", language))
        print(t("first_setup", language))
        username = input(t("username", language)).strip()
        if not username:
            username = "Player"
        profile = create_profile(username, language)
        print(t("profile_created", language, username=username))
    else:
        language = profile.get("language", "zh-CN")
        print(t("welcome_back", language, username=profile["username"]))
        if profile["latest_accuracy"] is not None:
            avg = get_avg_accuracy(profile)
            last_date = profile['history'][-1]['date'] if profile['history'] else "N/A"
            print(t("stats", language))
            print(t("last_game", language, date=last_date))
            if avg:
                print(t("average_stat", language, accuracy=avg))
            print(t("total_stat", language, total=profile["total_games"]))
        print()

    pgn = read_pgn(language)

    print(t("parsing", language), end="")
    try:
        test_game = chess.pgn.read_game(io.StringIO(pgn))
        if test_game is None:
            print(t("failed", language))
            sys.exit(t("parse_error", language, error="格式无效"))
        print(t("success", language))
    except Exception as e:
        print(t("failed", language))
        sys.exit(t("parse_error", language, error=e))

    data, err, accuracy = analyze_with_stockfish(pgn, language)
    if err:
        print(t("error", language, error=err))
        sys.exit()

    avg_before = get_avg_accuracy(profile)
    profile = update_profile(profile, accuracy, pgn)
    avg_after = get_avg_accuracy(profile)

    print("\n" + t("username_stat", language, username=profile["username"]))
    print(t("analysis_date", language, date=profile["history"][-1]["date"]))
    print(t("latest_accuracy", language, accuracy=accuracy))

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
        print(t("average_accuracy", language, accuracy=avg_after, trend=trend_str))

    print(t("total_games", language, total=profile["total_games"]))
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