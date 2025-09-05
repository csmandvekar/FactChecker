from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Import routers
# from api.routes import upload, analyze, reports, auth
# from api.routes import public
# from services.supabase import init_supabase
# from core.database import init_db
print("--- Starting main.py ---")

print("Importing config...")
from core.config import settings
print("...config imported.")

print("Importing database module...")
from core.database import init_db
print("...database module imported.")

print("Importing supabase module...")
from services.supabase import init_supabase
print("...supabase module imported.")

print("Importing routers...")
from api.routes import upload
print("upload")
from api.routes import analyze
print("analyze")
from api.routes import reports
print("reports")
from api.routes import auth
print("auth")
from api.routes import public
from api.routes import intelligence
print("...routers imported.")

# Create FastAPI app
app = FastAPI(
    title="DeepVerify Studio API",
    description="A forensic analysis platform for detecting deepfakes and document tampering",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("startup")

@app.on_event("startup")
async def on_startup():
    try:
        init_db()
        init_supabase()
        logger.info("Application startup complete: database initialized")
    except Exception as e:
        logger.exception(f"Startup failed: {e}")
        raise

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
# Keep `/api/token` and `/api/auth/*` consistent
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(public.router, tags=["public"])
app.include_router(intelligence.router, prefix="/api", tags=["intelligence"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "DeepVerify Studio API"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "DeepVerify Studio API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Serve static files (evidence, heatmaps, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    
