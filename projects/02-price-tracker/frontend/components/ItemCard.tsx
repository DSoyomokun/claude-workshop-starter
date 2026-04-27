"use client";
import { useState } from "react";
import { Item, PricePoint } from "@/lib/types";
import { Sparkline } from "./Sparkline";
import { ItemDetail } from "./ItemDetail";

function dropPct(item: Item) {
  if (!item.first_price || !item.latest_price) return null;
  const pct = ((item.first_price - item.latest_price) / item.first_price) * 100;
  return pct >= 10 ? pct : null;
}

export function ItemCard({
  item,
  history,
  onRefresh,
}: {
  item: Item;
  history: PricePoint[];
  onRefresh: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const sold = item.status === "sold";
  const drop = dropPct(item);

  async function handleRefresh(e: React.MouseEvent) {
    e.stopPropagation();
    setRefreshing(true);
    await onRefresh();
    setRefreshing(false);
  }

  return (
    <>
      <div
        onClick={() => setOpen(true)}
        className={`bg-[#141414] border border-[#2a2a2a] rounded-lg overflow-hidden cursor-pointer hover:border-[#444] transition-colors ${sold ? "opacity-60" : ""}`}
      >
        {/* Image */}
        <div className="relative aspect-square bg-[#1f1f1f]">
          {item.image_url ? (
            <img
              src={item.image_url}
              alt={item.title ?? ""}
              className={`w-full h-full object-cover ${sold ? "grayscale" : ""}`}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-[#444] text-xs">No image</div>
          )}
          {sold && (
            <span className="absolute top-2 right-2 bg-[#ef4444] text-white text-xs font-bold px-2 py-0.5 rounded-full">
              SOLD
            </span>
          )}
        </div>

        {/* Info */}
        <div className="p-3 space-y-2">
          <p className="text-[#f5f5f5] text-sm font-medium truncate">{item.title ?? "Loading…"}</p>

          <div className="flex items-center justify-between">
            <span className="text-[#f5f5f5] text-lg font-bold">
              {item.latest_price != null ? `$${item.latest_price}` : "—"}
            </span>
            {drop != null && (
              <span className="bg-[#22c55e] text-white text-xs font-bold px-2 py-0.5 rounded-full">
                ↓ {drop.toFixed(0)}%
              </span>
            )}
          </div>

          <Sparkline history={history} />

          <div className="flex justify-end">
            <button
              onClick={handleRefresh}
              className="text-[#888] hover:text-[#f5f5f5] text-xs transition-colors"
            >
              {refreshing ? "↺ …" : "↺ Refresh"}
            </button>
          </div>
        </div>
      </div>

      {open && (
        <ItemDetail item={item} history={history} onClose={() => setOpen(false)} onRefresh={onRefresh} />
      )}
    </>
  );
}
