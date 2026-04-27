"use client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot,
} from "recharts";
import { PricePoint } from "@/lib/types";

function fmt(date: string) {
  return new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function PriceChart({ history, sold }: { history: PricePoint[]; sold: boolean }) {
  if (history.length === 0) return <p className="text-[#888] text-sm">No price data yet.</p>;
  if (history.length === 1)
    return <p className="text-[#888] text-sm">Check back after the next refresh to see price history.</p>;

  const data = history.map((p) => ({ date: fmt(p.scraped_at), price: p.price }));
  const last = data[data.length - 1];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
        <XAxis dataKey="date" tick={{ fill: "#888", fontSize: 11 }} />
        <YAxis
          tickFormatter={(v) => `$${v}`}
          tick={{ fill: "#888", fontSize: 11 }}
          width={55}
        />
        <Tooltip
          formatter={(v) => [`$${v}`, "Price"]}
          contentStyle={{ background: "#141414", border: "1px solid #2a2a2a", color: "#f5f5f5" }}
        />
        <Line type="monotone" dataKey="price" stroke="#e8ff00" dot={{ fill: "#e8ff00", r: 3 }} strokeWidth={2} />
        {sold && (
          <ReferenceDot x={last.date} y={last.price} r={5} fill="#ef4444" stroke="none" label={{ value: "SOLD", fill: "#ef4444", fontSize: 11 }} />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
