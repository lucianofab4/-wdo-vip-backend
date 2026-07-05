"use client";
import { useState } from "react";
import { toggleStrategy } from "@/lib/api";
import type { StrategyConfig } from "@/lib/api";

export default function StrategyToggle({
  config,
  onUpdate,
}: {
  config: StrategyConfig;
  onUpdate: (updated: StrategyConfig) => void;
}) {
  const [loading, setLoading] = useState(false);

  async function handleToggle() {
    setLoading(true);
    try {
      const updated = await toggleStrategy(config.game, config.strategy, !config.is_active);
      onUpdate(updated);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleToggle}
      disabled={loading}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
        config.is_active ? "bg-indigo-600" : "bg-gray-700"
      } ${loading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
          config.is_active ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}
