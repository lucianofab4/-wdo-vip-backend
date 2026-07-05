"use client";
import { useEffect, useState } from "react";
import { fetchStrategies, toggleGame } from "@/lib/api";
import type { StrategyConfig } from "@/lib/api";
import StrategyToggle from "@/components/StrategyToggle";

const GAMES = [
  { key: "bacbo", label: "Bac Bo", emoji: "🎴" },
  { key: "dadinho", label: "Dadinho", emoji: "🎲" },
  { key: "crash", label: "Crash", emoji: "🚀" },
];

export default function SettingsPage() {
  const [strategies, setStrategies] = useState<StrategyConfig[]>([]);
  const [gameEnabled, setGameEnabled] = useState<Record<string, boolean>>({
    bacbo: true,
    dadinho: true,
    crash: true,
  });
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    fetchStrategies().then(setStrategies);
  }, []);

  function handleStrategyUpdate(updated: StrategyConfig) {
    setStrategies((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
  }

  async function handleGameToggle(game: string, enabled: boolean) {
    setSaving(game);
    try {
      await toggleGame(game, enabled);
      setGameEnabled((prev) => ({ ...prev, [game]: enabled }));
    } finally {
      setSaving(null);
    }
  }

  const byGame = GAMES.map((g) => ({
    ...g,
    strategies: strategies.filter((s) => s.game === g.key),
  }));

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Configurações</h1>

      {/* ─── Checkbox de Jogos ─── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-4 text-gray-200">Jogos Ativos</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-2xl divide-y divide-gray-800">
          {GAMES.map((g) => (
            <div key={g.key} className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-3">
                <span className="text-xl">{g.emoji}</span>
                <div>
                  <p className="font-medium text-gray-100">{g.label}</p>
                  <p className="text-xs text-gray-500">
                    {gameEnabled[g.key] ? "Monitorando" : "Pausado"}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleGameToggle(g.key, !gameEnabled[g.key])}
                disabled={saving === g.key}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  gameEnabled[g.key] ? "bg-indigo-600" : "bg-gray-700"
                } ${saving === g.key ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                    gameEnabled[g.key] ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Estratégias por jogo ─── */}
      {byGame.map(
        (g) =>
          g.strategies.length > 0 && (
            <section key={g.key} className="mb-6">
              <h2 className="text-base font-semibold mb-3 text-gray-300 flex items-center gap-2">
                <span>{g.emoji}</span> {g.label} — Estratégias
              </h2>
              <div className="bg-gray-900 border border-gray-800 rounded-2xl divide-y divide-gray-800">
                {g.strategies.map((s) => (
                  <div key={s.id} className="flex items-center justify-between px-5 py-4">
                    <div>
                      <p className="font-medium text-gray-100 capitalize">{s.strategy}</p>
                      <p className="text-xs text-gray-500">
                        {JSON.stringify(s.config)
                          .replace(/[{}"]/g, "")
                          .replace(/,/g, " · ")}
                      </p>
                    </div>
                    <StrategyToggle config={s} onUpdate={handleStrategyUpdate} />
                  </div>
                ))}
              </div>
            </section>
          )
      )}
    </div>
  );
}
