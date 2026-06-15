import uuid
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
 
from app.core.logger import logger
from app.models.user import User
from app.core.config import settings
from app.schemas.auth import (
    SessionResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.database import DatabaseService
from dataclasses import dataclass
from typing import Optional as _Optional
from app.utils.auth import (
    create_access_token,
    verify_token,
)
from app.utils.sanitization import (
    sanitize_email,
    sanitize_string,
    validate_password_strength,
)

router = APIRouter()
security = HTTPBearer()
db_service = DatabaseService()


@dataclass
class TokenSession:
    id: uuid.UUID
    user_id: _Optional[uuid.UUID] = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    try:
        token = sanitize_string(credentials.credentials)
        payload = verify_token(token)

        if payload is None:
            logger.error("invalid_token", extra={"token_part": token[:10] + "..."})
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("id")
        try:
            user_uuid = uuid.UUID(str(user_id))
        except Exception:
            logger.error("invalid_token_uuid", extra={"token_part": token[:10] + "..."})
            raise HTTPException(status_code=422, detail="Invalid token format")

        user = await db_service.get_user(user_uuid)

        if user is None:
            logger.error("user_not_found", extra={"user_id": str(user_uuid)})
            raise HTTPException(
                status_code=404,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user
    except ValueError as ve:
        logger.error("token_validation_failed", exc_info=True, extra={"error": str(ve)})
        raise HTTPException(
            status_code=422,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenSession:
    try:
        token = sanitize_string(credentials.credentials)

        if not token:
            logger.error("session_id_not_found", extra={"token_part": ""})
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = verify_token(token)

        if payload is None:
            logger.error("invalid_session_token", extra={"token_part": token[:10] + "..."})
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        sub = payload.get("sub")
        user_id = payload.get("id")

        try:
            session_uuid = uuid.UUID(str(sub)) if sub else None
        except Exception:
            logger.error("invalid_session_sub", extra={"sub": str(sub)})
            raise HTTPException(status_code=422, detail="Invalid token subject")

        parsed_user_id = None
        if user_id:
            try:
                parsed_user_id = uuid.UUID(str(user_id))
            except Exception:
                parsed_user_id = None

        return TokenSession(id=session_uuid, user_id=parsed_user_id)
    except ValueError as ve:
        logger.error("token_validation_failed", exc_info=True, extra={"error": str(ve)})
        raise HTTPException(
            status_code=422,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form(default="password"),
):
    try:
        username = sanitize_string(username)
        password = sanitize_string(password)
        grant_type = sanitize_string(grant_type)

        if grant_type != "password":
            raise HTTPException(
                status_code=400,
                detail="Unsupported grant type. Only 'password' is supported.",
            )

        user = await db_service.get_user_by_email(username)
        if not user or not user.verify_password(password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(str(user.id), user_id=user.id, access_level=user.level.value)
        return TokenResponse(access_token=token.access_token, token_type="bearer", expires_at=token.expires_at)
    except ValueError as ve:
        logger.error("login_validation_failed", exc_info=True, extra={"error": str(ve)})
        raise HTTPException(status_code=422, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_unexpected_error", exc_info=True, extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/session", response_model=SessionResponse)
async def create_session(
    name: str = Form(default=""),
    user: User = Depends(get_current_user)
):
    try:
        session_id = uuid.uuid4()
        sanitized_name = sanitize_string(name) if name else ""

        token = create_access_token(str(session_id), user_id=user.id, access_level=user.level.value)

        logger.info(
            "session_created",
            extra={"session_id": str(session_id), "user_id": str(user.id), "name": sanitized_name, "expires_at": token.expires_at.isoformat()},
        )

        return SessionResponse(session_id=str(session_id), name=sanitized_name, token=token)
    except ValueError as ve:
        logger.error("session_creation_validation_failed", exc_info=True, extra={"error": str(ve), "user_id": user.id})
        raise HTTPException(status_code=422, detail=str(ve))


@router.patch("/session/{session_id}/name", response_model=SessionResponse)
async def update_session_name(
    session_id: str, name: str = Form(...), current_session: TokenSession = Depends(get_current_session)
):
    try:
        sanitized_session_id = sanitize_string(session_id)
        sanitized_name = sanitize_string(name)

        if str(current_session.id) != sanitized_session_id:
            raise HTTPException(status_code=403, detail="Cannot modify other sessions")

        raise HTTPException(status_code=410, detail="Session metadata is not persisted on the server (stateless JWTs)")
    except ValueError as ve:
        logger.error("session_update_validation_failed", exc_info=True, extra={"error": str(ve), "session_id": session_id})
        raise HTTPException(status_code=422, detail=str(ve))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, current_session: TokenSession = Depends(get_current_session)):
    try:
        sanitized_session_id = sanitize_string(session_id)
        logger.info(
            "delete_session_attempt",
            extra={"url_session_id": sanitized_session_id, "token_session_id": str(current_session.id), "match": (sanitized_session_id == str(current_session.id))},
        )

        if sanitized_session_id != str(current_session.id):
            logger.warning(
                "delete_session_mismatch",
                extra={"url_session_id": sanitized_session_id, "token_session_id": str(current_session.id)},
            )
            raise HTTPException(status_code=403, detail="Cannot delete other sessions")

        logger.info("session_delete_noop", extra={"session_id": session_id, "user_id": str(current_session.user_id)})
    except ValueError as ve:
        logger.error("session_deletion_validation_failed", exc_info=True, extra={"error": str(ve), "session_id": session_id})
        raise HTTPException(status_code=422, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("session_deletion_failed", exc_info=True, extra={"error": str(e), "session_id": session_id})
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.get("/sessions", response_model=List[SessionResponse])
async def get_user_sessions(user: User = Depends(get_current_user)):
    return []