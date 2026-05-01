from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import Job
from schemas import JobOut
from auth import verify_api_key

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/", response_model=List[JobOut])
def list_jobs(
    db:              Session       = Depends(get_db),
    _:               str           = Depends(verify_api_key),
    source_id:       Optional[int] = Query(None),
    location:        Optional[str] = Query(None),
    contract_type:   Optional[str] = Query(None),
    sector:          Optional[str] = Query(None),
    is_active:       Optional[bool]= Query(None),
    search:          Optional[str] = Query(None),
    page:            int           = Query(1, ge=1),
    limit:           int           = Query(20, le=100),
):
    q = db.query(Job)
    if source_id:     q = q.filter(Job.source_id == source_id)
    if location:      q = q.filter(Job.location.ilike(f"%{location}%"))
    if contract_type: q = q.filter(Job.contract_type.ilike(f"%{contract_type}%"))
    if sector:        q = q.filter(Job.sector.ilike(f"%{sector}%"))
    if is_active is not None: q = q.filter(Job.is_active == is_active)
    if search:        q = q.filter(
        Job.title.ilike(f"%{search}%") | Job.company.ilike(f"%{search}%")
    )
    return q.order_by(Job.scraped_at.desc()).offset((page-1)*limit).limit(limit).all()

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.patch("/{job_id}/deactivate")
def deactivate_job(job_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_active = False
    db.commit()
    return {"message": f"Job {job_id} deactivated"}

@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted"}
