"""Video processor: copies video as-is (original audio kept)."""
import asyncio
import shutil
from pathlib import Path
from typing import Optional
from config import OUTPUT_DIR
from logger import get_logger

log = get_logger("processor")


def _process(video_path: Path, reel_id: str) -> Optional[Path]:
    """Simply copy the downloaded file to output dir – no audio changes."""
    out_path = OUTPUT_DIR / f"{reel_id}_final.mp4"
    try:
        shutil.copy2(video_path, out_path)
        log.info("Video ready (original audio kept): %s", out_path.name)
        return out_path
    except Exception as exc:
        log.error("Copy failed for %s: %s", reel_id, exc)
        return None


async def process_video(video_path: Path, reel_id: str) -> Optional[Path]:
    return await asyncio.to_thread(_process, video_path, reel_id)
