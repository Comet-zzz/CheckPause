import os

from dotenv import load_dotenv

APP_NAME = "CheckPause"
APP_VERSION = "1.8.0"
AUTHOR = "CometZZZ"
COPYRIGHT_YEAR = "2026"
GITHUB_URL = "https://github.com/Comet-zzz/CheckPause"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))
