from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.routes import results, signals, stats, strategies, users, payments

app = FastAPI(title="Signal Bot API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(results.router)
app.include_router(signals.router)
app.include_router(stats.router)
app.include_router(strategies.router)
app.include_router(users.router)
app.include_router(payments.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    logger.info("API iniciada.")
