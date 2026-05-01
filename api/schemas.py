from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class JobOut(BaseModel):
    id:               int
    title:            Optional[str]
    company:          Optional[str]
    location:         Optional[str]
    contract_type:    Optional[str]
    sector:           Optional[str]
    category:         Optional[str]
    experience_level: Optional[str]
    education_level:  Optional[str]
    salary:           Optional[str]
    url:              Optional[str]
    published_at:     Optional[datetime]
    scraped_at:       Optional[datetime]
    is_active:        bool
    source_id:        Optional[int]
    class Config:
        from_attributes = True

class SourceOut(BaseModel):
    id:                   int
    name:                 str
    is_active:            Optional[bool]
    last_crawl_at:        Optional[datetime]
    last_start_at:        Optional[datetime]
    execution_time:       Optional[int]
    last_crawl_count:     Optional[int]
    last_duplicate_count: Optional[int]
    total_jobs_count:     Optional[int]
    class Config:
        from_attributes = True

class CrawlLogOut(BaseModel):
    id:             int
    source_id:      Optional[int]
    started_at:     Optional[datetime]
    finished_at:    Optional[datetime]
    status:         Optional[str]
    new_jobs:       Optional[int]
    duplicate_jobs: Optional[int]
    total_jobs:     Optional[int]
    execution_time: Optional[int]
    error_message:  Optional[str]
    class Config:
        from_attributes = True

class StatsOut(BaseModel):
    total_jobs:    int
    active_jobs:   int
    inactive_jobs: int
    total_sources: int
    total_crawls:  int
    last_crawl_at: Optional[datetime]
