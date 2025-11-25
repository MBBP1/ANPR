import base64, os
from datetime import datetime
from sqlalchemy.orm import Session
from . import models, config

def get_occupied_count(db: Session):
    # Cars with entry_time set and exit_time NULL are currently parked
    return db.query(models.PlateEntry).filter(models.PlateEntry.exit_time.is_(None)).count()

def create_entry(db: Session, plate: str, image_base64: str = None, confidence: float = None, timestamp: datetime = None):
    image_path = None
    if image_base64:
        # save image to disk
        try:
            data = base64.b64decode(image_base64)
            fname = f"{plate}_{int(datetime.utcnow().timestamp())}.jpg"
            fpath = os.path.join(config.IMAGE_FOLDER, fname)
            with open(fpath, "wb") as f:
                f.write(data)
            image_path = fpath
        except Exception:
            image_path = None

    if timestamp is None:
        timestamp = datetime.utcnow()

    entry = models.PlateEntry(
        plate=plate,
        confidence=confidence,
        image_path=image_path,
        entry_time=timestamp
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def close_entry(db: Session, plate: str, timestamp: datetime = None):
    # find latest open entry for plate
    entry = db.query(models.PlateEntry).filter(
        models.PlateEntry.plate == plate,
        models.PlateEntry.exit_time.is_(None)
    ).order_by(models.PlateEntry.entry_time.desc()).first()

    if not entry:
        return None

    if timestamp is None:
        timestamp = datetime.utcnow()

    entry.exit_time = timestamp
    entry.duration_seconds = int((entry.exit_time - entry.entry_time).total_seconds())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def list_entries(db: Session, limit: int = 100):
    return db.query(models.PlateEntry).order_by(models.PlateEntry.entry_time.desc()).limit(limit).all()
