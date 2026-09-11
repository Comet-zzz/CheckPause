import os
import sys


PROFILE_FILE = "profile.json"


def clear_profile_data():
    confirm = input("⚠️ Confirm delete all user data? This cannot be undone! (y/n): ")
    if confirm.lower() == "y":
        if os.path.exists(PROFILE_FILE):
            os.remove(PROFILE_FILE)
            print("✅ All user data cleared. Please restart the program.")
            sys.exit(0)
        print("⚠️ Profile file not found.")
    else:
        print("✅ Deletion cancelled.")


def read_pgn():
    print("Please paste your PGN game, then enter END on a new line:")
    lines = []
    while True:
        line = input()
        if line.lower() in ["clear", "/reset"]:
            clear_profile_data()
            continue
        if line == "END":
            return "\n".join(lines)
        lines.append(line)
