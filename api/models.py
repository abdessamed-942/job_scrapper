from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Source(Base):
    __tablename__ = "sources"
    id                   = Column(Integer, primary_key=True)
    name                 = Column(String(50), unique=True, nullable=False)
    is_active            = Column(Boolean, default=True)
    last_crawl_at        = Column(DateTime)
    last_start_at        = Column(DateTime)
    execution_time       = Column(Integer)
    last_crawl_count     = Column(Integer, default=0)
    last_duplicate_count = Column(Integer, default=0)
    total_jobs_count     = Column(Integer, default=0)
    jobs                 = relationship("Job", back_populates="source")
    crawl_logs           = relationship("CrawlLog", back_populates="source")

class Job(Base):
    __tablename__ = "jobs"
    id               = Column(Integer, primary_key=True)
    source_id        = Column(Integer, ForeignKey("sources.id"))
    external_id      = Column(String(255))
    url              = Column(Text)
    title            = Column(String(500), nullable=False)
    company          = Column(String(255))
    description      = Column(Text)
    location         = Column(String(255))
    contract_type    = Column(String(100))
    sector           = Column(String(255))
    category         = Column(String(255))
    experience_level = Column(String(100))
    education_level  = Column(String(100))
    salary           = Column(String(100))
    languages        = Column(Text)
    skills           = Column(Text)
    published_at     = Column(DateTime)
    expires_at       = Column(DateTime)
    scraped_at       = Column(DateTime, server_default=func.now())
    is_active        = Column(Boolean, default=True)
    fingerprint      = Column(String(32), unique=True)
    source           = relationship("Source", back_populates="jobs")

class CrawlLog(Base):
    __tablename__ = "crawl_logs"
    id             = Column(Integer, primary_key=True)
    source_id      = Column(Integer, ForeignKey("sources.id"))
    started_at     = Column(DateTime, nullable=False)
    finished_at    = Column(DateTime)
    status         = Column(String(20), default="running")
    new_jobs       = Column(Integer, default=0)
    duplicate_jobs = Column(Integer, default=0)
    total_jobs     = Column(Integer, default=0)
    execution_time = Column(Integer, default=0)
    error_message  = Column(Text)
    log_output     = Column(Text)
    source         = relationship("Source", back_populates="crawl_logs")
