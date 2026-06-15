"""Send videos to a Telegram user/bot chat with retry logic."""
import asyncio
from pathlib import Path
import httpx
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_RETRIES,
    TELEGRAM_RETRY_DELAY,
)
from logger import get_logger

log = get_logger("telegram_sender")

_API = "https://api.telegram.org/bot{token}/sendVideo"
_MAX_SIZE_BYTES = 50 * 1024 * 1024   # Telegram Bot API limit: 50 MB


async def send_video(video_path: Path, caption: str = "") -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return False

    size = video_path.stat().st_size
    if size > _MAX_SIZE_BYTES:
        log.warning("Video %s is %.1f MB – exceeds 50 MB limit; skipping.",
                    video_path.name, size / 1024 / 1024)
        return False

    url = _API.format(token=TELEGRAM_BOT_TOKEN)

    for attempt in range(1, TELEGRAM_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=120, verify=False) as client:
                with video_path.open("rb") as fh:
                    resp = await client.post(
                        url,
                        data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]},
                        files={"video": (video_path.name, fh, "video/mp4")},
                    )
            if resp.status_code == 200:
                log.info("Sent %s to Telegram chat %s.", video_path.name, TELEGRAM_CHAT_ID)
                return True
            log.warning("Attempt %d/%d – HTTP %d: %s",
                        attempt, TELEGRAM_RETRIES, resp.status_code, resp.text[:200])
        except Exception as exc:
            log.warning("Attempt %d/%d – error: %s", attempt, TELEGRAM_RETRIES, exc)

        if attempt < TELEGRAM_RETRIES:
            await asyncio.sleep(TELEGRAM_RETRY_DELAY)

    log.error("All %d attempts failed for %s.", TELEGRAM_RETRIES, video_path.name)
    return False
