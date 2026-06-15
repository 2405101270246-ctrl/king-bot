"""SQLite database layer for tracking processed reels."""
import sqlite3
import contextlib
from datetime import datetime
from config import DB_PATH
from logger import get_logger

log = get_logger("database")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with contextlib.closing(_connect()) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reels (
                reel_id     TEXT PRIMARY KEY,
                url         TEXT NOT NULL,
                title       TEXT,
                status      TEXT NOT NULL DEFAULT 'pending',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        conn.commit()
    log.info("Database initialised at %s", DB_PATH)


def is_processed(reel_id: str) -> bool:
    with contextlib.closing(_connect()) as conn:
        row = conn.execute(
            "SELECT status FROM reels WHERE reel_id = ?", (reel_id,)
        ).fetchone()
    return row is not None and row["status"] == "done"


def mark_pending(reel_id: str, url: str, title: str = "") -> None:
    now = datetime.utcnow().isoformat()
    with contextlib.closing(_connect()) as conn:
        conn.execute(
            """INSERT OR IGNORE INTO reels (reel_id, url, title, status, created_at, updated_at)
               VALUES (?, ?, ?, 'pending', ?, ?)""",
            (reel_id, url, title, now, now),
        )
        conn.commit()


def mark_done(reel_id: str) -> None:
    _update_status(reel_id, "done")


def mark_failed(reel_id: str) -> None:
    _update_status(reel_id, "failed")


def _update_status(reel_id: str, status: str) -> None:
    now = datetime.utcnow().isoformat()
    with contextlib.closing(_connect()) as conn:
        conn.execute(
            "UPDATE reels SET status = ?, updated_at = ? WHERE reel_id = ?",
            (status, now, reel_id),
        )
        conn.commit()
    log.debug("Reel %s → %s", reel_id, status)
