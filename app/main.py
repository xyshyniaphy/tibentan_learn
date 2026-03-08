from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os

from app.database import init_db
from app.routes import pages, api


# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: Nothing to clean up


app = FastAPI(
    title="Tibetan Learning Tutorial Generator",
    description="Generate word-by-word Tibetan language learning materials",
    version="1.0.0",
    lifespan=lifespan
)

# Setup templates
templates = Jinja2Templates(directory="app/templates")
app.state.templates = templates

# Include routers
app.include_router(pages.router)
app.include_router(api.router)
