"use client";
import { useEffect, useState } from "react";
import { fetchSignals } from "@/lib/api";
import type { Signal } from "@/lib/api";
import SignalTable from "@/components/SignalTable";

const GAMES = [
  { key: "all", label: "Todos" },
  { key: "bacbo", label: "🎴 Bac Bo" },
  { key: "dadinho", label: "🎲 Dadinho" },
  { key: "crash", label: "🚀 Crash" },
];

const STATUSES = [
  { key: "all", label: "Todos" },
  { key: "win", label: "✅ Win" },
  { key: "loss", label: "❌ Loss" },
  { key: "pending", label: "⏳ Pendente" },
];

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [game, setGame] = useState("all");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchSignals(game === "all" ? undefined : game, status === "all" ? undefined : status)
      .then(setSignals)
      .finally(() => setLoading(false));
  }, [game, status]);

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Sinais</h1>

      <div className="flex flex-wrap gap-3 mb-6">
        <FilterGroup label="Jogo" options={GAMES} value={game} onChange={setGame} />
        <FilterGroup label="Status" options={STATUSES} value={status} onChange={setStatus} />
      </div>

      {loading ? (
        <p className="text-gray-500 text-sm">Carregando...</p>
      ) : (
        <SignalTable signals={signals} />
      )}
    </div>
  );
}

function FilterGroup({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { key: string; label: string }[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 font-medium">{label}:</span>
      {options.map((o) => (
        <button
          key={o.key}
          onClick={() => onChange(o.key)}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
            value === o.key
              ? "bg-indigo-600 text-white"
              : "bg-gray-800 text-gray-400 hover:bg-gray-700"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
