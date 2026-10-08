"""MongoDB connection and readiness checks using PyMongo's async client."""

import logging

from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.config import settings


logger = logging.getLogger(__name__)


class MongoDBUnavailable(RuntimeError):
    """Raised when MongoDB is unconfigured or cannot be reached."""


class MongoDBConnection:
    def __init__(self) -> None:
        self.client: AsyncMongoClient | None = None
        self.database = None

    async def connect(self) -> None:
        """Create and verify the Mongo connection before exposing it to routes."""
        if not settings.mongodb_uri:
            raise MongoDBUnavailable("MONGODB_URI is not configured.")
        if not settings.mongodb_database:
            raise MongoDBUnavailable("MONGODB_DATABASE is not configured.")

        client = None
        try:
            client = AsyncMongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
                appname="VedaVerseAIBackend",
            )
            database = client[settings.mongodb_database]
            await database.command("ping")
        except (PyMongoError, OSError, ValueError) as exc:
            if client is not None:
                await client.close()
            raise MongoDBUnavailable("Could not connect to MongoDB.") from exc

        self.client = client
        self.database = database
        logger.info("MongoDB connection established.")

    async def ping(self) -> None:
        """Check that the configured MongoDB deployment is responding."""
        if self.client is None or self.database is None:
            raise MongoDBUnavailable("MongoDB connection is not established.")
        try:
            await self.database.command("ping")
        except (PyMongoError, OSError) as exc:
            raise MongoDBUnavailable("MongoDB health check failed.") from exc

    async def close(self) -> None:
        """Close the client pool during application shutdown."""
        if self.client is not None:
            await self.client.close()
            self.client = None
            self.database = None


mongodb = MongoDBConnection()
