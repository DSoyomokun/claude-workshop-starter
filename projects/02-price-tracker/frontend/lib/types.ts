export type ItemStatus = "active" | "sold" | "removed";

export interface Item {
  id: number;
  url: string;
  title: string | null;
  image_url: string | null;
  status: ItemStatus;
  sold_at: string | null;
  created_at: string;
  latest_price: number | null;
  first_price: number | null;
}

export interface PricePoint {
  id: number;
  item_id: number;
  price: number;
  scraped_at: string;
}

export interface AuthStatus {
  logged_in: boolean;
  username: string | null;
}
