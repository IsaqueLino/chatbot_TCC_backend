from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat import Chat
from app.models.message import Message
from app.schemas.chat import ChatCreate, ChatRead
from app.schemas.message import MessageCreate, MessageRead
from app.core.LLMs.agents.chatbot.agent import LangGraphAgent

router = APIRouter()


@router.post("/add_chat", response_model=ChatRead)
def add_chat(payload: ChatCreate, db: Session = Depends(get_db)):
    chat = Chat(title=payload.title, user_id=payload.user_id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/get_chats/{user_id}", response_model=List[ChatRead])
def get_chats(user_id: uuid.UUID, db: Session = Depends(get_db)):
    chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).all()
    return chats


@router.delete("/delete_chat/{chat_id}")
def delete_chat(chat_id: uuid.UUID, db: Session = Depends(get_db)):
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # delete messages first
    db.query(Message).filter(Message.chat_id == chat_id).delete()
    db.delete(chat)
    db.commit()

    return {"detail": "deleted"}


@router.put("/update_chat_title/{chat_id}", response_model=ChatRead)
def update_chat_title(chat_id: uuid.UUID, payload: ChatCreate, db: Session = Depends(get_db)):
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat.title = payload.title
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/{chat_id}/messages", response_model=List[MessageRead])
def fetch_messages(chat_id: uuid.UUID, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()
    return msgs


@router.post("/{chat_id}/messages", response_model=List[MessageRead])
async def post_message(chat_id: uuid.UUID, payload: MessageCreate, db: Session = Depends(get_db)):
    # Create and persist user message
    user_msg = Message(chat_id=chat_id, role=payload.role, content=payload.content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Call the LLM agent to generate an assistant response
    try:
        agent = LangGraphAgent()
        # Use the pydantic schema for messages so the agent sees .role and .content
        agent_input = [MessageCreate(role=payload.role, content=payload.content)]
        resp = await agent.get_response(agent_input, session_id=str(chat_id), user_id=None)
        assistant_content = resp.get('response') if isinstance(resp, dict) else None
        if not assistant_content:
            assistant_content = f"Resposta automática: {payload.content}"
    except Exception as e:
        # Log and fallback to simple echo so the endpoint remains functional
        from app.core.logger import logger
        import traceback
        tb = traceback.format_exc()
        logger.error('agent_error', extra={'error': str(e), 'trace': tb})
        assistant_content = f"Resposta automática: {payload.content}"

    assistant_msg = Message(chat_id=chat_id, role="assistant", content=assistant_content)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return [user_msg, assistant_msg]
