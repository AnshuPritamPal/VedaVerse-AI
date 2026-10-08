"""Environment-backed settings for the FastAPI backend."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Resolve configuration relative to this file so imports behave the same when
# Uvicorn starts from either the project root or the backend directory.
BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "").strip()
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "").strip()
    mongodb_server_selection_timeout_ms: int = int(
        os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
    )
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "").strip()
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256").strip()
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )


settings = Settings()
