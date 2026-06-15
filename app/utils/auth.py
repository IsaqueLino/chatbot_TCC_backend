import re
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from typing import Optional

from jose import (
    JWTError,
    jwt,
)

from app.core.config import settings
from app.core.logger import logger
from app.schemas.auth import Token
from app.utils.sanitization import sanitize_string


def create_access_token(
    thread_id: str, 
    expires_delta: Optional[timedelta] = None,
    user_id: Optional[object] = None,
    access_level: Optional[str] = None
) -> Token:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": thread_id,
        "exp": expire,
        "iat": datetime.now(UTC),
        "jti": sanitize_string(f"{thread_id}-{datetime.now(UTC).timestamp()}"),
    }
    
    if user_id is not None:
        try:
            to_encode["id"] = str(user_id)
        except Exception:
            to_encode["id"] = sanitize_string(str(user_id))
    if access_level is not None:
        to_encode["access_level"] = access_level

    secret = settings.JWT_SECRET_KEY or "dev-secret-change-me"
    algorithm = settings.JWT_ALGORITHM or "HS256"

    if not settings.JWT_SECRET_KEY:
        logger.warning("using_default_jwt_secret", extra={"note": "JWT_SECRET_KEY not set; using insecure default for development"})
    if not settings.JWT_ALGORITHM:
        logger.warning("using_default_jwt_algorithm", extra={"note": "JWT_ALGORITHM not set; using HS256"})

    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)

    logger.info("token_created", extra={"thread_id": thread_id, "expires_at": expire.isoformat()})

    return Token(access_token=encoded_jwt, expires_at=expire)


def verify_token(token: str) -> Optional[dict]:
    if not token or not isinstance(token, str):
        logger.warning("token_invalid_format")
        raise ValueError("Token must be a non-empty string")

    if not re.match(r"^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$", token):
        logger.warning("token_suspicious_format")
        raise ValueError("Token format is invalid - expected JWT format")

    secret = settings.JWT_SECRET_KEY or "dev-secret-change-me"
    algorithm = settings.JWT_ALGORITHM or "HS256"

    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        logger.info("token_verified", extra={"token_sub": payload.get("sub")})
        return payload

    except JWTError as e:
        logger.error("token_verification_failed", extra={"error": str(e)})
        return None