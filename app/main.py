from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from . import models, schemas, database, crud, utils, config

# create DB tables if not exists
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Parking ALPR API")

# Dependency
def get_db():
    yield from database.get_db()

@app.get("/api/status", response_model=schemas.StatusResponse)
def get_status(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    utils.verify_token(authorization)
    occupied = crud.get_occupied_count(db)
    free = max(config.TOTAL_SLOTS - occupied, 0)
    # open_gate logic can be added: e.g. open if free>0 else False
    open_gate = free > 0
    return schemas.StatusResponse(total_slots=config.TOTAL_SLOTS, occupied=occupied, free=free, open_gate=open_gate)

@app.post("/api/entry", response_model=schemas.PlateOut)
def post_entry(payload: schemas.EntryIn, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    utils.verify_token(authorization)
    # timestamp optional
    ts = payload.timestamp or datetime.utcnow()
    entry = crud.create_entry(db, plate=payload.plate, image_base64=payload.image_base64, confidence=payload.confidence, timestamp=ts)
    return entry

@app.post("/api/exit", response_model=schemas.PlateOut)
def post_exit(payload: schemas.ExitIn, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    utils.verify_token(authorization)
    ts = payload.timestamp or datetime.utcnow()
    entry = crud.close_entry(db, plate=payload.plate, timestamp=ts)
    if entry is None:
        raise HTTPException(status_code=404, detail="Open entry for plate not found")
    return entry

@app.get("/api/plates", response_model=list[schemas.PlateOut])
def get_plates(limit: int = 100, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    utils.verify_token(authorization)
    entries = crud.list_entries(db, limit=limit)
    return entries
