"""Persistent cache of answers to frequently asked questions.

A repeated question is answered from MongoDB instead of re-running retrieval
and the LLM. Matching happens in two steps:

1. Exact: the same normalized text, detail level and cache version.
2. Paraphrase: cosine similarity of question embeddings at or above
   ``ANSWER_CACHE_SIMILARITY`` (0.92 by default), and only between questions
   that mention the same numbers, so "Explain 2.47" never reuses 2.48.

Embeddings of cached questions are mirrored in memory as a NumPy matrix, so
a paraphrase lookup is one matrix-vector product. Entries expire after
``ANSWER_CACHE_TTL_DAYS`` through a MongoDB TTL index, and hit counts plus
the number of distinct askers record which questions are asked most.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.config import settings
from app.database.mongodb import mongodb


logger = logging.getLogger(__name__)

# Bump when retrieval or answer generation changes enough that earlier cached
# answers should no longer be served.
CACHE_VERSION = 2  # 2: hybrid (semantic + BM25) retrieval

# Fields of a RAG result that the chat API returns and the cache stores.
CACHED_FIELDS = ("answer", "references", "verses", "display_items")

# A question is listed as "popular" only once this many different people have
# asked it, so one person's wording is never shown to others.
POPULAR_MIN_USERS = 3


class AnswerCacheUnavailable(RuntimeError):
    """Raised when the cache collection cannot be reached."""


def is_cacheable(result: dict[str, Any]) -> bool:
    """Only cache complete, verified answers worth serving again."""
    return (
        isinstance(result.get("answer"), str)
        and bool(result["answer"].strip())
        and not result.get("insufficient_context")
        and not result.get("error")
        and bool(result.get("references"))
    )


class AnswerCacheService:
    def __init__(self) -> None:
        self._ids: list[ObjectId] = []
        self._keys: list[tuple[bool, tuple[str, ...]]] = []
        self._matrix: np.ndarray | None = None
        self._loaded = False
        self._load_lock = asyncio.Lock()

    def _collection(self):
        if mongodb.database is None:
            raise AnswerCacheUnavailable("MongoDB is not connected.")
        return mongodb.database["answer_cache"]

    async def ensure_indexes(self) -> None:
        try:
            collection = self._collection()
            await collection.create_index(
                [("normalized_question", ASCENDING), ("detailed", ASCENDING),
                 ("version", ASCENDING)],
                name="uniq_answer_cache_question", unique=True,
            )
            await collection.create_index(
                "created_at", name="ttl_answer_cache",
                expireAfterSeconds=settings.answer_cache_ttl_days * 24 * 3600,
            )
            await collection.create_index(
                [("user_count", DESCENDING), ("hit_count", DESCENDING)],
                name="idx_answer_cache_popular",
            )
        except PyMongoError as exc:
            raise AnswerCacheUnavailable("Answer cache indexes are unavailable.") from exc

    # ---- in-memory embedding mirror -------------------------------------

    def _fresh_filter(self) -> dict[str, Any]:
        # The TTL monitor only runs once a minute; skip entries due to expire.
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.answer_cache_ttl_days)
        return {"version": CACHE_VERSION, "created_at": {"$gt": cutoff}}

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        async with self._load_lock:
            if self._loaded:
                return
            cursor = self._collection().find(
                self._fresh_filter(),
                {"embedding": 1, "detailed": 1, "numbers": 1},
            )
            ids, keys, vectors = [], [], []
            async for document in cursor:
                ids.append(document["_id"])
                keys.append((bool(document["detailed"]), tuple(document.get("numbers", []))))
                vectors.append(document["embedding"])
            self._ids, self._keys = ids, keys
            self._matrix = np.asarray(vectors, dtype=np.float32) if vectors else None
            self._loaded = True
            logger.info("Answer cache loaded with %s entries.", len(ids))

    def _remember(self, entry_id: ObjectId, signature: dict[str, Any]) -> None:
        vector = np.asarray([signature["embedding"]], dtype=np.float32)
        self._matrix = vector if self._matrix is None else np.vstack([self._matrix, vector])
        self._ids.append(entry_id)
        self._keys.append((signature["detailed"], tuple(signature["numbers"])))

    def _closest(self, signature: dict[str, Any]) -> tuple[ObjectId | None, float]:
        if self._matrix is None:
            return None, 0.0
        similarities = self._matrix @ np.asarray(signature["embedding"], dtype=np.float32)
        wanted = (signature["detailed"], tuple(signature["numbers"]))
        for position in np.argsort(-similarities):
            if similarities[position] < settings.answer_cache_similarity:
                break
            if self._keys[position] == wanted:
                return self._ids[position], float(similarities[position])
        return None, 0.0

    # ---- public API ------------------------------------------------------

    async def lookup(self, signature: dict[str, Any], *, user_id: ObjectId) -> dict[str, Any] | None:
        """Return a cached result for this question, recording the hit."""
        try:
            await self._ensure_loaded()
            collection = self._collection()
            document = await collection.find_one({
                **self._fresh_filter(),
                "normalized_question": signature["normalized"],
                "detailed": signature["detailed"],
            })
            similarity = 1.0
            if document is None:
                entry_id, similarity = self._closest(signature)
                if entry_id is not None:
                    document = await collection.find_one({**self._fresh_filter(), "_id": entry_id})
            if document is None:
                return None

            now = datetime.now(timezone.utc)
            await collection.update_one(
                {"_id": document["_id"]},
                {"$inc": {"hit_count": 1}, "$set": {"last_asked_at": now}},
            )
            # Count each person once towards popularity.
            await collection.update_one(
                {"_id": document["_id"], "user_ids": {"$ne": user_id}},
                {"$push": {"user_ids": user_id}, "$inc": {"user_count": 1}},
            )
        except PyMongoError as exc:
            raise AnswerCacheUnavailable("Answer cache lookup failed.") from exc

        logger.info(
            "Answer cache hit (similarity %.3f) for cached question %r.",
            similarity, document.get("question"),
        )
        return dict(document["result"])

    async def store(
        self, question: str, signature: dict[str, Any], result: dict[str, Any],
        *, user_id: ObjectId,
    ) -> None:
        if not is_cacheable(result):
            return
        now = datetime.now(timezone.utc)
        document = {
            "question": question,
            "normalized_question": signature["normalized"],
            "detailed": signature["detailed"],
            "numbers": signature["numbers"],
            "embedding": signature["embedding"],
            "result": {field: result.get(field, []) for field in CACHED_FIELDS},
            "version": CACHE_VERSION,
            "hit_count": 0,
            "user_ids": [user_id],
            "user_count": 1,
            "created_at": now,
            "last_asked_at": now,
        }
        try:
            await self._ensure_loaded()
            inserted = await self._collection().insert_one(document)
        except DuplicateKeyError:
            return  # The same question was cached concurrently.
        except PyMongoError as exc:
            raise AnswerCacheUnavailable("Answer could not be cached.") from exc
        self._remember(inserted.inserted_id, signature)

    async def popular_questions(self, limit: int) -> list[dict[str, Any]]:
        """Most-asked cached questions that several different people asked."""
        try:
            cursor = self._collection().find(
                {**self._fresh_filter(), "user_count": {"$gte": POPULAR_MIN_USERS}},
                {"question": 1, "hit_count": 1, "user_count": 1},
            ).sort([("user_count", DESCENDING), ("hit_count", DESCENDING)]).limit(limit)
            documents = await cursor.to_list(length=limit)
        except PyMongoError as exc:
            raise AnswerCacheUnavailable("Popular questions are unavailable.") from exc
        return [
            {"question": document["question"], "times_asked": document["hit_count"] + 1}
            for document in documents
        ]


answer_cache_service = AnswerCacheService()
