import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import (
    Any,
    Dict,
)

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    Request,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.limiter import limiter
from app.core.logger import logger
from app.core.middleware import MetricsMiddleware
from app.services.database import database_service
from fastapi import Body
from scripts.create_admin import create_admin_user
import sys, asyncio

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info("application_startup", extra={"project_name": settings.APP_NAME, "version": settings.VERSION, "api_prefix": settings.API_V1_STR})
    # Check database connectivity but do NOT run migrations or create admin user
    try:
        healthy = await database_service.health_check()
        if healthy:
            logger.info("database_connectivity_ok")
        else:
            logger.warning("database_unreachable", extra={"note": "Database is not reachable on startup"})
    except Exception as e:
        logger.error("database_health_check_failed_on_startup", extra={"error": str(e)})

    # Attempt to create admin user if script exists; failures are logged but do not stop startup
    try:
        await create_admin_user()
        logger.info("create_admin_completed")
    except Exception as e:
        logger.warning("create_admin_failed_on_startup", extra={"error": str(e)})

    yield
    logger.info("application_shutdown")


fastapi_app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


# Add custom metrics middleware
fastapi_app.add_middleware(MetricsMiddleware)

# Set up rate limiter exception handler
fastapi_app.state.limiter = limiter
fastapi_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Add validation exception handler
@fastapi_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors from request data.

    Args:
        request: The request that caused the validation error
        exc: The validation error

    Returns:
        JSONResponse: A formatted error response
    """
    # Log the validation error
    logger.error(
        "validation_error",
        extra={"client_host": request.client.host if request.client else "unknown", "path": request.url.path, "errors": str(exc.errors())},
    )

    # Format the errors to be more user-friendly
    formatted_errors = []
    for error in exc.errors():
        loc = " -> ".join([str(loc_part) for loc_part in error["loc"] if loc_part != "body"])
        formatted_errors.append({"field": loc, "message": error["msg"]})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": formatted_errors},
    )


# Global exception handler to ensure all uncaught exceptions are logged
@fastapi_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", exc_info=True, extra={"path": request.url.path, "method": request.method, "error": str(exc)})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Set up CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for logo storage
# __file__ está em app/main.py, então parent.parent vai para backend/
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(os.path.join(static_dir, "logos"), exist_ok=True)
fastapi_app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API router
fastapi_app.include_router(api_router, prefix=settings.API_V1_STR)


@fastapi_app.get("/")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["root"][0])
async def root(request: Request):
    """Root endpoint returning basic API information."""
    logger.info("root_endpoint_called")
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT.value,
        "swagger_url": "/docs",
        "redoc_url": "/redoc",
    }


@fastapi_app.get("/health")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["health"][0])
async def health_check(request: Request) -> Dict[str, Any]:
    """Health check endpoint with environment-specific information.

    Returns:
        Dict[str, Any]: Health status information
    """
    logger.info("health_check_called")

    # Check database connectivity
    db_healthy = await database_service.health_check()

    response = {
        "status": "healthy" if db_healthy else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT.value,
        "components": {"api": "healthy", "database": "healthy" if db_healthy else "unhealthy"},
        "timestamp": datetime.now().isoformat(),
    }

    # If DB is unhealthy, set the appropriate status code
    status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=response, status_code=status_code)


# Export the FastAPI ASGI application instance under both `app` and `application`.
# This avoids ambiguity where importers treat `app` as a factory function.
app = fastapi_app
application = fastapi_app


# Backwards-compatible endpoint used by the frontend sidebar user modal
@fastapi_app.put("/update_user")
async def update_user_endpoint(payload: dict = Body(...)):
    """Update user's name and/or password.

    Expected payload: { "id": str (UUID), "username": str (optional), "password": str (optional) }
    """
    try:
        import uuid as _uuid
        user_id = _uuid.UUID(str(payload.get("id")))
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid or missing user id"})

    username = payload.get("username")
    password = payload.get("password")

    updated = await database_service.update_user_info(user_id, name=username, password=password)
    if not updated:
        return JSONResponse(status_code=404, content={"detail": "User not found"})

    return JSONResponse(status_code=200, content={"detail": "User updated"})
