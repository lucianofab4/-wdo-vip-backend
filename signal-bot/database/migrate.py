"""Executa migrações manuais no banco."""
import asyncio
from dotenv import load_dotenv
load_dotenv("C:/Users/Game-PC/signal-bot/.env")

from sqlalchemy import text
from database.connection import engine
from database.models import Base


async def _add_col(conn, table, col, definition):
    r = await conn.execute(text(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='{table}' AND column_name='{col}'
    """))
    if not r.fetchone():
        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {definition}"))
        print(f"OK  {table}.{col} adicionada")
    else:
        print(f"--  {table}.{col} ja existe")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        await _add_col(conn, "invite_codes",   "target_telegram_id", "BIGINT NULL")
        await _add_col(conn, "access_requests", "channel_invite_link", "VARCHAR(500) NULL")

    print("OK Migração concluída.")


if __name__ == "__main__":
    asyncio.run(main())
