from sqlmodel import Session, select
from typing import List
from app.models.sensor import SensorData
from app.schemas.sensor import SensorDataCreate

class SensorService:
    def __init__(self, session: Session):
        self.session = session

    def create_sensor_data(self, data_in: SensorDataCreate) -> SensorData:
        db_data = SensorData(**data_in.model_dump())
        self.session.add(db_data)
        self.session.commit()
        self.session.refresh(db_data)
        return db_data

    def get_sensor_data_by_device(self, device_id: str, limit: int = 100) -> List[SensorData]:
        statement = select(SensorData).where(SensorData.device_id == device_id).order_by(SensorData.created_at.desc()).limit(limit)
        return self.session.exec(statement).all()