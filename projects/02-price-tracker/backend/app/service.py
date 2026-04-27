import os
import logging
from dotenv import load_dotenv

from app.models import ScrapeResult, ItemResponse, PricePoint, RefreshResult
from app.repository import PriceRepository
from app.scraper.listing import ListingStrategy
from app.scraper.brand_page import BrandPageStrategy
from app.scraper.saved_items import SavedItemsStrategy

load_dotenv()

SESSION_PATH = os.environ.get("SESSION_PATH", "grailed_session.json")

logger = logging.getLogger(__name__)


class PriceService:
    def __init__(self):
        self.repo = PriceRepository()

    def _listing_strategy(self) -> ListingStrategy:
        from pathlib import Path
        session = SESSION_PATH if Path(SESSION_PATH).exists() else None
        return ListingStrategy(session_path=session)

    async def add_item(self, url: str) -> ItemResponse:
        strategy = self._listing_strategy()
        result = await strategy.scrape(url)
        item_id = self.repo.upsert_item(result)
        if result.price is not None:
            self.repo.save_price(item_id, result.price)
        if result.status == "sold":
            self.repo.mark_sold(item_id)
        return self.repo.get_item_by_id(item_id)

    async def add_bulk(self, urls: list[str]) -> list[ItemResponse]:
        items = []
        for url in urls:
            try:
                item = await self.add_item(url)
                items.append(item)
            except Exception as e:
                logger.error("Failed to add item %s: %s", url, e)
        return items

    async def add_from_brand_page(self, url: str) -> list[ItemResponse]:
        strategy = BrandPageStrategy()
        urls = await strategy.extract_listing_urls(url)
        return await self.add_bulk(urls)

    async def add_from_saved_items(self) -> list[ItemResponse]:
        from pathlib import Path
        if not Path(SESSION_PATH).exists():
            raise RuntimeError("Not logged in — call /auth/login first")
        strategy = SavedItemsStrategy(session_path=SESSION_PATH)
        urls = await strategy.extract_saved_urls()
        return await self.add_bulk(urls)

    async def refresh_item(self, item_id: int) -> RefreshResult:
        item = self.repo.get_item_by_id(item_id)
        if not item:
            return RefreshResult(id=item_id, success=False, error="Item not found")

        try:
            strategy = self._listing_strategy()
            result = await strategy.scrape(item.url)

            if result.status == "sold" and item.status == "active":
                self.repo.mark_sold(item_id)
                return RefreshResult(id=item_id, success=True, error="Listing marked as sold")

            if result.price is not None:
                self.repo.save_price(item_id, result.price)
                return RefreshResult(id=item_id, success=True, price=result.price)

            return RefreshResult(id=item_id, success=False, error=result.error or "No price found")

        except Exception as e:
            logger.error("Refresh failed for item %d: %s", item_id, e)
            return RefreshResult(id=item_id, success=False, error=str(e))

    async def refresh_all(self) -> list[RefreshResult]:
        items = self.repo.get_active_items()
        results = []
        for item in items:
            result = await self.refresh_item(item.id)
            results.append(result)
        return results

    def get_items(self) -> list[ItemResponse]:
        return self.repo.get_all_items()

    def get_history(self, item_id: int) -> list[PricePoint]:
        return self.repo.get_price_history(item_id)
