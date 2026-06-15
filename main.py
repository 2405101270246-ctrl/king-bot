"""
Entry point – orchestrates the full pipeline on a 1-minute polling loop.

Pipeline per new reel:
  scraper → downloader → processor → telegram_sender → cleanup
"""
import asyncio
import signal
from pathlib import Path
from typing import Optional

import database
import downloader
import processor
import scraper
import telegram_sender
from config import CHECK_INTERVAL_SECONDS
from logger import get_logger

log = get_logger("main")
_shutdown = asyncio.Event()


def _register_signals() -> None:
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, lambda *_: _shutdown.set())
        except (OSError, ValueError):
            pass   # not available on all platforms (Windows)


def _cleanup(*paths: Optional[Path]) -> None:
    for p in paths:
        if p and p.exists():
            try:
                p.unlink()
                log.debug("Deleted temp file: %s", p.name)
            except OSError as exc:
                log.warning("Could not delete %s: %s", p, exc)


async def _handle_reel(reel: dict) -> None:
    reel_id: str = reel["reel_id"]
    url: str     = reel["url"]

    if database.is_processed(reel_id):
        log.debug("Already processed – skipping %s", reel_id)
        return

    database.mark_pending(reel_id, url)
    log.info("▶ Processing reel %s", reel_id)

    # ── 1. fetch metadata ────────────────────────────────────────────────
    info = await downloader.get_video_info(url)
    title = (info or {}).get("title", reel_id)

    # ── 2. download ──────────────────────────────────────────────────────
    raw_video: Optional[Path] = await downloader.download_reel(reel_id, url)
    if not raw_video:
        database.mark_failed(reel_id)
        return

    # ── 3. process (swap audio) ──────────────────────────────────────────
    final_video: Optional[Path] = await processor.process_video(raw_video, reel_id)
    if not final_video:
        database.mark_failed(reel_id)
        _cleanup(raw_video)
        return

    # ── 4. send to Telegram ──────────────────────────────────────────────
    ok = await telegram_sender.send_video(final_video, caption=title)

    if ok:
        database.mark_done(reel_id)
    else:
        database.mark_failed(reel_id)

    # ── 5. cleanup ───────────────────────────────────────────────────────
    _cleanup(raw_video, final_video)


async def _poll_once() -> None:
    log.info("Checking for new reels…")
    reels = await scraper.fetch_reels()
    if not reels:
        log.info("No reels found this round.")
        return

    # only send reels not already processed
    new_reels = [r for r in reels if not database.is_processed(r["reel_id"])]
    log.info("%d new reel(s) to process (skipping %d already done).",
             len(new_reels), len(reels) - len(new_reels))

    for reel in new_reels:
        if _shutdown.is_set():
            break
        await _handle_reel(reel)
        # 15 min gap between each reel send
        if new_reels.index(reel) < len(new_reels) - 1:
            log.info("Waiting 900s before next reel…")
            try:
                await asyncio.wait_for(_shutdown.wait(), timeout=900)
            except asyncio.TimeoutError:
                pass


async def main() -> None:
    _register_signals()
    database.init_db()
    log.info("Bot started. Poll interval: %ds", CHECK_INTERVAL_SECONDS)

    while not _shutdown.is_set():
        try:
            await _poll_once()
        except Exception as exc:
            log.error("Unexpected error in poll loop: %s", exc, exc_info=True)

        # interruptible sleep
        try:
            await asyncio.wait_for(_shutdown.wait(), timeout=CHECK_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            pass

    log.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
