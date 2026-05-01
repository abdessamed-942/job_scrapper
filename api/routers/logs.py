from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import CrawlLog
from schemas import CrawlLogOut
from auth import verify_api_key

router = APIRouter(prefix="/crawl-logs", tags=["Crawl Logs"])

@router.get("/", response_model=List[CrawlLogOut])
def list_logs(
    db:        Session       = Depends(get_db),
    _:         str           = Depends(verify_api_key),
    source_id: Optional[int] = Query(None),
    status:    Optional[str] = Query(None),
    page:      int           = Query(1, ge=1),
    limit:     int           = Query(20, le=100),
):
    q = db.query(CrawlLog)
    if source_id: q = q.filter(CrawlLog.source_id == source_id)
    if status:    q = q.filter(CrawlLog.status == status)
    return q.order_by(CrawlLog.started_at.desc()).offset((page-1)*limit).limit(limit).all()
