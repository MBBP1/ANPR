from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StatusResponse(BaseModel):
    total_slots: int
    occupied: int
    free: int
    open_gate: Optional[bool] = False

class EntryIn(BaseModel):
    plate: str
    timestamp: Optional[datetime] = None
    image_base64: Optional[str] = None
    confidence: Optional[float] = None

class ExitIn(BaseModel):
    plate: str
    timestamp: Optional[datetime] = None

class PlateOut(BaseModel):
    id: int
    plate: str
    confidence: Optional[float]
    image_path: Optional[str]
    entry_time: datetime
    exit_time: Optional[datetime]
    duration_seconds: Optional[int]

    class Config:
        orm_mode = True
