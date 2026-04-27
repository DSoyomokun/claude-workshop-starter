from app.db import db
from app.models import ItemResponse, PricePoint, ScrapeResult
from typing import Optional


class PriceRepository:
    def upsert_item(self, result: ScrapeResult) -> int:
        with db() as conn:
            cur = conn.execute(
                """
                INSERT INTO items (url, title, image_url, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    image_url = excluded.image_url
                RETURNING id
                """,
                (result.url, result.title, result.image_url, result.status),
            )
            row = cur.fetchone()
            return row["id"]

    def mark_sold(self, item_id: int):
        with db() as conn:
            conn.execute(
                "UPDATE items SET status='sold', sold_at=datetime('now') WHERE id=?",
                (item_id,),
            )

    def save_price(self, item_id: int, price: float):
        with db() as conn:
            conn.execute(
                "INSERT INTO price_history (item_id, price) VALUES (?, ?)",
                (item_id, price),
            )

    def get_all_items(self) -> list[ItemResponse]:
        with db() as conn:
            rows = conn.execute(
                """
                SELECT
                    i.*,
                    (SELECT price FROM price_history WHERE item_id=i.id ORDER BY scraped_at DESC LIMIT 1) AS latest_price,
                    (SELECT price FROM price_history WHERE item_id=i.id ORDER BY scraped_at ASC  LIMIT 1) AS first_price
                FROM items i
                ORDER BY i.created_at DESC
                """
            ).fetchall()
            return [ItemResponse(**dict(r)) for r in rows]

    def get_item_by_id(self, item_id: int) -> Optional[ItemResponse]:
        with db() as conn:
            row = conn.execute(
                """
                SELECT
                    i.*,
                    (SELECT price FROM price_history WHERE item_id=i.id ORDER BY scraped_at DESC LIMIT 1) AS latest_price,
                    (SELECT price FROM price_history WHERE item_id=i.id ORDER BY scraped_at ASC  LIMIT 1) AS first_price
                FROM items i WHERE i.id=?
                """,
                (item_id,),
            ).fetchone()
            return ItemResponse(**dict(row)) if row else None

    def get_item_by_url(self, url: str) -> Optional[ItemResponse]:
        with db() as conn:
            row = conn.execute(
                """
                SELECT
                    i.*,
                    (SELECT price FROM price_history WHERE item_id=i.id ORDER BY scraped_at DESC LIMIT 1) AS latest_price,
                    (SELECT price FROM price_history WHERE item_id=i.id ORDER BY scraped_at ASC  LIMIT 1) AS first_price
                FROM items i WHERE i.url=?
                """,
                (url,),
            ).fetchone()
            return ItemResponse(**dict(row)) if row else None

    def get_active_items(self) -> list[ItemResponse]:
        with db() as conn:
            rows = conn.execute(
                """
                SELECT
                    i.*,
                    (SELECT price FROM price_history WHERE item_id=i.id ORDER BY scraped_at DESC LIMIT 1) AS latest_price,
                    (SELECT price FROM price_history WHERE item_id=i.id ORDER BY scraped_at ASC  LIMIT 1) AS first_price
                FROM items i WHERE i.status='active'
                """
            ).fetchall()
            return [ItemResponse(**dict(r)) for r in rows]

    def get_price_history(self, item_id: int) -> list[PricePoint]:
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM price_history WHERE item_id=? ORDER BY scraped_at ASC",
                (item_id,),
            ).fetchall()
            return [PricePoint(**dict(r)) for r in rows]
