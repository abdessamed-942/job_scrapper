from fastapi import FastAPI
from routers import jobs, sources, logs, stats

app = FastAPI(
    title="Job Scrapper API",
    description="Admin API for managing scraped jobs from Algerian job sites",
    version="1.0.0"
)

app.include_router(jobs.router)
app.include_router(sources.router)
app.include_router(logs.router)
app.include_router(stats.router)

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Job Scrapper API is running 🚀"}
