"use client";
import { Item, PricePoint } from "@/lib/types";
import { PriceChart } from "./PriceChart";

function dropPct(item: Item) {
  if (!item.first_price || !item.latest_price) return null;
  return ((item.first_price - item.latest_price) / item.first_price) * 100;
}

export function ItemDetail({
  item,
  history,
  onClose,
  onRefresh,
}: {
  item: Item;
  history: PricePoint[];
  onClose: () => void;
  onRefresh: () => void;
}) {
  const drop = dropPct(item);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70" onClick={onClose}>
      <div
        className="bg-[#141414] border border-[#2a2a2a] rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex justify-between items-start">
            <h2 className="text-[#f5f5f5] text-xl font-bold pr-4">{item.title ?? "Untitled"}</h2>
            <button onClick={onClose} className="text-[#888] hover:text-[#f5f5f5] text-xl leading-none">✕</button>
          </div>

          {/* Image + meta */}
          <div className="flex gap-6">
            {item.image_url && (
              <img
                src={item.image_url}
                alt={item.title ?? ""}
                className={`w-40 h-40 object-cover rounded-lg flex-shrink-0 ${item.status === "sold" ? "grayscale" : ""}`}
              />
            )}
            <div className="space-y-2 text-sm">
              <div className="flex items-baseline gap-3">
                <span className="text-[#f5f5f5] text-2xl font-bold">
                  {item.latest_price != null ? `$${item.latest_price}` : "—"}
                </span>
                {item.status === "sold" && (
                  <span className="bg-[#ef4444] text-white text-xs font-bold px-2 py-0.5 rounded-full">SOLD</span>
                )}
              </div>
              {item.first_price && (
                <p className="text-[#888]">First tracked: <span className="text-[#f5f5f5]">${item.first_price}</span></p>
              )}
              {drop != null && drop >= 10 && (
                <p className="text-[#22c55e] font-semibold">↓ {drop.toFixed(1)}% drop</p>
              )}
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#e8ff00] hover:underline"
              >
                View on Grailed ↗
              </a>
            </div>
          </div>

          {/* Chart */}
          <div>
            <p className="text-[#888] text-xs uppercase tracking-wider mb-3">Price History</p>
            <PriceChart history={history} sold={item.status === "sold"} />
          </div>

          {/* Refresh */}
          <div className="flex justify-end">
            <button
              onClick={onRefresh}
              className="text-sm text-[#888] hover:text-[#f5f5f5] transition-colors"
            >
              ↺ Refresh now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
