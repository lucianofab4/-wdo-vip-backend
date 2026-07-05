import type { Signal } from "@/lib/api";

const STATUS_STYLE: Record<string, string> = {
  win: "text-green-400 bg-green-400/10",
  loss: "text-red-400 bg-red-400/10",
  pending: "text-yellow-400 bg-yellow-400/10",
  cancelled: "text-gray-500 bg-gray-500/10",
};

const GAME_EMOJI: Record<string, string> = {
  bacbo: "🎴",
  dadinho: "🎲",
  crash: "🚀",
};

export default function SignalTable({ signals }: { signals: Signal[] }) {
  if (!signals.length) {
    return <p className="text-gray-500 text-sm">Nenhum sinal encontrado.</p>;
  }
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-900 text-gray-400 text-left">
            <th className="px-4 py-3">Jogo</th>
            <th className="px-4 py-3">Entrada</th>
            <th className="px-4 py-3">Estratégia</th>
            <th className="px-4 py-3">Gale</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Horário</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((s) => (
            <tr key={s.id} className="border-t border-gray-800 hover:bg-gray-900/50 transition-colors">
              <td className="px-4 py-3">
                {GAME_EMOJI[s.game] ?? "🎯"}{" "}
                <span className="text-gray-300 capitalize">{s.game}</span>
              </td>
              <td className="px-4 py-3 font-semibold text-white">{s.entry}</td>
              <td className="px-4 py-3 text-gray-400">{s.strategy}</td>
              <td className="px-4 py-3 text-gray-400">{s.gale_level}</td>
              <td className="px-4 py-3">
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    STATUS_STYLE[s.status] ?? "text-gray-400"
                  }`}
                >
                  {s.status.toUpperCase()}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-500 text-xs">
                {new Date(s.created_at).toLocaleString("pt-BR")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
