"""
Commercial Analytics Platform - FastAPI Backend Entry
"""
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("app")

from app.data.store import DataStore
from app.data.mongo import ensure_indexes
from app.ai.vector_store import VectorStore
from app.api import (
    health, kpi, hcp, rep, territory, conversion, kol,
    briefing, nba, sources, chat, exec_dashboard, audit, export,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Bootstrapping DataStore...")
    DataStore.instance().load_all()
    logger.info("DataStore ready. Rows: %s", DataStore.instance().counts())
    try:
        await ensure_indexes()
    except Exception as e:
        logger.warning("Mongo index init failed (non-fatal): %s", e)
    try:
        n = await VectorStore.instance().build()
        logger.info("VectorStore built (%s chunks)", n)
    except Exception as e:
        logger.warning("VectorStore build failed (non-fatal): %s", e)
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Commercial Analytics Platform API",
    description="Pharma commercial analytics + GenAI (AWS Bedrock / Emergent fallback)",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = os.environ.get("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origins] if cors_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (health, kpi, hcp, rep, territory, conversion, kol, briefing, nba,
               sources, chat, exec_dashboard, audit, export):
    app.include_router(module.router, prefix="/api")


@app.get("/")
def root():
    return {"service": "commercial-analytics-platform", "status": "ok"}
