from typing import List
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import desc

from app.schemas.chat import ChatRequest
from app.schemas.message import MessageCreate, MessageRead
from app.models.message import Message
from app.core.LLMs.agents.chatbot.agent import LangGraphAgent

agent = LangGraphAgent()

async def process_chat_message(
    chat_request: ChatRequest,
    session_id: str,
    db: DbSession
) -> List[MessageRead]:
    chat_id = chat_request.chat_id

    for msg in chat_request.messages:
        db_msg = Message(chat_id=chat_id, role=msg.role, content=msg.content)
        db.add(db_msg)
        db.commit()
        db.refresh(db_msg)

    recent_db_messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(desc(Message.created_at))
        .limit(20)
        .all()
    )
    
    recent_db_messages.reverse()

    context_messages = [
        MessageCreate(role=m.role, content=m.content)
        for m in recent_db_messages
    ]

    agent_response = await agent.get_response(
        messages=context_messages,
        session_id=session_id
    )
    
    assistant_content = agent_response.get("response", "Desculpe, não consegui processar sua solicitação.")
    
    assistant_msg = Message(chat_id=chat_id, role="assistant", content=assistant_content)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return [MessageRead.from_orm(assistant_msg)]