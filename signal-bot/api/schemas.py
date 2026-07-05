from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class GameResultOut(BaseModel):
    id: int
    game: str
    table_id: str
    result: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SignalOut(BaseModel):
    id: int
    game: str
    table_id: str
    strategy: str
    entry: str
    gale_level: int
    status: str
    result_id: Optional[int]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class StrategyConfigOut(BaseModel):
    id: int
    game: str
    strategy: str
    is_active: bool
    config: dict

    class Config:
        from_attributes = True


class StrategyToggle(BaseModel):
    is_active: bool


class StrategyConfigUpdate(BaseModel):
    is_active: Optional[bool] = None
    config: Optional[dict] = None


class StatsOut(BaseModel):
    game: str
    total: int
    wins: int
    losses: int
    pending: int
    win_rate: float
    wins_direct: int = 0
    wins_gale1: int = 0
    wins_gale2: int = 0


class GameToggle(BaseModel):
    game: str
    enabled: bool
