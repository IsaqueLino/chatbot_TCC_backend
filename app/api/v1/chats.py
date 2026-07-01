from typing import List
import uuid
import json
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat import Chat
from app.models.message import Message
from app.models.sensor import SensorData
from app.schemas.chat import ChatCreate, ChatRead
from app.schemas.message import MessageCreate, MessageRead
from app.core.LLMs.agents.chatbot.agent import LangGraphAgent

router = APIRouter()


def _asks_for_chart(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    keywords = ["grafico", "gráfico", "chart", "plot", "visualizacao", "visualização"]
    return any(k in lowered for k in keywords)


def _has_chart_block(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"```\s*chart", text, flags=re.IGNORECASE))


def _build_chart_block(sensor_rows: list[SensorData]) -> str | None:
    if not sensor_rows:
        return None

    # Use one device (most recent) to keep the chart readable.
    target_device = sensor_rows[0].device_id
    device_rows = [r for r in sensor_rows if r.device_id == target_device][:20]
    if not device_rows:
        return None

    # Show oldest -> newest on x-axis.
    device_rows.reverse()

    chart_data = []
    for r in device_rows:
        ts = r.created_at.strftime("%H:%M") if r.created_at else "N/A"
        chart_data.append({
            "time": ts,
            "temperatura": round(float(r.temperature), 2),
            "umidadeAr": round(float(r.air_humidity), 2),
            "umidadeSolo": round(float(r.soil_moisture), 2),
            "ph": round(float(r.ph), 2),
        })

    payload = {
        "type": "line",
        "title": f"Tendência dos sensores - {target_device}",
        "data": chart_data,
        "xKey": "time",
        "series": [
            {"key": "temperatura", "name": "Temperatura (°C)", "color": "#db3a34"},
            {"key": "umidadeAr", "name": "Umidade do Ar (%)", "color": "#1d6fa4"},
            {"key": "umidadeSolo", "name": "Umidade do Solo (%)", "color": "#2f9e44"},
            {"key": "ph", "name": "pH", "color": "#9b59b6"},
        ],
    }

    chart_json = json.dumps(payload, ensure_ascii=False)
    return f"```chart\n{chart_json}\n```"


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
    user_msg = Message(chat_id=chat_id, role=payload.role, content=payload.content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    history = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .limit(40)
        .all()
    )
    agent_input = [MessageCreate(role=m.role, content=m.content) for m in history]

    sensor_rows = (
        db.query(SensorData)
        .order_by(SensorData.created_at.desc())
        .limit(60)
        .all()
    )
    context = ""
    if sensor_rows:
        by_device = {}
        for row in sensor_rows:
            by_device.setdefault(row.device_id, []).append(row)
        lines = ["Dados recentes dos sensores (mais recente primeiro):"]
        for dev, readings in by_device.items():
            lines.append(f"\nDispositivo: {dev}")
            for r in readings[:20]:
                ts = r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "N/A"
                lines.append(
                    f"  {ts}: Temp={r.temperature}°C, UmidAr={r.air_humidity}%, "
                    f"UmidSolo={r.soil_moisture}%, pH={r.ph}"
                )
        context = "\n".join(lines)

    try:
        agent = LangGraphAgent()
        resp = await agent.get_response(agent_input, session_id=str(chat_id), context=context)
        assistant_content = resp.get('response') if isinstance(resp, dict) else None
        if not assistant_content:
            assistant_content = "Desculpe, não consegui processar sua solicitação."

        # Fallback: if user requested a chart and the model did not return one,
        # append a valid chart block generated from recent sensor data.
        if _asks_for_chart(payload.content) and not _has_chart_block(assistant_content):
            chart_block = _build_chart_block(sensor_rows)
            if chart_block:
                assistant_content = (
                    f"{assistant_content}\n\n"
                    "Gráfico gerado automaticamente com os dados mais recentes:\n"
                    f"{chart_block}"
                )
    except Exception as e:
        from app.core.logger import logger
        import traceback
        logger.error('agent_error', extra={'error': str(e), 'trace': traceback.format_exc()})
        assistant_content = "Desculpe, ocorreu um erro ao processar sua solicitação."

    assistant_msg = Message(chat_id=chat_id, role="assistant", content=assistant_content)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return [user_msg, assistant_msg]
