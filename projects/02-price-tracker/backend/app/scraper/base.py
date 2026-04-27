import re
import logging
from abc import ABC, abstractmethod
from playwright.async_api import Page

from app.models import ScrapeResult

logger = logging.getLogger(__name__)

CURRENCY_RE = re.compile(r"\$\s*([\d,]+(?:\.\d{1,2})?)")


class ScraperStrategy(ABC):
    @abstractmethod
    async def scrape(self, url: str) -> ScrapeResult:
        ...

    async def _extract_price_fallback(self, page: Page) -> float | None:
        """Try og meta tags, then currency regex near a heading."""
        # og:price:amount / product:price:amount
        for prop in ("og:price:amount", "product:price:amount"):
            val = await page.get_attribute(f'meta[property="{prop}"]', "content")
            if val:
                try:
                    return float(val.replace(",", ""))
                except ValueError:
                    pass

        # Currency regex near headings
        headings = await page.query_selector_all("h1, h2, h3")
        for heading in headings:
            parent = await heading.evaluate_handle("el => el.parentElement")
            text = await parent.evaluate("el => el.innerText")
            match = CURRENCY_RE.search(text)
            if match:
                try:
                    return float(match.group(1).replace(",", ""))
                except ValueError:
                    pass

        return None
