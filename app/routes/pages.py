from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job, Output
from app.services.html_generator import generate_tutorial_html

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

    output = db.query(Output).filter(Output.job_id == job_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="Result not found")

    return request.app.state.templates.TemplateResponse(
        "result.html",
        {"request": request, "job": job, "html_content": output.html_content}
    )
