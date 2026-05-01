from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Source
from schemas import SourceOut
from auth import verify_api_key

router = APIRouter(prefix="/sources", tags=["Sources"])

@router.get("/", response_model=List[SourceOut])
def list_sources(db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    return db.query(Source).all()

@router.patch("/{source_id}/activate")
def activate_source(source_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.is_active = True
    db.commit()
    return {"message": f"Source {source.name} activated"}

@router.patch("/{source_id}/deactivate")
def deactivate_source(source_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.is_active = False
    db.commit()
    return {"message": f"Source {source.name} deactivated"}
