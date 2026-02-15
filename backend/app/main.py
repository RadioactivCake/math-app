import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE importing services
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, seed_db, DATABASE_PATH
from .routers import topics, problems, submissions

# Create FastAPI app
app = FastAPI(
    title="Math Feedback API",
    description="API for evaluating student math solutions and providing feedback",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics.router)
app.include_router(problems.router)
app.include_router(submissions.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    if not DATABASE_PATH.exists():
        print("Initializing database...")
        init_db()
        seed_db()
    else:
        print("Database already exists.")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Math Feedback API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "topics": "/api/topics",
            "problems": "/api/problems/{id}",
            "submissions": "/api/submissions"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from .services.ocr import vision_service
    from .services.evaluator import evaluator_service

    return {
        "status": "healthy",
        "database": DATABASE_PATH.exists(),
        "vision_configured": vision_service.is_configured(),
        "evaluator_configured": evaluator_service.is_configured()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
