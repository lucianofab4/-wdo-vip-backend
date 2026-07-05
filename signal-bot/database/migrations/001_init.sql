-- ─── Extensões ─────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Resultados dos jogos ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS game_results (
    id          BIGSERIAL PRIMARY KEY,
    game        VARCHAR(20)  NOT NULL,   -- bacbo | dadinho | crash
    table_id    VARCHAR(100) NOT NULL,
    result      JSONB        NOT NULL,   -- dados específicos do jogo
    raw_data    JSONB,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_results_game       ON game_results(game);
CREATE INDEX idx_results_table      ON game_results(table_id);
CREATE INDEX idx_results_created    ON game_results(created_at DESC);

-- ─── Sinais gerados ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS signals (
    id           BIGSERIAL PRIMARY KEY,
    game         VARCHAR(20)  NOT NULL,
    table_id     VARCHAR(100) NOT NULL,
    strategy     VARCHAR(50)  NOT NULL,
    entry        VARCHAR(100) NOT NULL,  -- o que apostar
    gale_level   SMALLINT     NOT NULL DEFAULT 0,
    status       VARCHAR(20)  NOT NULL DEFAULT 'pending', -- pending|win|loss|cancelled
    result_id    BIGINT REFERENCES game_results(id),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    resolved_at  TIMESTAMPTZ
);

CREATE INDEX idx_signals_game    ON signals(game);
CREATE INDEX idx_signals_status  ON signals(status);
CREATE INDEX idx_signals_created ON signals(created_at DESC);

-- ─── Usuários Telegram ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS telegram_users (
    id          BIGSERIAL    PRIMARY KEY,
    telegram_id BIGINT       UNIQUE NOT NULL,
    username    VARCHAR(100),
    first_name  VARCHAR(100),
    is_active   BOOLEAN      NOT NULL DEFAULT true,
    is_admin    BOOLEAN      NOT NULL DEFAULT false,
    plan        VARCHAR(20)  NOT NULL DEFAULT 'free',  -- free | vip
    expires_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ─── Configuração das estratégias ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS strategy_configs (
    id          SERIAL      PRIMARY KEY,
    game        VARCHAR(20) NOT NULL,
    strategy    VARCHAR(50) NOT NULL,
    is_active   BOOLEAN     NOT NULL DEFAULT true,
    config      JSONB       NOT NULL DEFAULT '{}',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(game, strategy)
);

-- Seed inicial das estratégias
INSERT INTO strategy_configs (game, strategy, is_active, config) VALUES
  ('bacbo',   'streak',   true,  '{"min_streak": 3, "max_gale": 2}'),
  ('bacbo',   'reverse',  true,  '{"min_streak": 4, "max_gale": 2}'),
  ('bacbo',   'surf',     false, '{"window": 10, "max_gale": 1}'),
  ('dadinho', 'streak',   true,  '{"min_streak": 3, "max_gale": 2}'),
  ('dadinho', 'high_low', true,  '{"min_streak": 3, "max_gale": 2}'),
  ('crash',   'multiplier', true, '{"target": 2.0, "min_streak_low": 3, "max_gale": 1}'),
  ('crash',   'timing',    false, '{"interval_seconds": 30, "max_gale": 1}')
ON CONFLICT DO NOTHING;

-- ─── Métricas diárias (cache) ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_metrics (
    id         SERIAL      PRIMARY KEY,
    game       VARCHAR(20) NOT NULL,
    date       DATE        NOT NULL,
    total      INT         NOT NULL DEFAULT 0,
    wins       INT         NOT NULL DEFAULT 0,
    losses     INT         NOT NULL DEFAULT 0,
    win_rate   NUMERIC(5,2),
    UNIQUE(game, date)
);
