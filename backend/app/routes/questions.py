"""Frequently asked questions, drawn from the answer cache."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.security import get_current_user
from app.models.user import User
from app.services.answer_cache_service import AnswerCacheUnavailable, answer_cache_service


logger = logging.getLogger(__name__)
router = APIRouter()


class PopularQuestion(BaseModel):
    question: str
    times_asked: int


@router.get("/popular", response_model=list[PopularQuestion], tags=["questions"])
async def popular_questions(
    limit: int = Query(default=4, ge=1, le=20),
    current_user: User = Depends(get_current_user),
) -> list[PopularQuestion]:
    try:
        questions = await answer_cache_service.popular_questions(limit)
    except AnswerCacheUnavailable as exc:
        logger.warning("Popular questions are unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Popular questions are unavailable.",
        ) from exc
    return [PopularQuestion(**question) for question in questions]
