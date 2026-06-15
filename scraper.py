"""
Facebook Reels scraper using Playwright.

IMPORTANT – Legal notice
------------------------
This scraper only reads publicly visible reel URLs from a public Facebook page.
It does NOT log in, bypass authentication, circumvent rate-limits, or defeat any
DRM / security system.  You are solely responsible for ensuring you have the
legal right to access and redistribute any content you process.
"""
import asyncio
import re
from typing import List, Dict
from playwright.async_api import async_playwright, Page, BrowserContext
from config import (
    FACEBOOK_REELS_URL,
    PLAYWRIGHT_HEADLESS,
    PAGE_LOAD_TIMEOUT,
    SCROLL_PAUSE,
    MAX_SCROLL_ROUNDS,
)
from logger import get_logger

log = get_logger("scraper")

# Matches /reel/123456789 (with or without trailing slash or query string)
_REEL_RE = re.compile(r"facebook\.com/reel/(\d{7,})")


async def _scroll_and_collect(page: Page) -> List[Dict]:
    """Scroll the reels page and harvest reel URLs."""
    seen: set[str] = set()
    reels: List[Dict] = []

    for round_ in range(MAX_SCROLL_ROUNDS):
        # collect all <a> hrefs visible now
        links = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.href)",
        )
        for href in links:
            m = _REEL_RE.search(href)
            if m:
                reel_id = m.group(1)
                if reel_id not in seen:
                    seen.add(reel_id)
                    # normalise to canonical reel URL
                    canonical = f"https://www.facebook.com/reel/{reel_id}/"
                    reels.append({"reel_id": reel_id, "url": canonical, "title": ""})

        log.debug("Scroll round %d – total reels found so far: %d", round_ + 1, len(reels))

        prev_height: int = await page.evaluate("document.body.scrollHeight")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(SCROLL_PAUSE)
        new_height: int = await page.evaluate("document.body.scrollHeight")

        if new_height == prev_height:
            log.debug("No more content to scroll.")
            break

    return reels


async def fetch_reels() -> List[Dict]:
    """
    Returns a list of dicts: [{reel_id, url, title}, …]
    Only public content – no authentication used.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
        ctx: BrowserContext = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page: Page = await ctx.new_page()
        try:
            log.info("Opening %s", FACEBOOK_REELS_URL)
            await page.goto(FACEBOOK_REELS_URL, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
            await asyncio.sleep(3)

            # dismiss cookie / login wall if present
            for selector in (
                '[data-testid="cookie-policy-manage-dialog-accept-button"]',
                'div[aria-label="Allow all cookies"]',
                'button:has-text("Accept All")',
                'button:has-text("Allow essential and optional cookies")',
                'div[aria-label="Close"]',
            ):
                try:
                    btn = page.locator(selector)
                    if await btn.count() > 0:
                        await btn.first.click(timeout=3000)
                        log.debug("Dismissed overlay: %s", selector)
                        await asyncio.sleep(1)
                        break
                except Exception:
                    pass

            # if redirected to login page, go directly to reels tab
            current_url = page.url
            if "login" in current_url or "checkpoint" in current_url:
                log.warning("Redirected to login page, trying direct reels tab URL")
                await page.goto(
                    f"{FACEBOOK_REELS_URL.rstrip('/')}",
                    timeout=PAGE_LOAD_TIMEOUT,
                    wait_until="domcontentloaded",
                )
                await asyncio.sleep(3)

            reels = await _scroll_and_collect(page)
            log.info("Scraped %d reel(s) from the page.", len(reels))
            return reels
        except Exception as exc:
            log.error("Scraper error: %s", exc, exc_info=True)
            return []
        finally:
            await browser.close()
