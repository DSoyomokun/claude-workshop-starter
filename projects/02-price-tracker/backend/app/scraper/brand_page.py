import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.models import ScrapeResult
from app.scraper.base import ScraperStrategy

logger = logging.getLogger(__name__)

# Verified against live Grailed brand page via Playwright inspection
LISTING_CARD_SELECTOR = "a.UserItem_link__kgEWg"  # 44 results on Jordan Brand page


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
                try:
                    await page.wait_for_selector(LISTING_CARD_SELECTOR, timeout=8_000)
                    elements = await page.query_selector_all(LISTING_CARD_SELECTOR)
                    for el in elements:
                        href = await el.get_attribute("href")
                        if href and "/listings/" in href:
                            # Strip Algolia query params, keep clean URL
                            clean = href.split("?")[0]
                            full = clean if clean.startswith("http") else f"https://www.grailed.com{clean}"
                            if full not in urls:
                                urls.append(full)
                except PlaywrightTimeoutError:
                    # Fall back to any listing link on the page
                    elements = await page.query_selector_all('a[href*="/listings/"]')
                    for el in elements:
                        href = await el.get_attribute("href")
                        if href:
                            clean = href.split("?")[0]
                            full = clean if clean.startswith("http") else f"https://www.grailed.com{clean}"
                            if full not in urls:
                                urls.append(full)

                await browser.close()
                logger.info("Found %d listings on brand page %s", len(urls), url)
                return urls

        except PlaywrightTimeoutError as e:
            logger.error("Timeout loading brand page %s: %s", url, e)
            raise
        except Exception as e:
            logger.exception("Unexpected error on brand page %s", url)
            return []
