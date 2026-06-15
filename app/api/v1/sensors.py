from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List
from app.core.database import get_session
from app.schemas.sensor import SensorDataCreate, SensorDataRead
from app.services.sensor import SensorService

router = APIRouter()

@router.post("/data", response_model=SensorDataRead)
def create_sensor_data(data_in: SensorDataCreate, session: Session = Depends(get_session)):
    service = SensorService(session)
    return service.create_sensor_data(data_in)

@router.get("/data/{device_id}", response_model=List[SensorDataRead])
def get_sensor_data(device_id: str, limit: int = 100, session: Session = Depends(get_session)):
    service = SensorService(session)
    return service.get_sensor_data_by_device(device_id, limit)