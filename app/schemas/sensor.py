from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SensorDataCreate(BaseModel):
    device_id: str
    temperature: float
    air_humidity: float
    soil_moisture: float
    ph: float

class SensorDataRead(BaseModel):
    id: UUID
    device_id: str
    temperature: float
    air_humidity: float
    soil_moisture: float
    ph: float
    created_at: datetime

    class Config:
        from_attributes = True