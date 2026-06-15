"""Download Facebook Reels via yt-dlp."""
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp
from config import DOWNLOADS_DIR, YTDLP_RATE_LIMIT
from logger import get_logger

log = get_logger("downloader")

_YDL_OPTS_BASE: Dict[str, Any] = {
    "format": "hd/best",
    "merge_output_format": "mp4",
    "ratelimit": YTDLP_RATE_LIMIT,
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "retries": 5,
    "fragment_retries": 5,
    "nocheckcertificate": True,
}


def _build_opts(out_path: Path) -> Dict[str, Any]:
    return {
        **_YDL_OPTS_BASE,
        "outtmpl": str(out_path / "%(id)s.%(ext)s"),
    }


async def download_reel(reel_id: str, url: str) -> Optional[Path]:
    """
    Download *url* into DOWNLOADS_DIR.
    Returns the local file path on success, None on failure.
    """
    opts = _build_opts(DOWNLOADS_DIR)

    def _run() -> Optional[Path]:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                p = Path(filename)
                if not p.exists():
                    # yt-dlp may have merged to .mp4
                    p = p.with_suffix(".mp4")
                if p.exists():
                    log.info("Downloaded: %s", p.name)
                    return p
                log.error("Expected file not found: %s", filename)
                return None
        except yt_dlp.utils.DownloadError as exc:
            log.error("yt-dlp error for %s: %s", reel_id, exc)
            return None

    return await asyncio.to_thread(_run)


async def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """Return yt-dlp metadata dict without downloading."""
    opts = {**_YDL_OPTS_BASE, "skip_download": True}

    def _run() -> Optional[Dict]:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as exc:
            log.error("get_video_info failed: %s", exc)
            return None

    return await asyncio.to_thread(_run)
