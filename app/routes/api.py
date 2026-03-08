import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job, Word, Output
from app.schemas import JobCreate, JobResponse, ProgressResponse
from app.services.tibetan_parser import extract_tibetan_words, get_title_from_text
from app.services.translator import translate_words
from app.services.html_generator import generate_tutorial_html

router = APIRouter(prefix="/api", tags=["api"])


def process_job(job_id: str, db_url: str):
    """Background task to process a translation job."""
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

        # Extract words
        words_data = extract_tibetan_words(job.input_text)
        job.total_words = len(words_data)

        if not words_data:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.commit()
            return

        db.commit()

        # Store words in database
        for order, word in words_data:
            db_word = Word(
                job_id=job_id,
                word_order=order,
                tibetan_word=word,
                processed=False
            )
            db.add(db_word)
        db.commit()

        # Get words to translate
        tibetan_words = [w for _, w in words_data]

        # Translate (run async function in sync context)
        translations = asyncio.run(translate_words(tibetan_words))

        # Update words with translations
        translation_map = {}
        for t in translations:
            tibetan_key = t.get("tibetan") or t.get("tibetan_word") or t.get("word")
            if tibetan_key:
                translation_map[tibetan_key] = t
        db_words = db.query(Word).filter(Word.job_id == job_id).order_by(Word.word_order).all()

        for db_word in db_words:
            if db_word.tibetan_word in translation_map:
                trans = translation_map[db_word.tibetan_word]
                db_word.phonetic = trans.get("phonetic")
                db_word.chinese = trans.get("chinese")
                db_word.english = trans.get("english")
                db_word.processed = True
                job.processed_words += 1
                db.commit()

        # Generate HTML
        db_words = db.query(Word).filter(Word.job_id == job_id).order_by(Word.word_order).all()
        html_content = generate_tutorial_html(db_words, job.title or "Tibetan Tutorial")

        output = Output(job_id=job_id, html_content=html_content)
        db.add(output)

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        import traceback
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
    background_tasks.add_task(process_job, job_id, settings.database_url)

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
    """Download the generated HTML file."""
    from urllib.parse import quote

    output = db.query(Output).filter(Output.job_id == job_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Result not found")

    job = db.query(Job).filter(Job.id == job_id).first()
    # Use ASCII-safe filename with URL encoding for the Content-Disposition
    filename = f"tibetan_tutorial_{job_id[:8]}.html"
    encoded_filename = quote(job.title or "tibetan_tutorial")

    return PlainTextResponse(
        content=output.html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}.html"
        }
    )
