import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.models import ScrapeResult
from app.scraper.base import ScraperStrategy

logger = logging.getLogger(__name__)

# ── Selectors ──────────────────────────────────────────────────────────────────
# NOTE: verify with Playwright MCP before shipping.
# Run: "Use the playwright MCP to open grailed.com/designers/[brand], find the
# listing card elements, and give me a stable CSS selector for each card's link."
# ──────────────────────────────────────────────────────────────────────────────
LISTING_CARD_SELECTORS = [
    'a[href*="/listings/"]',
    '[data-testid="listing-card"] a',
    '.listing-card a',
    'article a[href*="/listings/"]',
]


class BrandPageStrategy(ScraperStrategy):
    """Extracts all listing URLs from the first page of a brand/designer page."""

    async def scrape(self, url: str) -> ScrapeResult:
        # Not used directly — use extract_listing_urls instead
        raise NotImplementedError("Use extract_listing_urls for brand pages")

    async def extract_listing_urls(self, url: str) -> list[str]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto(url, timeout=30_000, wait_until="domcontentloaded")

                urls: list[str] = []
                for selector in LISTING_CARD_SELECTORS:
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
                logger.info("Found %d listings on brand page %s", len(urls), url)
                return urls

        except PlaywrightTimeoutError as e:
            logger.error("Timeout loading brand page %s: %s", url, e)
            raise
        except Exception as e:
            logger.exception("Unexpected error on brand page %s", url)
            return []
