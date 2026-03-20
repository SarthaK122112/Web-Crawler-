"""
Main FastAPI application entry point.

Initializes the FastAPI server, registers API routes,
configures CORS middleware, and sets up the database on startup.

Run with:
    uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.routes import router
from backend.database.models import init_db
import os

app = FastAPI(
    title="Dark Pattern Detector",
    description="AI-driven semantic web crawler for detecting deceptive design patterns",
    version="1.0.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve screenshots as static files
screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=screenshots_dir), name="screenshots")

# Register API routes
app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup():
    """Initialize the database on application startup."""
    init_db()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "running", "service": "Dark Pattern Detector API"}
