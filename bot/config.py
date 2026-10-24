"""All settings live here. Secrets come from environment variables / .env."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional (e.g. on GitHub Actions)
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "seen.json"

# --- Secrets -----------------------------------------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# --- Hacker News (primary) --------------------------------------------
HN_API = "https://hn.algolia.com/api/v1/search"
HN_MIN_POINTS = 100        # only alert once a front-page story reaches this
HN_MAX_ITEMS = 30          # how many front-page stories to inspect

# --- Techmeme (secondary) ---------------------------------------------
TECHMEME_FEED = "https://www.techmeme.com/feed.xml"
TECHMEME_MAX_ITEMS = 20

# --- Behaviour ---------------------------------------------------------
MAX_MESSAGES_PER_RUN = 10  # flood protection
SEEN_TTL_DAYS = 30         # forget old URLs after this long
LOOP_INTERVAL_SECONDS = 600  # used only with --loop
REQUEST_TIMEOUT = 15
USER_AGENT = "personal-tech-news-bot/1.0"

# --- Keyword filters (case-insensitive, matched against the title) ----
BLOCKLIST: list[str] = []  # e.g. ["crypto", "nft"]
ALLOWLIST: list[str] = []  # empty = allow everything; e.g. ["ai", "security"]
