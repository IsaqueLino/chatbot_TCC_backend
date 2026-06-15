import uuid
from typing import Optional
from sqlmodel import Field
from .base import BaseModel

class SensorData(BaseModel, table=True):
    __tablename__ = "sensor_data"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    device_id: str = Field(index=True)
    temperature: float
    air_humidity: float
    soil_moisture: float
    ph: float