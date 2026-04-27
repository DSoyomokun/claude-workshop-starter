"use client";
import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { Item, PricePoint, AuthStatus } from "@/lib/types";
import { ItemCard } from "@/components/ItemCard";
import { AuthPrompt } from "@/components/AuthPrompt";

type Tab = "single" | "brand" | "saved";

const TAB_LABELS: Record<Tab, string> = {
  single: "SINGLE LISTING",
  brand: "BRAND PAGE",
  saved: "MY SAVED ITEMS",
};

const TAB_PLACEHOLDERS: Record<Tab, string> = {
  single: "https://www.grailed.com/listings/…",
  brand: "https://www.grailed.com/designers/…",
  saved: "",
};

export default function Home() {
  const [tab, setTab] = useState<Tab>("single");
  const [url, setUrl] = useState("");
  const [items, setItems] = useState<Item[]>([]);
  const [histories, setHistories] = useState<Record<number, PricePoint[]>>({});
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshingAll, setRefreshingAll] = useState(false);

  const loadItems = useCallback(async () => {
    const data = await api.getItems();
    setItems(data);
    const entries = await Promise.all(
      data.map(async (item) => [item.id, await api.getHistory(item.id)] as const)
    );
    setHistories(Object.fromEntries(entries));
  }, []);

  useEffect(() => {
    loadItems();
    api.getAuthStatus().then(setAuth);
  }, [loadItems]);

  async function handleTrack() {
    if (!url.trim()) return;
    setLoading(true);
    try {
      if (tab === "single") await api.addItem(url.trim());
      else if (tab === "brand") await api.importBrandPage(url.trim());
      setUrl("");
      await loadItems();
    } catch (e) {
      alert(`Failed: ${e instanceof Error ? e.message : e}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleImportSaved() {
    setLoading(true);
    try {
      await api.importSaved();
      await loadItems();
    } catch (e) {
      alert(`Failed: ${e instanceof Error ? e.message : e}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefreshAll() {
    setRefreshingAll(true);
    await api.refreshAll();
    await loadItems();
    setRefreshingAll(false);
  }

  async function handleRefreshItem(id: number) {
    await api.refreshItem(id);
    await loadItems();
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#f5f5f5]">
      {/* Top bar */}
      <header className="sticky top-0 z-40 bg-[#0a0a0a] border-b border-[#2a2a2a] px-6 py-4 flex justify-between items-center">
        <span className="font-bold tracking-widest text-sm uppercase">Grailed Tracker</span>
        <button
          onClick={handleRefreshAll}
          disabled={refreshingAll}
          className="border border-[#2a2a2a] text-[#888] hover:text-[#f5f5f5] hover:border-[#444] text-xs px-4 py-1.5 rounded transition-colors disabled:opacity-40"
        >
          {refreshingAll ? `Refreshing ${items.length} items…` : "Refresh All"}
        </button>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 space-y-8">
        {/* Tabs */}
        <div className="flex gap-6 border-b border-[#2a2a2a]">
          {(["single", "brand", "saved"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`pb-3 text-xs font-bold tracking-wider uppercase transition-colors ${
                tab === t
                  ? "text-[#f5f5f5] border-b-2 border-[#e8ff00]"
                  : "text-[#888] hover:text-[#f5f5f5]"
              }`}
            >
              {TAB_LABELS[t]}
            </button>
          ))}
        </div>

        {/* Input area */}
        {tab === "saved" ? (
          auth?.logged_in ? (
            <div className="flex items-center gap-3">
              <span className="text-[#888] text-sm">Logged in as @{auth.username}</span>
              <button
                onClick={handleImportSaved}
                disabled={loading}
                className="bg-[#e8ff00] text-black font-bold px-5 py-2 rounded-lg text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {loading ? "Importing…" : "Import Saved Items"}
              </button>
            </div>
          ) : (
            <AuthPrompt onConnected={() => api.getAuthStatus().then(setAuth)} />
          )
        ) : (
          <div className="flex gap-3">
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleTrack()}
              placeholder={TAB_PLACEHOLDERS[tab]}
              className="flex-1 bg-[#141414] border border-[#2a2a2a] rounded-lg px-4 py-2.5 text-sm text-[#f5f5f5] placeholder-[#444] focus:outline-none focus:border-[#444]"
            />
            <button
              onClick={handleTrack}
              disabled={loading || !url.trim()}
              className="bg-[#e8ff00] text-black font-bold px-6 py-2.5 rounded-lg text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {loading ? "Tracking…" : "TRACK"}
            </button>
          </div>
        )}

        {/* Item grid */}
        {items.length === 0 ? (
          <div className="text-center py-20 text-[#444]">
            No items tracked yet. Paste a URL above to start.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((item) => (
              <ItemCard
                key={item.id}
                item={item}
                history={histories[item.id] ?? []}
                onRefresh={() => handleRefreshItem(item.id)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
