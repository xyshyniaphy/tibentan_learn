import uuid
import asyncio
from datetime import datetime
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job, Word, Output
from app.schemas import JobCreate, JobResponse, ProgressResponse
from app.services.tibetan_parser import process_tibetan_text_async, get_title_from_text
from app.services.html_generator import generate_tutorial_html
from app.utils.ip_check import is_ip_allowed

router = APIRouter(prefix="/api", tags=["api"])


def run_process_job(job_id: str, db_url: str):
    """Sync wrapper to run the async job processing."""
    asyncio.run(process_job_async(job_id, db_url))


async def process_job_async(job_id: str, db_url: str):
    """Async background task to process a translation job."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        # Process text: segment and translate in one step
        translations = await process_tibetan_text_async(job.input_text)

        if not translations:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.commit()
            return

        job.total_words = len(translations)
        db.commit()

        # Store words with translations
        for idx, trans in enumerate(translations):
            db_word = Word(
                job_id=job_id,
                word_order=trans.get("order", idx),
                tibetan_word=trans.get("tibetan"),
                phonetic=trans.get("phonetic"),
                chinese=trans.get("chinese"),
                english=trans.get("english"),
                processed=True
            )
            db.add(db_word)
            job.processed_words += 1
            db.commit()

        # Mark as completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        import traceback
        traceback.print_exc()
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = f"{type(e).__name__}: {str(e)}"
            db.commit()
    finally:
        db.close()


@router.post("/generate")
async def generate(
    data: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submit text and start background job."""
    job_id = str(uuid.uuid4())
    title = get_title_from_text(data.text)

    job = Job(
        id=job_id,
        input_text=data.text,
        title=title,
        status="pending",
        total_words=0,
        processed_words=0
    )
    db.add(job)
    db.commit()

    # Start background processing
    from app.config import get_settings
    settings = get_settings()
    background_tasks.add_task(run_process_job, job_id, settings.database_url)

    return {"job_id": job_id, "redirect": f"/progress/{job_id}"}


@router.get("/progress/{job_id}", response_model=ProgressResponse)
async def get_progress(job_id: str, db: Session = Depends(get_db)):
    """Get progress status for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress_percent = 0.0
    if job.total_words > 0:
        progress_percent = (job.processed_words / job.total_words) * 100

    return ProgressResponse(
        job_id=job.id,
        status=job.status,
        total_words=job.total_words,
        processed_words=job.processed_words,
        progress_percent=round(progress_percent, 1)
    )


@router.get("/download/{job_id}")
async def download_html(job_id: str, db: Session = Depends(get_db)):
    """Download the generated HTML file (generated on-demand)."""
    from urllib.parse import quote

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")

    # Generate HTML on-demand
    words = db.query(Word).filter(Word.job_id == job_id).order_by(Word.word_order).all()
    html_content = generate_tutorial_html(words, job.title or "Tibetan Tutorial")

    # Use ASCII-safe filename with URL encoding for the Content-Disposition
    filename = f"tibetan_tutorial_{job_id[:8]}.html"
    encoded_filename = quote(job.title or "tibetan_tutorial")

    return PlainTextResponse(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}.html"
        }
    )


class DeleteRequest(BaseModel):
    job_ids: List[str]


@router.post("/jobs/delete")
async def delete_jobs(
    request: Request,
    data: DeleteRequest,
    db: Session = Depends(get_db)
):
    """Delete selected jobs."""
    if not is_ip_allowed(request):
        raise HTTPException(status_code=403, detail="Access denied: IP not whitelisted")

    from sqlalchemy import or_

    if not data.job_ids:
        raise HTTPException(status_code=400, detail="No jobs selected")

    deleted_count = 0
    for job_id in data.job_ids:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            # Cascade delete will handle words and outputs
            db.delete(job)
            deleted_count += 1

    db.commit()
    return {"deleted": deleted_count}
