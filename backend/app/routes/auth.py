"""HTTP endpoints for user registration."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.core.security import (
    TokenConfigurationError,
    create_access_token,
    get_current_user,
)
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    DuplicateUserError,
    DUMMY_PASSWORD_HASH,
    RegistrationUnavailable,
    auth_service,
    hash_password,
    verify_password,
)


logger = logging.getLogger(__name__)
router = APIRouter()


def _safe_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
)
async def register(request: RegisterRequest) -> UserResponse:
    try:
        hashed_password = await run_in_threadpool(
            hash_password, request.password.get_secret_value()
        )
        user = await auth_service.register_user(
            email=str(request.email),
            username=request.username,
            hashed_password=hashed_password,
        )
    except DuplicateUserError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RegistrationUnavailable as exc:
        logger.error("User registration is unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during user registration.")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during registration.",
        ) from exc

    return _safe_user_response(user)


@router.post("/login", response_model=AccessTokenResponse, tags=["auth"])
async def login(request: LoginRequest) -> AccessTokenResponse:
    try:
        user = await auth_service.get_user_by_identifier(request.username_or_email)
        stored_hash = user.hashed_password if user else DUMMY_PASSWORD_HASH
        password_matches = await run_in_threadpool(
            verify_password,
            request.password.get_secret_value(),
            stored_hash,
        )
        if user is None or not password_matches:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(str(user.id))
    except RegistrationUnavailable as exc:
        logger.error("User login is unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="User lookup is unavailable.") from exc
    except TokenConfigurationError as exc:
        logger.error("JWT configuration is unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Token authentication is not configured.",
        ) from exc

    return AccessTokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse, tags=["auth"])
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return _safe_user_response(user)
