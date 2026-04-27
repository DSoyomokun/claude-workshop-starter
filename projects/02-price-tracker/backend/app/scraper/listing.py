import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.models import ScrapeResult
from app.scraper.base import ScraperStrategy

logger = logging.getLogger(__name__)

# ── Selectors ──────────────────────────────────────────────────────────────────
# NOTE: these must be verified / replaced using the Playwright MCP before this
# code ships. Run: "Use the playwright MCP to open a real Grailed listing URL,
# find the price/title/image elements, and give me stable CSS selectors."
# ──────────────────────────────────────────────────────────────────────────────
PRICE_SELECTORS = [
    '[data-testid="listing-price"]',
    ".listing-price",
    'p[class*="Price"]',
    'span[class*="price"]',
]

TITLE_SELECTORS = [
    '[data-testid="listing-title"]',
    'h1[class*="title"]',
    "h1",
]

IMAGE_SELECTORS = [
    '[data-testid="listing-cover-photo"] img',
    ".cover-photo img",
    'img[class*="cover"]',
    'img[class*="listing"]',
]

SOLD_INDICATORS = [
    '[data-testid="sold-badge"]',
    'span:text("Sold")',
    'div:text("This listing has been sold")',
]


class ListingStrategy(ScraperStrategy):
    def __init__(self, session_path: str | None = None):
        self.session_path = session_path

    async def scrape(self, url: str) -> ScrapeResult:
        from playwright.async_api import async_playwright

        try:
            async with async_playwright() as p:
                launch_opts = {"headless": True}
                browser = await p.chromium.launch(**launch_opts)
                ctx_opts = {}
                if self.session_path:
                    ctx_opts["storage_state"] = self.session_path
                context = await browser.new_context(**ctx_opts)
                page = await context.new_page()

                response = await page.goto(url, timeout=30_000, wait_until="domcontentloaded")

                # Treat hard redirects / 404s as sold/removed
                if response and response.status == 404:
                    await browser.close()
                    return ScrapeResult(url=url, status="sold", error="404 — listing not found")

                # Check for in-page sold indicators
                for selector in SOLD_INDICATORS:
                    try:
                        el = await page.wait_for_selector(selector, timeout=2_000)
                        if el:
                            title = await self._get_text(page, TITLE_SELECTORS)
                            image_url = await self._get_image(page)
                            await browser.close()
                            return ScrapeResult(url=url, title=title, image_url=image_url, status="sold")
                    except PlaywrightTimeoutError:
                        pass

                title = await self._get_text(page, TITLE_SELECTORS)
                image_url = await self._get_image(page)
                price = await self._get_price(page)

                await browser.close()

                if price is None:
                    return ScrapeResult(
                        url=url, title=title, image_url=image_url,
                        status="active", error="Price not found — selectors may need updating"
                    )

                return ScrapeResult(url=url, title=title, image_url=image_url, price=price, status="active")

        except PlaywrightTimeoutError as e:
            logger.error("Timeout scraping listing %s: %s", url, e)
            raise
        except Exception as e:
            logger.exception("Unexpected error scraping listing %s", url)
            return ScrapeResult(url=url, status="active", error=str(e))

    async def _get_price(self, page) -> float | None:
        import re
        for selector in PRICE_SELECTORS:
            try:
                el = await page.wait_for_selector(selector, timeout=3_000)
                if el:
                    text = await el.inner_text()
                    match = re.search(r"[\d,]+(?:\.\d{1,2})?", text.replace(",", ""))
                    if match:
                        return float(match.group().replace(",", ""))
            except PlaywrightTimeoutError:
                continue
        return await self._extract_price_fallback(page)

    async def _get_text(self, page, selectors: list[str]) -> str | None:
        for selector in selectors:
            try:
                el = await page.wait_for_selector(selector, timeout=2_000)
                if el:
                    return (await el.inner_text()).strip() or None
            except PlaywrightTimeoutError:
                continue
        return None

    async def _get_image(self, page) -> str | None:
        for selector in IMAGE_SELECTORS:
            try:
                el = await page.wait_for_selector(selector, timeout=2_000)
                if el:
                    src = await el.get_attribute("src")
                    if src:
                        return src
            except PlaywrightTimeoutError:
                continue
        return None
