import type { Stats } from "@/lib/api";

const GAME_LABEL: Record<string, string> = {
  bacbo: "🎴 Bac Bo",
  dadinho: "🎲 Dadinho",
  crash: "🚀 Crash",
};

export default function StatsCard({ data }: { data: Stats }) {
  const label = GAME_LABEL[data.game] ?? data.game;
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col gap-3">
      <h3 className="text-base font-semibold text-gray-200">{label}</h3>
      <div className="grid grid-cols-3 gap-2 text-center">
        <Stat label="Total" value={data.total} color="text-gray-300" />
        <Stat label="Wins" value={data.wins} color="text-green-400" />
        <Stat label="Losses" value={data.losses} color="text-red-400" />
      </div>
      <div className="mt-1">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Taxa de acerto</span>
          <span className="font-medium text-gray-300">{data.win_rate.toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-500 rounded-full transition-all"
            style={{ width: `${Math.min(data.win_rate, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex flex-col">
      <span className={`text-xl font-bold ${color}`}>{value}</span>
      <span className="text-xs text-gray-500">{label}</span>
    </div>
  );
}
