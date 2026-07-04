from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, JSON, Numeric, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from database.connection import Base
import secrets


class GameResult(Base):
    __tablename__ = "game_results"

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    game       = Column(String(20), nullable=False, index=True)
    table_id   = Column(String(100), nullable=False, index=True)
    result     = Column(JSON, nullable=False)
    raw_data   = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Signal(Base):
    __tablename__ = "signals"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    game        = Column(String(20), nullable=False, index=True)
    table_id    = Column(String(100), nullable=False)
    strategy    = Column(String(50), nullable=False)
    entry       = Column(String(100), nullable=False)
    gale_level  = Column(SmallInteger, nullable=False, default=0)
    status      = Column(String(20), nullable=False, default="pending", index=True)
    result_id   = Column(BigInteger, ForeignKey("game_results.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username    = Column(String(100), nullable=True)
    first_name  = Column(String(100), nullable=True)
    is_active   = Column(Boolean, nullable=False, default=True)
    is_admin    = Column(Boolean, nullable=False, default=False)
    plan        = Column(String(20), nullable=False, default="free")
    expires_at  = Column(DateTime(timezone=True), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class StrategyConfig(Base):
    __tablename__ = "strategy_configs"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    game      = Column(String(20), nullable=False)
    strategy  = Column(String(50), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    config    = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("game", "strategy"),)


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    code               = Column(String(32), unique=True, nullable=False)
    created_by         = Column(BigInteger, nullable=True)
    target_telegram_id = Column(BigInteger, nullable=True)  # se preenchido, só esse ID pode usar
    used_by            = Column(BigInteger, nullable=True)
    used_at            = Column(DateTime(timezone=True), nullable=True)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    is_active          = Column(Boolean, nullable=False, default=True)

    @staticmethod
    def generate() -> str:
        return secrets.token_hex(16)


class AccessRequest(Base):
    __tablename__ = "access_requests"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id         = Column(BigInteger, nullable=True)
    username            = Column(String(100), nullable=True)
    first_name          = Column(String(100), nullable=True)
    status              = Column(String(20), nullable=False, default="pending")
    payment_status      = Column(String(20), nullable=False, default="free")
    plan                = Column(String(20), nullable=True)
    amount              = Column(Numeric(10, 2), nullable=True)
    payment_id          = Column(String(100), nullable=True)
    buyer_name          = Column(String(200), nullable=True)
    channel_invite_link = Column(String(500), nullable=True)   # link gerado automaticamente
    requested_at        = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at         = Column(DateTime(timezone=True), nullable=True)


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    game     = Column(String(20), nullable=False)
    date     = Column(String(10), nullable=False)
    total    = Column(Integer, nullable=False, default=0)
    wins     = Column(Integer, nullable=False, default=0)
    losses   = Column(Integer, nullable=False, default=0)
    win_rate = Column(Numeric(5, 2), nullable=True)

    __table_args__ = (UniqueConstraint("game", "date"),)
