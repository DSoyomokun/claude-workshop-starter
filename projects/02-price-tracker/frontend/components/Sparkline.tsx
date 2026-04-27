"use client";
import { LineChart, Line, ResponsiveContainer } from "recharts";
import { PricePoint } from "@/lib/types";

export function Sparkline({ history }: { history: PricePoint[] }) {
  if (history.length < 2) return null;
  const data = history.slice(-10).map((p) => ({ price: p.price }));
  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={data}>
        <Line type="monotone" dataKey="price" stroke="#e8ff00" dot={false} strokeWidth={1.5} />
      </LineChart>
    </ResponsiveContainer>
  );
}
