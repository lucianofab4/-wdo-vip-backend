"use client";
import { useEffect, useState, useCallback, useRef } from "react";
import {
  fetchStats, fetchSignals, fetchUsers, fetchRequests,
  approveRequest, rejectRequest, removeUser, renewUser, checkHealth,
} from "@/lib/api";
import type { Stats, Signal, UsersStats, AccessRequest, TelegramUser } from "@/lib/api";
import {
  RefreshCw, Wifi, WifiOff, Clock, Users, Trophy,
  Target, AlertCircle, Check, X, UserX, Bell, RotateCcw, CalendarClock,
} from "lucide-react";

const REFRESH_INTERVAL = 10;

const ENTRY_STYLE: Record<string, string> = {
  PLAYER: "bg-blue-500/20 text-blue-300 border border-blue-500/30",
  BANKER: "bg-orange-500/20 text-orange-300 border border-orange-500/30",
  TIE:    "bg-purple-500/20 text-purple-300 border border-purple-500/30",
};

const STATUS_CFG: Record<string, { label: string; icon: string; row: string; badge: string }> = {
  win:       { label: "WIN",    icon: "✅", row: "bg-green-950/30 border-green-900/40",   badge: "text-green-400 bg-green-400/10 border border-green-500/20" },
  loss:      { label: "LOSS",   icon: "❌", row: "bg-red-950/30 border-red-900/40",       badge: "text-red-400 bg-red-400/10 border border-red-500/20" },
  pending:   { label: "AGUARD", icon: "⏳", row: "bg-yellow-950/20 border-yellow-900/30", badge: "text-yellow-400 bg-yellow-400/10 border border-yellow-500/20" },
  cancelled: { label: "CANC",   icon: "⛔", row: "bg-gray-900/40 border-gray-800/40",     badge: "text-gray-500 bg-gray-500/10 border border-gray-700/20" },
};

const GALE_LABEL = ["Direto", "Gale 1", "Gale 2"];
type SignalFilter = "all" | "win" | "loss" | "pending";

const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
const fmtDateFull = (iso: string) =>
  new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });

// ─── Win Rate Ring ───────────────────────────────────────────────────────────
function WinRateRing({ rate }: { rate: number }) {
  const r = 40, circ = 2 * Math.PI * r;
  const color = rate >= 80 ? "#4ade80" : rate >= 60 ? "#facc15" : "#f87171";
  return (
    <div className="relative w-24 h-24 flex-shrink-0">
      <svg width="96" height="96" className="-rotate-90">
        <circle cx="48" cy="48" r={r} fill="none" stroke="#1f2937" strokeWidth="9" />
        <circle cx="48" cy="48" r={r} fill="none" stroke={color} strokeWidth="9"
          strokeDasharray={`${(Math.min(rate,100)/100)*circ} ${circ}`} strokeLinecap="round"
          style={{ transition: "stroke-dasharray .8s ease" }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold" style={{ color }}>{rate.toFixed(0)}%</span>
        <span className="text-xs text-gray-500 mt-0.5">acerto</span>
      </div>
    </div>
  );
}

// ─── Stats Panel ─────────────────────────────────────────────────────────────
function StatsPainel({ data }: { data: Stats }) {
  const rate = data.win_rate;
  const rateColor = rate >= 80 ? "text-green-400" : rate >= 60 ? "text-yellow-400" : "text-red-400";
  const barColor  = rate >= 80 ? "bg-green-500"  : rate >= 60 ? "bg-yellow-500"  : "bg-red-500";
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-5">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xl font-bold mb-1">Bac Bo</div>
          <span className="text-xs text-green-400 bg-green-400/10 border border-green-500/20 px-2.5 py-0.5 rounded-full">
            Monitorando
          </span>
        </div>
        <WinRateRing rate={rate} />
      </div>

      <div className="grid grid-cols-4 gap-2">
        {[
          { label: "Total",     value: data.total,   icon: <Target size={13} />,      color: "text-gray-200" },
          { label: "Wins",      value: data.wins,    icon: <Trophy size={13} />,      color: "text-green-400" },
          { label: "Losses",    value: data.losses,  icon: <AlertCircle size={13} />, color: "text-red-400" },
          { label: "Pendentes", value: data.pending, icon: <Clock size={13} />,       color: "text-yellow-400" },
        ].map(({ label, value, icon, color }) => (
          <div key={label} className="bg-gray-800/50 border border-gray-700/30 rounded-xl p-3 text-center">
            <div className={`flex items-center justify-center gap-1 text-xs mb-1.5 ${color}`}>{icon} {label}</div>
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
          </div>
        ))}
      </div>

      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2.5">Vitorias por Gale</p>
        <div className="grid grid-cols-3 gap-2">
          {[
            { label: "Direto", value: data.wins_direct, color: "bg-emerald-500", text: "text-emerald-400" },
            { label: "Gale 1", value: data.wins_gale1,  color: "bg-indigo-500",  text: "text-indigo-400" },
            { label: "Gale 2", value: data.wins_gale2,  color: "bg-violet-500",  text: "text-violet-400" },
          ].map(({ label, value, color, text }) => {
            const pct = data.wins > 0 ? (value / data.wins) * 100 : 0;
            return (
              <div key={label} className="bg-gray-800/40 border border-gray-700/20 rounded-xl p-3">
                <div className={`text-xl font-bold ${text}`}>{value}</div>
                <div className="text-xs text-gray-400 mb-2">{label}</div>
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%`, transition: "width .7s ease" }} />
                </div>
                <div className="text-xs text-gray-600 mt-1">{pct.toFixed(0)}% dos wins</div>
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1.5">
          <span>Taxa de acerto geral</span>
          <span className={`font-semibold ${rateColor}`}>{rate.toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div className={`h-full ${barColor} rounded-full`}
            style={{ width: `${Math.min(rate,100)}%`, transition: "width .7s ease" }} />
        </div>
      </div>
    </div>
  );
}

// ─── Plan Badge ──────────────────────────────────────────────────────────────
function PlanBadge({ user }: { user: TelegramUser }) {
  const now = new Date();
  const expired = user.expires_at ? new Date(user.expires_at) < now : false;

  if (user.plan === "lifetime") {
    return (
      <span className="text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-500/20 px-1.5 py-0.5 rounded font-medium">
        Vitalicio
      </span>
    );
  }
  if (user.plan === "6months") {
    if (expired) {
      return (
        <span className="text-xs text-red-400 bg-red-400/10 border border-red-500/20 px-1.5 py-0.5 rounded font-medium">
          Expirado
        </span>
      );
    }
    return (
      <span className="text-xs text-blue-400 bg-blue-400/10 border border-blue-500/20 px-1.5 py-0.5 rounded font-medium">
        6 Meses
      </span>
    );
  }
  return null;
}

// ─── Users Panel ─────────────────────────────────────────────────────────────
function UsersPainel({
  data, onRemove, onRenew, pendingCount, onShowRequests,
}: {
  data: UsersStats;
  onRemove: (id: number) => void;
  onRenew: (id: number) => void;
  pendingCount: number;
  onShowRequests: () => void;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4 h-full">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-200 flex items-center gap-2">
          <Users size={15} className="text-indigo-400" /> Usuarios
        </h2>
        <div className="flex items-center gap-2">
          {pendingCount > 0 && (
            <button onClick={onShowRequests}
              className="flex items-center gap-1.5 text-xs text-amber-400 bg-amber-400/10 border border-amber-500/20 px-2.5 py-1 rounded-lg hover:bg-amber-400/20 transition-colors">
              <Bell size={11} />
              {pendingCount} pendente{pendingCount > 1 ? "s" : ""}
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-2">
        <div className="flex-1 text-center px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-xl">
          <div className="text-2xl font-bold text-green-400">{data.total_active}</div>
          <div className="text-xs text-gray-500">Ativos</div>
        </div>
        <div className="flex-1 text-center px-3 py-2 bg-gray-800/60 border border-gray-700/30 rounded-xl">
          <div className="text-2xl font-bold text-gray-300">{data.total_all}</div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
        <div className="flex-1 text-center px-3 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
          <div className="text-lg font-bold text-emerald-400">
            {(data.total_revenue ?? 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
          </div>
          <div className="text-xs text-gray-500">Faturado</div>
        </div>
        {data.expired_count > 0 && (
          <div className="flex-1 text-center px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-xl">
            <div className="text-2xl font-bold text-red-400">{data.expired_count}</div>
            <div className="text-xs text-gray-500">Expirados</div>
          </div>
        )}
      </div>

      {data.users.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-4">Nenhum usuario ativo.</p>
      ) : (
        <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
          {data.users.map((u) => {
            const isExpired = u.expires_at ? new Date(u.expires_at) < new Date() : false;
            return (
              <div key={u.id} className={`flex items-center justify-between rounded-lg px-3 py-2 ${isExpired ? "bg-red-950/20 border border-red-900/30" : "bg-gray-800/40"}`}>
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-7 h-7 rounded-full bg-indigo-600/30 border border-indigo-500/30 flex items-center justify-center text-xs font-bold text-indigo-300 flex-shrink-0">
                    {(u.first_name ?? u.username ?? "?")[0].toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-gray-200 flex items-center gap-1 flex-wrap">
                      <span className="truncate">{u.first_name ?? u.username ?? "—"}</span>
                      {u.is_admin && <span className="text-xs text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded flex-shrink-0">Admin</span>}
                      <PlanBadge user={u} />
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-1.5 flex-wrap">
                      {u.username && <span>@{u.username}</span>}
                      {u.expires_at && u.plan === "6months" && (
                        <span className={`flex items-center gap-0.5 ${isExpired ? "text-red-400" : "text-gray-600"}`}>
                          <CalendarClock size={10} />
                          {isExpired ? "Exp. " : "Ate "}
                          {fmtDateFull(u.expires_at)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                  {!u.is_admin && u.plan === "6months" && (
                    <button onClick={() => onRenew(u.telegram_id)}
                      title="Renovar +180 dias"
                      className="text-gray-600 hover:text-blue-400 transition-colors p-1 rounded">
                      <RotateCcw size={13} />
                    </button>
                  )}
                  {!u.is_admin && (
                    <button onClick={() => onRemove(u.telegram_id)}
                      title="Remover acesso"
                      className="text-gray-600 hover:text-red-400 transition-colors p-1 rounded">
                      <UserX size={13} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Requests Panel ──────────────────────────────────────────────────────────
function RequestsPainel({
  requests, onApprove, onReject, onClose, loading,
}: {
  requests: AccessRequest[];
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
  onClose: () => void;
  loading: Set<number>;
}) {
  return (
    <div className="bg-gray-900 border border-amber-500/30 rounded-2xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800 bg-amber-500/5">
        <h2 className="font-semibold text-amber-400 flex items-center gap-2">
          <Bell size={15} /> Solicitacoes de Acesso
          <span className="bg-amber-500/20 text-amber-300 text-xs px-2 py-0.5 rounded-full">{requests.length}</span>
        </h2>
        <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors text-xs">
          Fechar
        </button>
      </div>

      {requests.length === 0 ? (
        <div className="px-5 py-8 text-center text-gray-500 text-sm">Nenhuma solicitacao pendente.</div>
      ) : (
        <div className="divide-y divide-gray-800">
          {requests.map((r) => {
            const isLoading = loading.has(r.id);
            return (
              <div key={r.id} className="flex items-center justify-between px-5 py-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-amber-600/20 border border-amber-500/30 flex items-center justify-center text-sm font-bold text-amber-300">
                    {(r.first_name ?? r.username ?? "?")[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-200">
                      {r.first_name ?? r.username ?? "—"}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-2">
                      {r.username && <span>@{r.username}</span>}
                      <span className="text-gray-600">ID: {r.telegram_id}</span>
                    </div>
                    <div className="text-xs text-gray-600 mt-0.5">
                      {fmtDateFull(r.requested_at)} {fmtTime(r.requested_at)}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onApprove(r.id)}
                    disabled={isLoading}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600/20 border border-green-500/30 text-green-400 hover:bg-green-600/40 text-xs font-medium rounded-lg transition-colors disabled:opacity-50">
                    <Check size={12} /> Aprovar
                  </button>
                  <button
                    onClick={() => onReject(r.id)}
                    disabled={isLoading}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600/20 border border-red-500/30 text-red-400 hover:bg-red-600/40 text-xs font-medium rounded-lg transition-colors disabled:opacity-50">
                    <X size={12} /> Recusar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Signal Feed ─────────────────────────────────────────────────────────────
function SignalFeed({ signals, filter, onFilter }: {
  signals: Signal[];
  filter: SignalFilter;
  onFilter: (f: SignalFilter) => void;
}) {
  const filtered = filter === "all" ? signals : signals.filter((s) => s.status === filter);
  const tabs: { key: SignalFilter; label: string }[] = [
    { key: "all",     label: `Todos (${signals.length})` },
    { key: "win",     label: `Wins (${signals.filter(s => s.status==="win").length})` },
    { key: "loss",    label: `Losses (${signals.filter(s => s.status==="loss").length})` },
    { key: "pending", label: `Aguardando (${signals.filter(s => s.status==="pending").length})` },
  ];
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
        <h2 className="font-semibold text-gray-200">Feed de Sinais</h2>
        <div className="flex gap-1">
          {tabs.map(({ key, label }) => (
            <button key={key} onClick={() => onFilter(key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filter === key ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>
      {!filtered.length ? (
        <div className="px-5 py-10 text-center text-gray-500 text-sm">Nenhum sinal encontrado.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs uppercase tracking-wider bg-gray-900/80 border-b border-gray-800">
                <th className="px-5 py-3 text-left">Status</th>
                <th className="px-5 py-3 text-left">Entrada</th>
                <th className="px-5 py-3 text-left">Gale</th>
                <th className="px-5 py-3 text-left">Estrategia</th>
                <th className="px-5 py-3 text-right">Horario</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => {
                const cfg = STATUS_CFG[s.status] ?? STATUS_CFG.cancelled;
                return (
                  <tr key={s.id} className={`border-t border-gray-800/60 ${cfg.row}`}>
                    <td className="px-5 py-3">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${cfg.badge}`}>
                        {cfg.icon} {cfg.label}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${ENTRY_STYLE[s.entry] ?? "text-gray-300"}`}>
                        {s.entry}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-gray-400 text-xs">{GALE_LABEL[s.gale_level] ?? `Gale ${s.gale_level}`}</td>
                    <td className="px-5 py-3 text-gray-500 text-xs">{s.strategy}</td>
                    <td className="px-5 py-3 text-right">
                      <span className="text-gray-300 text-xs font-medium">{fmtTime(s.created_at)}</span><br />
                      <span className="text-gray-600 text-xs">{fmtDate(s.created_at)}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Dashboard ───────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [stats, setStats]       = useState<Stats[]>([]);
  const [signals, setSignals]   = useState<Signal[]>([]);
  const [usersData, setUsers]   = useState<UsersStats | null>(null);
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [showReqs, setShowReqs] = useState(false);
  const [actionLoading, setActionLoading] = useState<Set<number>>(new Set());
  const [online, setOnline]     = useState<boolean | null>(null);
  const [lastUpdate, setLast]   = useState<Date | null>(null);
  const [countdown, setCD]      = useState(REFRESH_INTERVAL);
  const [loading, setLoading]   = useState(false);
  const [filter, setFilter]     = useState<SignalFilter>("all");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [healthy, s, sg, ud, reqs] = await Promise.all([
        checkHealth(),
        fetchStats(),
        fetchSignals(undefined, undefined, 50),
        fetchUsers(),
        fetchRequests("pending"),
      ]);
      setOnline(healthy);
      setStats(s);
      setSignals(sg);
      setUsers(ud);
      setRequests(reqs);
      if (reqs.length > 0) setShowReqs(true);
      setLast(new Date());
    } catch {
      setOnline(false);
    } finally {
      setLoading(false);
      setCD(REFRESH_INTERVAL);
    }
  }, []);

  useEffect(() => {
    load();
    const iv = setInterval(load, REFRESH_INTERVAL * 1000);
    return () => clearInterval(iv);
  }, [load]);

  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => setCD((c) => (c > 1 ? c - 1 : REFRESH_INTERVAL)), 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [lastUpdate]);

  const handleApprove = async (id: number) => {
    setActionLoading((p) => new Set(p).add(id));
    try {
      await approveRequest(id);
      setRequests((prev) => prev.filter((r) => r.id !== id));
      await load();
    } finally {
      setActionLoading((p) => { const n = new Set(p); n.delete(id); return n; });
    }
  };

  const handleReject = async (id: number) => {
    setActionLoading((p) => new Set(p).add(id));
    try {
      await rejectRequest(id);
      setRequests((prev) => prev.filter((r) => r.id !== id));
    } finally {
      setActionLoading((p) => { const n = new Set(p); n.delete(id); return n; });
    }
  };

  const handleRemoveUser = async (telegram_id: number) => {
    await removeUser(telegram_id);
    await load();
  };

  const handleRenewUser = async (telegram_id: number) => {
    await renewUser(telegram_id);
    await load();
  };

  const bacbo = stats.find((s) => s.game === "bacbo");

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Signal Bot</h1>
          <p className="text-sm text-gray-500 mt-0.5">Painel administrativo</p>
        </div>
        <div className="flex items-center gap-3">
          {online !== null && (
            <div className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full border ${
              online ? "bg-green-500/10 text-green-400 border-green-500/20" : "bg-red-500/10 text-red-400 border-red-500/20"
            }`}>
              {online ? <Wifi size={11} /> : <WifiOff size={11} />}
              {online ? "Online" : "Offline"}
            </div>
          )}
          {lastUpdate && (
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <Clock size={11} /> {lastUpdate.toLocaleTimeString("pt-BR")}
            </div>
          )}
          <button onClick={load} disabled={loading}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 border border-gray-700 px-3 py-1.5 rounded-lg transition-colors">
            <RefreshCw size={11} className={loading ? "animate-spin" : ""} />
            em {countdown}s
          </button>
        </div>
      </div>

      {/* Solicitações pendentes */}
      {showReqs && (
        <RequestsPainel
          requests={requests}
          onApprove={handleApprove}
          onReject={handleReject}
          onClose={() => setShowReqs(false)}
          loading={actionLoading}
        />
      )}

      {/* Stats + Usuarios */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          {bacbo ? <StatsPainel data={bacbo} /> : (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 text-center text-gray-500 text-sm h-full flex items-center justify-center">
              {loading ? "Carregando..." : "Sem dados de Bac Bo"}
            </div>
          )}
        </div>
        <div>
          {usersData ? (
            <UsersPainel
              data={usersData}
              onRemove={handleRemoveUser}
              onRenew={handleRenewUser}
              pendingCount={requests.length}
              onShowRequests={() => setShowReqs(true)}
            />
          ) : (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 text-center text-gray-500 text-sm h-full flex items-center justify-center">
              {loading ? "Carregando..." : "Sem dados"}
            </div>
          )}
        </div>
      </div>

      {/* Feed */}
      <SignalFeed signals={signals} filter={filter} onFilter={setFilter} />
    </div>
  );
}
