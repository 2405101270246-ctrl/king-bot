"""Central configuration loaded from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
MUSIC_DIR     = BASE_DIR / "music"
DOWNLOADS_DIR = BASE_DIR / "downloads"
OUTPUT_DIR    = BASE_DIR / "output"
LOGS_DIR      = BASE_DIR / "logs"
DB_PATH       = BASE_DIR / "reels.db"

for _d in (MUSIC_DIR, DOWNLOADS_DIR, OUTPUT_DIR, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── Facebook ───────────────────────────────────────────────────────────────
FACEBOOK_REELS_URL = os.getenv(
    "FACEBOOK_REELS_URL",
    "https://www.facebook.com/nisarmehdiedits/reels/",
)
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))

# ── Telegram ───────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID", "")   # your personal chat_id or group id
TELEGRAM_RETRIES     = int(os.getenv("TELEGRAM_RETRIES", "3"))
TELEGRAM_RETRY_DELAY = int(os.getenv("TELEGRAM_RETRY_DELAY", "5"))

# ── yt-dlp ─────────────────────────────────────────────────────────────────
_RATE_RAW = os.getenv("YTDLP_RATE_LIMIT", "500K")
# convert e.g. "500K" → 512000, "2M" → 2097152
def _parse_rate(s: str) -> int:
    s = s.strip().upper()
    if s.endswith("K"):  return int(float(s[:-1]) * 1024)
    if s.endswith("M"):  return int(float(s[:-1]) * 1024 * 1024)
    return int(s)
YTDLP_RATE_LIMIT = _parse_rate(_RATE_RAW)

# FFmpeg no longer used (original audio kept) – kept for backward compat
FFMPEG_THREADS = int(os.getenv("FFMPEG_THREADS", "2"))

# ── Playwright ─────────────────────────────────────────────────────────────
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
PAGE_LOAD_TIMEOUT   = int(os.getenv("PAGE_LOAD_TIMEOUT", "30000"))  # ms
SCROLL_PAUSE        = float(os.getenv("SCROLL_PAUSE", "2.0"))       # seconds
MAX_SCROLL_ROUNDS   = int(os.getenv("MAX_SCROLL_ROUNDS", "5"))
