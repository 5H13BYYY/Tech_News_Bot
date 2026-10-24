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

# --- Lobsters (third source) -------------------------------------------
LOBSTERS_ENABLED = True
LOBSTERS_URL = "https://lobste.rs/hottest.json"
LOBSTERS_MIN_SCORE = 30    # Lobsters scores run lower than HN points
LOBSTERS_MAX_ITEMS = 25

# --- Morning digest ----------------------------------------------------
DIGEST_ENABLED = True
DIGEST_HOUR = 8            # local time (TIMEZONE); the first run at/after this hour sends it
DIGEST_HN_ITEMS = 5        # keep the total modest: Telegram caps a message at 4096 chars
DIGEST_TECHMEME_ITEMS = 5
DIGEST_LOBSTERS_ITEMS = 3

# --- Topic tags --------------------------------------------------------
CLASSIFY_ENABLED = True    # add a '🤖 #AI · 💰 #Funding' line to each alert
MAX_TAGS = 2               # tags shown per story

# --- Behaviour ---------------------------------------------------------
MAX_MESSAGES_PER_RUN = 10  # flood protection
SEEN_TTL_DAYS = 30         # forget old URLs after this long
LOOP_INTERVAL_SECONDS = 600  # used only with --loop
REQUEST_TIMEOUT = 15
USER_AGENT = "personal-tech-news-bot/1.0"
TIMEZONE = "Asia/Phnom_Penh"  # IANA name, used for timestamps and the digest hour

# --- Keyword filters (case-insensitive, matched against the title) ----
BLOCKLIST: list[str] = []  # e.g. ["crypto", "nft"]
ALLOWLIST: list[str] = []  # empty = allow everything; e.g. ["ai", "security"]
