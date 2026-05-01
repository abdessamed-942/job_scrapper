from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Job, Source, CrawlLog
from schemas import StatsOut
from auth import verify_api_key

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    total_jobs    = db.query(Job).count()
    active_jobs   = db.query(Job).filter(Job.is_active == True).count()
    inactive_jobs = db.query(Job).filter(Job.is_active == False).count()
    total_sources = db.query(Source).count()
    total_crawls  = db.query(CrawlLog).count()
    last_crawl    = db.query(func.max(CrawlLog.started_at)).scalar()
    return StatsOut(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        inactive_jobs=inactive_jobs,
        total_sources=total_sources,
        total_crawls=total_crawls,
        last_crawl_at=last_crawl
    )
