from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class PlateEntry(Base):
    __tablename__ = "plate_entries"
    id = Column(Integer, primary_key=True, index=True)
    plate = Column(String(64), index=True, nullable=False)
    confidence = Column(Float, nullable=True)
    image_path = Column(String(512), nullable=True)
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    processed = Column(Boolean, default=False)  # if additional processing needed
