import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from api.dependencies import get_db
from api.schemas import StrategyConfigOut, StrategyConfigUpdate, GameToggle
from database.models import StrategyConfig

router = APIRouter(prefix="/strategies", tags=["Estratégias"])


@router.get("/", response_model=list[StrategyConfigOut])
async def list_strategies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StrategyConfig).order_by(StrategyConfig.game, StrategyConfig.strategy))
    return result.scalars().all()


@router.patch("/{game}/{strategy}", response_model=StrategyConfigOut)
async def update_strategy(
    game: str,
    strategy: str,
    body: StrategyConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StrategyConfig).where(
            StrategyConfig.game == game,
            StrategyConfig.strategy == strategy,
        )
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="Estratégia não encontrada")

    if body.is_active is not None:
        cfg.is_active = body.is_active
    if body.config is not None:
        cfg.config = body.config
    cfg.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(cfg)
    return cfg


@router.post("/game-toggle")
async def toggle_game(body: GameToggle):
    """Liga/desliga um jogo inteiro via variável de ambiente em tempo de execução."""
    env_key = f"GAME_{body.game.upper()}_ENABLED"
    os.environ[env_key] = "true" if body.enabled else "false"
    return {"game": body.game, "enabled": body.enabled, "message": "Atualizado (reinicie o coletor para efetivar)"}
