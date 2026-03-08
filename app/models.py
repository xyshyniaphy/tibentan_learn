from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    input_text = Column(Text, nullable=False)
    title = Column(String)
    status = Column(String, default="pending")
    total_words = Column(Integer, default=0)
    processed_words = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    words = relationship("Word", back_populates="job", cascade="all, delete-orphan")
    output = relationship("Output", back_populates="job", uselist=False, cascade="all, delete-orphan")


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    word_order = Column(Integer, nullable=False)
    tibetan_word = Column(String, nullable=False)
    phonetic = Column(String)
    chinese = Column(String)
    english = Column(String)
    pos = Column(String)  # part of speech
    processed = Column(Boolean, default=False)

    job = relationship("Job", back_populates="words")


class Output(Base):
    __tablename__ = "outputs"

    job_id = Column(String, ForeignKey("jobs.id"), primary_key=True)
    html_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="output")
