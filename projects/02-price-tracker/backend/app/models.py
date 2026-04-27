from pydantic import BaseModel
from typing import Optional


class AddItemRequest(BaseModel):
    url: str


class BulkAddRequest(BaseModel):
    urls: list[str]


class PricePoint(BaseModel):
    id: int
    item_id: int
    price: float
    scraped_at: str


class ItemResponse(BaseModel):
    id: int
    url: str
    title: Optional[str]
    image_url: Optional[str]
    status: str
    sold_at: Optional[str]
    created_at: str
    latest_price: Optional[float]
    first_price: Optional[float]


class ItemDetailResponse(ItemResponse):
    history: list[PricePoint]


class ScrapeResult(BaseModel):
    url: str
    title: Optional[str]
    image_url: Optional[str]
    price: Optional[float]
    status: str = "active"
    error: Optional[str] = None


class AuthStatusResponse(BaseModel):
    logged_in: bool
    username: Optional[str] = None


class RefreshResult(BaseModel):
    id: int
    success: bool
    price: Optional[float] = None
    error: Optional[str] = None
