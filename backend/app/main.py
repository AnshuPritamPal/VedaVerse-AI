"""FastAPI application entry point for VedaVerse AI."""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

# Keep the existing ``app.*`` imports working when Uvicorn is launched from
# the project root as ``backend.app.main:app``.
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Support the existing project .env and a backend-local .env without replacing
# values already loaded from the process environment.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")

from app.database.mongodb import MongoDBUnavailable, mongodb
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.conversations import router as conversations_router
from app.routes.messages import router as messages_router
from app.services.auth_service import RegistrationUnavailable, auth_service
from app.services.conversation_service import (
    ConversationStoreUnavailable,
    conversation_service,
)
from app.services.message_service import MessageStoreUnavailable, message_service


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open MongoDB before serving and close its client pool at shutdown."""
    try:
        await mongodb.connect()
        app.state.mongodb = mongodb.database
        app.state.mongodb_ready = True
        try:
            await auth_service.ensure_indexes()
        except RegistrationUnavailable as exc:
            logger.warning("User registration indexes are unavailable: %s", exc)
        try:
            await conversation_service.ensure_indexes()
        except ConversationStoreUnavailable as exc:
            logger.warning("Conversation indexes are unavailable: %s", exc)
        try:
            await message_service.ensure_indexes()
        except MessageStoreUnavailable as exc:
            logger.warning("Message indexes are unavailable: %s", exc)
    except MongoDBUnavailable as exc:
        app.state.mongodb = None
        app.state.mongodb_ready = False
        logger.warning("MongoDB is unavailable during startup: %s", exc)

    try:
        yield
    finally:
        await mongodb.close()


app = FastAPI(
    title="VedaVerse AI Backend",
    description="API layer for the existing VedaVerse RAG pipeline.",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(conversations_router, prefix="/api/conversations")
app.include_router(messages_router, prefix="/api/conversations")


@app.get("/api/health", tags=["health"])
async def health() -> dict[str, str]:
    try:
        await mongodb.ping()
    except MongoDBUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable. Check MONGODB_URI and MONGODB_DATABASE.",
        ) from exc
    return {
        "status": "ok",
        "service": "VedaVerse AI Backend",
        "database": "connected",
    }
