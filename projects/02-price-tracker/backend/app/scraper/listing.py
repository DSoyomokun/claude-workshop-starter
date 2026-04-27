import re
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.models import ScrapeResult
from app.scraper.base import ScraperStrategy

logger = logging.getLogger(__name__)


SOLD_INDICATORS = [
    'button:has-text("Sold")',
    '[class*="sold"]',
    'span:has-text("This listing has sold")',
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class ListingStrategy(ScraperStrategy):
    def __init__(self, session_path: str | None = None):
        self.session_path = session_path

    async def scrape(self, url: str) -> ScrapeResult:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx_opts: dict = {"user_agent": USER_AGENT}
                if self.session_path:
                    ctx_opts["storage_state"] = self.session_path
                context = await browser.new_context(**ctx_opts)
                page = await context.new_page()

                response = await page.goto(url, timeout=30_000, wait_until="domcontentloaded")

                if response and response.status == 404:
                    await browser.close()
                    return ScrapeResult(url=url, status="sold", error="404 — listing not found")

                await page.wait_for_timeout(2000)

                # Check sold indicators before extracting data
                for selector in SOLD_INDICATORS:
                    try:
                        el = await page.wait_for_selector(selector, timeout=1_500)
                        if el:
                            title, image_url = await self._get_meta(page)
                            await browser.close()
                            return ScrapeResult(url=url, title=title, image_url=image_url, status="sold")
                    except PlaywrightTimeoutError:
                        pass

                title, image_url = await self._get_meta(page)
                price = await self._get_price(page)

                await browser.close()

                if price is None:
                    return ScrapeResult(
                        url=url, title=title, image_url=image_url,
                        status="active", error="Price not found",
                    )

                return ScrapeResult(url=url, title=title, image_url=image_url, price=price, status="active")

        except PlaywrightTimeoutError as e:
            logger.error("Timeout scraping listing %s: %s", url, e)
            raise
        except Exception as e:
            logger.exception("Unexpected error scraping listing %s", url)
            return ScrapeResult(url=url, status="active", error=str(e))

    async def _get_meta(self, page) -> tuple[str | None, str | None]:
        """Extract title and image from og meta tags — most reliable on Grailed."""
        title = await page.get_attribute('meta[property="og:title"]', "content")
        if title:
            title = title.replace(" | Grailed", "").strip()
        image_url = await page.get_attribute('meta[property="og:image"]', "content")
        return title or None, image_url or None

    async def _get_price(self, page) -> float | None:
        # JSON-LD is the only reliable price source on Grailed listing pages.
        # All span[data-testid="Current"] elements belong to the similar-listings carousel.
        price = await page.evaluate("""
            () => {
                const scripts = [...document.querySelectorAll('script[type="application/ld+json"]')];
                for (const s of scripts) {
                    try {
                        const data = JSON.parse(s.textContent);
                        if (data['@type'] === 'Product' && data.offers?.price) {
                            return parseFloat(data.offers.price);
                        }
                    } catch {}
                }
                return null;
            }
        """)
        if price is not None:
            return float(price)
        return await self._extract_price_fallback(page)
