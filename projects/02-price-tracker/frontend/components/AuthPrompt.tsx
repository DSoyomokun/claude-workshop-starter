"use client";
import { useState } from "react";
import { api } from "@/lib/api";

export function AuthPrompt({ onConnected }: { onConnected: () => void }) {
  const [status, setStatus] = useState<"idle" | "connecting">("idle");

  async function handleConnect() {
    setStatus("connecting");
    try {
      await api.triggerLogin();
      onConnected();
    } catch {
      setStatus("idle");
    }
  }

  return (
    <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
      <p className="text-[#f5f5f5] text-lg font-semibold">Connect your Grailed account</p>
      <p className="text-[#888] text-sm max-w-sm">
        We&apos;ll open a browser window so you can log in. Your session is saved locally — we never store your credentials.
      </p>
      <button
        onClick={handleConnect}
        disabled={status === "connecting"}
        className="bg-[#e8ff00] text-black font-bold px-6 py-2 rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
      >
        {status === "connecting" ? "Opening browser… log in and close when done" : "Connect Grailed Account"}
      </button>
    </div>
  );
}
