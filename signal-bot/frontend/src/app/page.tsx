"use client";
import { useEffect, useState, useCallback, useRef } from "react";
import {
  fetchWdoSignals, fetchWdoStats, fetchUsers, fetchFreeSubscribers,
  fetchRequests, approveRequest, rejectRequest, removeUser, renewUser, checkHealth,
} from "@/lib/api";
import type { WdoSignal, WdoStats, UsersStats, AccessRequest, TelegramUser, FreeSubscriber } from "@/lib/api";
import {
  RefreshCw, Wifi, WifiOff, Clock, Users, Trophy,
  Target, AlertCircle, Check, X, UserX, Bell, RotateCcw, CalendarClock,
  TrendingUp, TrendingDown, Filter,
} from "lucide-react";

const REFRESH_INTERVAL = 15;

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });
const fmtDateFull = (iso: string) =>
  new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
const todayStr = () => new Date().toISOString().slice(0, 10);

const SIGNAL_TYPE_LABEL: Record<string, string> = {
  REGIAO_SUPORTE:    "Suporte",
  REGIAO_RESISTENCIA:"Resistência",
  MM6_PULLBACK:      "Pullback MM6",
  OPEN_DRIVE:        "Open Drive",
  GAP_FADE:          "Gap Fade",
  TOPO_DIA:          "Topo do Dia",
  FUNDO_DIA:         "Fundo do Dia",
};

const HOURS = ["09","10","11","12","13","14","15","16","17"];

// ─── WDO Stats Panel ──────────────────────────────────────────────────────────
function WdoStatsPainel({
  stats, hourFilter, onHourFilter,
}: {
  stats: WdoStats | null;
  hourFilter: string;
  onHourFilter: (h: string) => void;
}) {
  const s = stats ?? { total: 0, wins: 0, losses: 0, pending: 0, cancelled: 0, win_rate: 0 };
  const rate = s.win_rate;
  const rateColor = rate >= 70 ? "text-green-400" : rate >= 50 ? "text-yellow-400" : "text-red-400";
  const barColor  = rate >= 70 ? "bg-green-500" : rate >= 50 ? "bg-yellow-500" : "bg-red-500";
  const r = 40, circ = 2 * Math.PI * r;
  const ringColor = rate >= 70 ? "#4ade80" : rate >= 50 ? "#facc15" : "#f87171";

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-5">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xl font-bold mb-1">Mini Dólar WDO</div>
          <span className="text-xs text-green-400 bg-green-400/10 border border-green-500/20 px-2.5 py-0.5 rounded-full">
            Sinais ao vivo
          </span>
        </div>
        {/* Win rate ring */}
        <div className="relative w-24 h-24 flex-shrink-0">
          <svg width="96" height="96" className="-rotate-90">
            <circle cx="48" cy="48" r={r} fill="none" stroke="#1f2937" strokeWidth="9" />
            <circle cx="48" cy="48" r={r} fill="none" stroke={ringColor} strokeWidth="9"
              strokeDasharray={`${(Math.min(rate,100)/100)*circ} ${circ}`} strokeLinecap="round"
              style={{ transition: "stroke-dasharray .8s ease" }} />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-xl font-bold" style={{ color: ringColor }}>{rate.toFixed(0)}%</span>
            <span className="text-xs text-gray-500 mt-0.5">acerto</span>
          </div>
        </div>
      </div>

      {/* Hour filter */}
      <div>
        <div className="flex items-center gap-1.5 mb-2">
          <Filter size={11} className="text-gray-500" />
          <span className="text-xs text-gray-500 uppercase tracking-wider">Filtro por hora</span>
        </div>
        <div className="flex flex-wrap gap-1">
          <button onClick={() => onHourFilter("")}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
              hourFilter === "" ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"
            }`}>
            Todas
          </button>
          {HOURS.map((h) => (
            <button key={h} onClick={() => onHourFilter(h)}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                hourFilter === h ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"
              }`}>
              {h}h
            </button>
          ))}
        </div>
      </div>

      {/* Counters */}
      <div className="grid grid-cols-4 gap-2">
        {[
          { label: "Total",     value: s.total,     icon: <Target size={13} />,       color: "text-gray-200" },
          { label: "Gain",      value: s.wins,       icon: <TrendingUp size={13} />,   color: "text-green-400" },
          { label: "Loss",      value: s.losses,     icon: <TrendingDown size={13} />, color: "text-red-400" },
          { label: "Andando",   value: s.pending,    icon: <Clock size={13} />,        color: "text-yellow-400" },
        ].map(({ label, value, icon, color }) => (
          <div key={label} className="bg-gray-800/50 border border-gray-700/30 rounded-xl p-3 text-center">
            <div className={`flex items-center justify-center gap-1 text-xs mb-1.5 ${color}`}>{icon} {label}</div>
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
          </div>
        ))}
      </div>

      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1.5">
          <span>Taxa de acerto (gain/loss)</span>
          <span className={`font-semibold ${rateColor}`}>{rate.toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div className={`h-full ${barColor} rounded-full`}
            style={{ width: `${Math.min(rate,100)}%`, transition: "width .7s ease" }} />
        </div>
        <p className="text-xs text-gray-600 mt-1.5">GAIN = +6 pts  •  LOSS = −3 pts  •  Cancelado não conta</p>
      </div>
    </div>
  );
}

// ─── Plan Badge ───────────────────────────────────────────────────────────────
function PlanBadge({ user }: { user: TelegramUser }) {
  const now = new Date();
  const expired = user.expires_at ? new Date(user.expires_at) < now : false;
  const planMap: Record<string, { label: string; cls: string }> = {
    lifetime:        { label: "Vitalício",     cls: "text-emerald-400 bg-emerald-400/10 border-emerald-500/20" },
    "6months":       { label: "6 Meses",       cls: expired ? "text-red-400 bg-red-400/10 border-red-500/20" : "text-blue-400 bg-blue-400/10 border-blue-500/20" },
    dolar_semestral: { label: "Dólar Sem.",    cls: expired ? "text-red-400 bg-red-400/10 border-red-500/20" : "text-blue-400 bg-blue-400/10 border-blue-500/20" },
    dolar_mensal:    { label: "Dólar Men.",    cls: expired ? "text-red-400 bg-red-400/10 border-red-500/20" : "text-cyan-400 bg-cyan-400/10 border-cyan-500/20" },
    dolar_teste:     { label: "Teste",         cls: "text-orange-400 bg-orange-400/10 border-orange-500/20" },
  };
  const cfg = planMap[user.plan];
  if (!cfg) return null;
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${cfg.cls}`}>
      {expired ? "Expirado" : cfg.label}
    </span>
  );
}

// ─── VIP Users Tab ────────────────────────────────────────────────────────────
function VipUsersList({
  data, onRemove, onRenew,
}: {
  data: UsersStats;
  onRemove: (id: number) => void;
  onRenew: (id: number) => void;
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-3 gap-2">
        <div className="text-center px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-xl">
          <div className="text-2xl font-bold text-green-400">{data.total_active}</div>
          <div className="text-xs text-gray-500">Ativos</div>
        </div>
        <div className="text-center px-3 py-2 bg-gray-800/60 border border-gray-700/30 rounded-xl">
          <div className="text-2xl font-bold text-gray-300">{data.total_all}</div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
        <div className="text-center px-3 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
          <div className="text-base font-bold text-emerald-400">
            {(data.total_revenue ?? 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
          </div>
          <div className="text-xs text-gray-500">Faturado</div>
        </div>
      </div>

      {data.users.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-4">Nenhum usuário ativo.</p>
      ) : (
        <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
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
                      {u.is_admin && <span className="text-xs text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded">Admin</span>}
                      <PlanBadge user={u} />
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-1.5">
                      {u.username && <span>@{u.username}</span>}
                      {u.expires_at && (
                        <span className={`flex items-center gap-0.5 ${isExpired ? "text-red-400" : "text-gray-600"}`}>
                          <CalendarClock size={10} />
                          {isExpired ? "Exp. " : "Até "}
                          {fmtDateFull(u.expires_at)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                  {!u.is_admin && (u.plan === "6months" || u.plan === "dolar_semestral" || u.plan === "dolar_mensal") && (
                    <button onClick={() => onRenew(u.telegram_id)} title="Renovar"
                      className="text-gray-600 hover:text-blue-400 transition-colors p-1 rounded">
                      <RotateCcw size={13} />
                    </button>
                  )}
                  {!u.is_admin && (
                    <button onClick={() => onRemove(u.telegram_id)} title="Remover"
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

// ─── Free Subscribers Tab ─────────────────────────────────────────────────────
function FreeSubscribersList({ subscribers }: { subscribers: FreeSubscriber[] }) {
  if (subscribers.length === 0) {
    return (
      <div className="py-8 text-center">
        <p className="text-gray-500 text-sm">Nenhum assinante free sincronizado.</p>
        <p className="text-gray-600 text-xs mt-1">O monitor envia a lista automaticamente via API.</p>
      </div>
    );
  }
  return (
    <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
      {subscribers.map((s) => (
        <div key={s.id} className="flex items-center gap-2 bg-gray-800/40 rounded-lg px-3 py-2">
          <div className="w-7 h-7 rounded-full bg-blue-600/30 border border-blue-500/30 flex items-center justify-center text-xs font-bold text-blue-300 flex-shrink-0">
            {(s.first_name ?? s.username ?? "?")[0].toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium text-gray-200 truncate">
              {s.first_name ?? s.username ?? `ID ${s.telegram_id}`}
            </div>
            <div className="text-xs text-gray-500">
              {s.username && `@${s.username} · `}ID: {s.telegram_id}
            </div>
          </div>
          <span className="text-xs text-blue-400 bg-blue-400/10 border border-blue-500/20 px-1.5 py-0.5 rounded flex-shrink-0">
            Free
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Users Panel (com abas) ───────────────────────────────────────────────────
type UsersTab = "vip" | "free" | "requests";

function UsersPainel({
  data, freeSubscribers, requests, onRemove, onRenew, onApprove, onReject, actionLoading,
}: {
  data: UsersStats | null;
  freeSubscribers: FreeSubscriber[];
  requests: AccessRequest[];
  onRemove: (id: number) => void;
  onRenew: (id: number) => void;
  onApprove: (id: number) => void;
  onReject: (id: number) => void;
  actionLoading: Set<number>;
}) {
  const [tab, setTab] = useState<UsersTab>("vip");

  const tabs: { key: UsersTab; label: string; count?: number; badge?: string }[] = [
    { key: "vip",      label: "VIP Pagantes", count: data?.total_active },
    { key: "free",     label: "Canal Free",   count: freeSubscribers.length },
    { key: "requests", label: "Solicitações", count: requests.length, badge: requests.length > 0 ? "amber" : undefined },
  ];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex flex-col gap-4 h-full">
      <div className="flex items-center gap-2">
        <Users size={15} className="text-indigo-400" />
        <h2 className="font-semibold text-gray-200">Usuários</h2>
      </div>

      {/* Abas */}
      <div className="flex gap-1 border-b border-gray-800 pb-3">
        {tabs.map(({ key, label, count, badge }) => (
          <button key={key} onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              tab === key ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800"
            }`}>
            {label}
            {count !== undefined && (
              <span className={`px-1.5 py-0.5 rounded-full text-xs font-bold ${
                badge === "amber"
                  ? "bg-amber-500/20 text-amber-300"
                  : tab === key ? "bg-white/20 text-white" : "bg-gray-700 text-gray-400"
              }`}>
                {count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Conteúdo da aba */}
      {tab === "vip" && (
        data ? (
          <VipUsersList data={data} onRemove={onRemove} onRenew={onRenew} />
        ) : (
          <p className="text-gray-500 text-sm text-center py-4">Carregando...</p>
        )
      )}

      {tab === "free" && (
        <FreeSubscribersList subscribers={freeSubscribers} />
      )}

      {tab === "requests" && (
        requests.length === 0 ? (
          <div className="py-6 text-center text-gray-500 text-sm">Nenhuma solicitação pendente.</div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {requests.map((r) => {
              const isLoading = actionLoading.has(r.id);
              return (
                <div key={r.id} className="flex items-center justify-between bg-amber-950/20 border border-amber-900/30 rounded-lg px-3 py-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-amber-600/20 border border-amber-500/30 flex items-center justify-center text-xs font-bold text-amber-300 flex-shrink-0">
                      {(r.first_name ?? r.username ?? "?")[0].toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-gray-200 truncate">
                        {r.first_name ?? r.username ?? "—"}
                      </div>
                      <div className="text-xs text-gray-500">
                        {r.username && `@${r.username} · `}
                        {fmtDateFull(r.requested_at)} {fmtTime(r.requested_at)}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1.5 flex-shrink-0 ml-2">
                    <button onClick={() => onApprove(r.id)} disabled={isLoading}
                      className="flex items-center gap-1 px-2 py-1 bg-green-600/20 border border-green-500/30 text-green-400 hover:bg-green-600/40 text-xs rounded-lg transition-colors disabled:opacity-50">
                      <Check size={11} /> Aprovar
                    </button>
                    <button onClick={() => onReject(r.id)} disabled={isLoading}
                      className="flex items-center gap-1 px-2 py-1 bg-red-600/20 border border-red-500/30 text-red-400 hover:bg-red-600/40 text-xs rounded-lg transition-colors disabled:opacity-50">
                      <X size={11} /> Recusar
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )
      )}
    </div>
  );
}

// ─── Signal Feed WDO ──────────────────────────────────────────────────────────
type SigFilter = "all" | "win" | "loss" | "pending" | "cancelled";

const STATUS_CFG: Record<string, { label: string; icon: string; row: string; badge: string }> = {
  win:       { label: "GAIN",    icon: "✅", row: "bg-green-950/30 border-green-900/40",   badge: "text-green-400 bg-green-400/10 border border-green-500/20" },
  loss:      { label: "LOSS",    icon: "❌", row: "bg-red-950/30 border-red-900/40",       badge: "text-red-400 bg-red-400/10 border border-red-500/20" },
  pending:   { label: "ANDANDO", icon: "⏳", row: "bg-yellow-950/20 border-yellow-900/30", badge: "text-yellow-400 bg-yellow-400/10 border border-yellow-500/20" },
  cancelled: { label: "CANC",    icon: "⛔", row: "bg-gray-900/40 border-gray-800/40",     badge: "text-gray-500 bg-gray-500/10 border border-gray-700/20" },
};

function SignalFeed({ signals }: { signals: WdoSignal[] }) {
  const [filter, setFilter] = useState<SigFilter>("all");

  const filtered = filter === "all" ? signals : signals.filter((s) => s.status === filter);
  const tabs: { key: SigFilter; label: string }[] = [
    { key: "all",       label: `Todos (${signals.length})` },
    { key: "win",       label: `Gain (${signals.filter(s => s.status==="win").length})` },
    { key: "loss",      label: `Loss (${signals.filter(s => s.status==="loss").length})` },
    { key: "pending",   label: `Andando (${signals.filter(s => s.status==="pending").length})` },
    { key: "cancelled", label: `Canc. (${signals.filter(s => s.status==="cancelled").length})` },
  ];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
        <h2 className="font-semibold text-gray-200">Sinais WDO — Hoje</h2>
        <div className="flex gap-1 flex-wrap">
          {tabs.map(({ key, label }) => (
            <button key={key} onClick={() => setFilter(key)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filter === key ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {!filtered.length ? (
        <div className="px-5 py-10 text-center text-gray-500 text-sm">
          {signals.length === 0 ? "Nenhum sinal hoje — aguardando monitor." : "Nenhum sinal neste filtro."}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 text-xs uppercase tracking-wider bg-gray-900/80 border-b border-gray-800">
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Direção</th>
                <th className="px-4 py-3 text-left">Tipo</th>
                <th className="px-4 py-3 text-right">Entrada</th>
                <th className="px-4 py-3 text-right">Pts</th>
                <th className="px-4 py-3 text-right">Hora</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => {
                const cfg = STATUS_CFG[s.status] ?? STATUS_CFG.cancelled;
                const isCompra = s.direction === "COMPRA";
                const pts = s.pts_result;
                return (
                  <tr key={s.id} className={`border-t border-gray-800/60 ${cfg.row}`}>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-semibold ${cfg.badge}`}>
                        {cfg.icon} {cfg.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                        isCompra
                          ? "bg-green-500/20 text-green-300 border border-green-500/30"
                          : "bg-red-500/20 text-red-300 border border-red-500/30"
                      }`}>
                        {s.direction}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {SIGNAL_TYPE_LABEL[s.signal_type] ?? s.signal_type}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300 text-xs font-mono">
                      {s.entry_price != null ? s.entry_price.toFixed(1) : "—"}
                    </td>
                    <td className="px-4 py-3 text-right text-xs font-semibold">
                      {pts != null ? (
                        <span className={pts > 0 ? "text-green-400" : "text-red-400"}>
                          {pts > 0 ? "+" : ""}{pts.toFixed(1)}
                        </span>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-gray-300 text-xs font-medium">
                        {s.signal_time ?? fmtTime(s.created_at)}
                      </span>
                      <br />
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

// ─── Dashboard ────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [wdoSignals, setWdoSignals]       = useState<WdoSignal[]>([]);
  const [wdoStats, setWdoStats]           = useState<WdoStats | null>(null);
  const [usersData, setUsers]             = useState<UsersStats | null>(null);
  const [freeSubscribers, setFree]        = useState<FreeSubscriber[]>([]);
  const [requests, setRequests]           = useState<AccessRequest[]>([]);
  const [actionLoading, setActionLoading] = useState<Set<number>>(new Set());
  const [online, setOnline]               = useState<boolean | null>(null);
  const [lastUpdate, setLast]             = useState<Date | null>(null);
  const [countdown, setCD]                = useState(REFRESH_INTERVAL);
  const [loading, setLoading]             = useState(false);
  const [hourFilter, setHourFilter]       = useState("");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const today = todayStr();
    try {
      const [healthy, sigs, statsData, ud, subs, reqs] = await Promise.all([
        checkHealth(),
        fetchWdoSignals({ date: today, limit: 200 }),
        fetchWdoStats({ date: today, hour_from: hourFilter || undefined }),
        fetchUsers(),
        fetchFreeSubscribers(),
        fetchRequests("pending"),
      ]);
      setOnline(healthy);
      setWdoSignals(sigs);
      setWdoStats(statsData);
      setUsers(ud);
      setFree(subs);
      setRequests(reqs);
      setLast(new Date());
    } catch {
      setOnline(false);
    } finally {
      setLoading(false);
      setCD(REFRESH_INTERVAL);
    }
  }, [hourFilter]);

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

  const filteredSignals = hourFilter
    ? wdoSignals.filter((s) => s.signal_time?.startsWith(hourFilter + ":"))
    : wdoSignals;

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">WDO Painel</h1>
          <p className="text-sm text-gray-500 mt-0.5">Administrativo — sinais e usuários</p>
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

      {/* Stats + Usuários */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <WdoStatsPainel
            stats={wdoStats}
            hourFilter={hourFilter}
            onHourFilter={setHourFilter}
          />
        </div>
        <div>
          <UsersPainel
            data={usersData}
            freeSubscribers={freeSubscribers}
            requests={requests}
            onRemove={async (id) => { await removeUser(id); await load(); }}
            onRenew={async (id) => { await renewUser(id); await load(); }}
            onApprove={handleApprove}
            onReject={handleReject}
            actionLoading={actionLoading}
          />
        </div>
      </div>

      {/* Feed */}
      <SignalFeed signals={filteredSignals} />
    </div>
  );
}
