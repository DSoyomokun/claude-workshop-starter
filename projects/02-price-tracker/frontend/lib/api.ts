import { Item, PricePoint, AuthStatus } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return res.json();
}

export const api = {
  getItems: () => request<Item[]>("/items"),
  addItem: (url: string) =>
    request<Item>("/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }),
  addBulk: (urls: string[]) =>
    request<Item[]>("/items/bulk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urls }),
    }),
  importBrandPage: (url: string) =>
    request<Item[]>("/items/import/brand-page", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }),
  importSaved: () =>
    request<Item[]>("/items/import/saved", { method: "POST" }),
  getHistory: (id: number) => request<PricePoint[]>(`/items/${id}/history`),
  refreshItem: (id: number) =>
    request(`/items/${id}/refresh`, { method: "POST" }),
  refreshAll: () => request("/refresh-all", { method: "POST" }),
  getAuthStatus: () => request<AuthStatus>("/auth/status"),
  triggerLogin: () =>
    request<AuthStatus>("/auth/login", { method: "POST" }),
};
