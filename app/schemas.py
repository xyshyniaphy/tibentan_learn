from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class JobCreate(BaseModel):
    text: str


class JobResponse(BaseModel):
    id: str
    title: Optional[str]
    status: str
    total_words: int
    processed_words: int
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class WordResponse(BaseModel):
    tibetan_word: str
    phonetic: Optional[str]
    chinese: Optional[str]
    english: Optional[str]

    class Config:
        from_attributes = True


class ProgressResponse(BaseModel):
    job_id: str
    status: str
    total_words: int
    processed_words: int
    progress_percent: float
