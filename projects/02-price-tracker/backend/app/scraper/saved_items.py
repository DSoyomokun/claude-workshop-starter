import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.scraper.base import ScraperStrategy
from app.models import ScrapeResult

logger = logging.getLogger(__name__)

GRAILED_FAVORITES_URL = "https://www.grailed.com/sold_items?tab=favorites"

# ── Selectors ──────────────────────────────────────────────────────────────────
# NOTE: verify with Playwright MCP — open the hearted/saved items page while
# logged in and find the listing card link selector.
# ──────────────────────────────────────────────────────────────────────────────
SAVED_CARD_SELECTORS = [
    'a[href*="/listings/"]',
    '[data-testid="listing-card"] a',
    '.feed-item a[href*="/listings/"]',
]


class SavedItemsStrategy(ScraperStrategy):
    def __init__(self, session_path: str):
        self.session_path = session_path

    async def scrape(self, url: str) -> ScrapeResult:
        raise NotImplementedError("Use extract_saved_urls to get listing URLs from saved items")

    async def extract_saved_urls(self) -> list[str]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(storage_state=self.session_path)
                page = await context.new_page()
                await page.goto(GRAILED_FAVORITES_URL, timeout=30_000, wait_until="domcontentloaded")

                urls: list[str] = []
                for selector in SAVED_CARD_SELECTORS:
                    try:
                        await page.wait_for_selector(selector, timeout=5_000)
                        elements = await page.query_selector_all(selector)
                        for el in elements:
                            href = await el.get_attribute("href")
                            if href and "/listings/" in href:
                                full = href if href.startswith("http") else f"https://www.grailed.com{href}"
                                if full not in urls:
                                    urls.append(full)
                        if urls:
                            break
                    except PlaywrightTimeoutError:
                        continue

                await browser.close()
                logger.info("Found %d saved listings", len(urls))
                return urls

        except PlaywrightTimeoutError as e:
            logger.error("Timeout loading saved items page: %s", e)
            raise
        except Exception as e:
            logger.exception("Unexpected error loading saved items")
            return []
