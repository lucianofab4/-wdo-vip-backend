import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export interface Stats {
  game: string;
  total: number;
  wins: number;
  losses: number;
  pending: number;
  win_rate: number;
  wins_direct: number;
  wins_gale1: number;
  wins_gale2: number;
}

export interface Signal {
  id: number;
  game: string;
  table_id: string;
  strategy: string;
  entry: string;
  gale_level: number;
  status: string;
  created_at: string;
  resolved_at: string | null;
}

export interface TelegramUser {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  plan: string;
  expires_at: string | null;
  created_at: string;
}

export interface AccessRequest {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  buyer_name: string | null;
  plan: string | null;
  amount: number | null;
  status: string;
  payment_status: string;
  requested_at: string;
  resolved_at: string | null;
}

export interface UsersStats {
  total_active: number;
  total_all: number;
  pending_requests: number;
  expired_count: number;
  total_revenue: number;
  users: TelegramUser[];
}

export interface StrategyConfig {
  id: number;
  game: string;
  strategy: string;
  is_active: boolean;
  config: Record<string, unknown>;
}

export const fetchStats = () => api.get<Stats[]>("/stats").then((r) => r.data);
export const fetchSignals = (game?: string, status?: string, limit = 50) =>
  api.get<Signal[]>("/signals", { params: { game, status, limit } }).then((r) => r.data);
export const fetchUsers = () => api.get<UsersStats>("/users").then((r) => r.data);
export const fetchRequests = (status = "pending") =>
  api.get<AccessRequest[]>("/users/requests", { params: { status } }).then((r) => r.data);
export const approveRequest = (id: number) =>
  api.post(`/users/requests/${id}/approve`).then((r) => r.data);
export const rejectRequest = (id: number) =>
  api.post(`/users/requests/${id}/reject`).then((r) => r.data);
export const removeUser = (telegram_id: number) =>
  api.delete(`/users/${telegram_id}`).then((r) => r.data);
export const renewUser = (telegram_id: number) =>
  api.post(`/users/${telegram_id}/renew`).then((r) => r.data);
export const checkHealth = () => api.get("/health").then(() => true).catch(() => false);
export const fetchStrategies = () =>
  api.get<StrategyConfig[]>("/strategies/").then((r) => r.data);
export const toggleStrategy = (game: string, strategy: string, is_active: boolean) =>
  api.patch<StrategyConfig>(`/strategies/${game}/${strategy}`, { is_active }).then((r) => r.data);
export const toggleGame = (game: string, enabled: boolean) =>
  api.post("/strategies/game-toggle", { game, enabled }).then((r) => r.data);

// ─── WDO ─────────────────────────────────────────────────────────────────────

export interface WdoSignal {
  id: number;
  direction: string;          // COMPRA | VENDA
  entry_price: number | null;
  signal_type: string;        // REGIAO_SUPORTE | MM6_PULLBACK | OPEN_DRIVE | etc.
  status: string;             // pending | win | loss | cancelled
  pts_result: number | null;  // +6.0 = win, -3.0 = loss
  signal_time: string | null; // HH:MM
  created_at: string;
  resolved_at: string | null;
}

export interface WdoStats {
  total: number;
  wins: number;
  losses: number;
  pending: number;
  cancelled: number;
  win_rate: number;
}

export interface FreeSubscriber {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  joined_at: string | null;
  synced_at: string | null;
}

export const fetchWdoSignals = (params?: {
  date?: string; hour?: string; direction?: string; status?: string; limit?: number;
}) => api.get<WdoSignal[]>("/wdo/signals", { params }).then((r) => r.data);

export const fetchWdoStats = (params?: {
  date?: string; hour_from?: string; hour_to?: string;
}) => api.get<WdoStats>("/wdo/stats", { params }).then((r) => r.data);

export const fetchFreeSubscribers = () =>
  api.get<FreeSubscriber[]>("/wdo/free-subscribers").then((r) => r.data);
