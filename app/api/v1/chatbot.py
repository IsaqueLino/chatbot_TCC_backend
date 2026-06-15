from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session as DbSession

from app.api.v1.auth import get_current_session, TokenSession
from app.core.limiter import limiter
from app.core.config import settings
from app.core.logger import logger
from app.schemas.chat import ChatRequest, ChatResponse
from app.core.database import get_db
from app.services.chat import process_chat_message

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    session: TokenSession = Depends(get_current_session),
    db: DbSession = Depends(get_db),
):
    try:
        response_messages = await process_chat_message(
            chat_request=chat_request,
            session_id=str(session.id),
            db=db
        )
        return ChatResponse(messages=response_messages)
    except Exception as e:
        logger.error("chat_request_failed", exc_info=True, extra={"session_id": str(session.id), "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))