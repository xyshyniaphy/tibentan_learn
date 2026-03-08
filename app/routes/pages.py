from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job, Word
from app.services.html_generator import generate_tutorial_html
from app.utils.ip_check import is_ip_allowed

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Homepage - list all jobs with status."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return request.app.state.templates.TemplateResponse(
        "index.html",
        {"request": request, "jobs": jobs}
    )


@router.get("/input", response_class=HTMLResponse)
async def input_page(request: Request):
    """Page to input Tibetan text."""
    if not is_ip_allowed(request):
        return request.app.state.templates.TemplateResponse(
            "403.html",
            {"request": request},
            status_code=403
        )
    return request.app.state.templates.TemplateResponse(
        "input.html",
        {"request": request}
    )


@router.get("/progress/{job_id}", response_class=HTMLResponse)
async def progress_page(request: Request, job_id: str, db: Session = Depends(get_db)):
    """Progress page for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return request.app.state.templates.TemplateResponse(
        "progress.html",
        {"request": request, "job": job}
    )


@router.get("/result/{job_id}", response_class=HTMLResponse)
async def result_page(request: Request, job_id: str, db: Session = Depends(get_db)):
    """View generated HTML result."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")

    # Get words and generate HTML on-demand
    words = db.query(Word).filter(Word.job_id == job_id).order_by(Word.word_order).all()
    html_content = generate_tutorial_html(words, job.title or "Tibetan Tutorial")

    return request.app.state.templates.TemplateResponse(
        "result.html",
        {"request": request, "job": job, "html_content": html_content}
    )
