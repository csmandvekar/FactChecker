from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging
from datetime import datetime

from core.database import get_db
from models.announcement import Announcement
from models.company_financial import CompanyFinancial
from services.intelligence_analysis import IntelligenceAnalysisService
from services.intelligence_scraper import IntelligenceScraperService
from services.intelligence_fact_checker import FactCheckerService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
analysis_service = IntelligenceAnalysisService()
scraper_service = IntelligenceScraperService()
fact_checker_service = FactCheckerService()


@router.get("/intelligence/announcements")
async def get_announcements(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    company_symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Fetch all analyzed announcements for the main list view"""
    try:
        query = db.query(Announcement)
        
        if status:
            query = query.filter(Announcement.status == status)
        if company_symbol:
            query = query.filter(Announcement.company_symbol == company_symbol)
            
        announcements = query.order_by(Announcement.announcement_date.desc()).offset(skip).limit(limit).all()
        
        return {
            "announcements": [
                {
                    "id": ann.id,
                    "company_name": ann.company_name,
                    "company_symbol": ann.company_symbol,
                    "title": ann.title,
                    "announcement_date": ann.announcement_date.isoformat(),
                    "credibility_score": ann.credibility_score,
                    "status": ann.status,
                    "analysis_summary": ann.analysis_summary
                }
                for ann in announcements
            ],
            "total": query.count()
        }
    except Exception as e:
        logger.error(f"Error fetching announcements: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch announcements")


@router.get("/intelligence/announcements/{announcement_id}")
async def get_announcement_details(
    announcement_id: int,
    db: Session = Depends(get_db)
):
    """Fetch detailed analysis for a specific announcement"""
    try:
        announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
        
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
            
        return {
            "id": announcement.id,
            "company_name": announcement.company_name,
            "company_symbol": announcement.company_symbol,
            "title": announcement.title,
            "announcement_date": announcement.announcement_date.isoformat(),
            "pdf_url": announcement.pdf_url,
            "storage_path": announcement.storage_path,
            "full_text": announcement.full_text,
            "status": announcement.status,
            "credibility_score": announcement.credibility_score,
            "analysis_summary": announcement.analysis_summary,
            "created_at": announcement.created_at.isoformat(),
            "updated_at": announcement.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching announcement details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch announcement details")


@router.post("/intelligence/fact-check")
async def fact_check_content(
    background_tasks: BackgroundTasks,
    text_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Handle user uploads for the fact-checker"""
    try:
        if not text_content and not file:
            raise HTTPException(status_code=400, detail="Either text content or file must be provided")
            
        # Extract text from file if provided
        content_to_check = text_content
        if file:
            if file.content_type == "application/pdf":
                # Extract text from PDF
                content_to_check = await fact_checker_service.extract_pdf_text(file)
            elif file.content_type.startswith("text/"):
                content_to_check = await file.read()
                content_to_check = content_to_check.decode('utf-8')
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
        
        if not content_to_check:
            raise HTTPException(status_code=400, detail="No content to analyze")
            
        # Perform fact-checking
        result = await fact_checker_service.check_content(content_to_check, db)
        
        return {
            "status": "success",
            "verification_result": result["verification_status"],
            "confidence_score": result["confidence_score"],
            "evidence": result["evidence"],
            "analysis_details": result["analysis_details"],
            "recommendations": result["recommendations"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fact-checking: {e}")
        raise HTTPException(status_code=500, detail="Fact-checking failed")


@router.post("/intelligence/run-scraper")
async def run_scraper(
    background_tasks: BackgroundTasks,
    secret_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """Secure endpoint for cron job to trigger scraping"""
    try:
        # Simple secret key validation (in production, use proper authentication)
        expected_key = "your-secret-scraper-key"  # Should be in environment variables
        if secret_key != expected_key:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
        # Run scraper in background
        background_tasks.add_task(scraper_service.run_full_scrape, db)
        
        return {
            "status": "success",
            "message": "Scraper started successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scraper: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scraper")


@router.get("/intelligence/companies")
async def get_companies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of companies with financial data"""
    try:
        companies = db.query(CompanyFinancial).offset(skip).limit(limit).all()
        
        return {
            "companies": [
                {
                    "id": comp.id,
                    "company_symbol": comp.company_symbol,
                    "company_name": comp.company_name,
                    "last_quarter_revenue_cr": comp.last_quarter_revenue_cr,
                    "last_quarter_profit_cr": comp.last_quarter_profit_cr,
                    "market_cap_cr": comp.market_cap_cr,
                    "pe_ratio": comp.pe_ratio,
                    "last_updated": comp.last_updated.isoformat()
                }
                for comp in companies
            ],
            "total": db.query(CompanyFinancial).count()
        }
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch companies")


@router.post("/intelligence/analyze/{announcement_id}")
async def analyze_announcement(
    announcement_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually trigger analysis for a specific announcement"""
    try:
        announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
        
        if not announcement:
            raise HTTPException(status_code=404, detail="Announcement not found")
            
        # Run analysis in background
        background_tasks.add_task(analysis_service.analyze_announcement, announcement, db)
        
        return {
            "status": "success",
            "message": f"Analysis started for announcement {announcement_id}",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")


@router.get("/intelligence/stats")
async def get_intelligence_stats(db: Session = Depends(get_db)):
    """Get statistics for the intelligence module"""
    try:
        total_announcements = db.query(Announcement).count()
        analyzed_announcements = db.query(Announcement).filter(Announcement.status == 'analyzed').count()
        pending_announcements = db.query(Announcement).filter(Announcement.status == 'pending').count()
        total_companies = db.query(CompanyFinancial).count()
        
        # Get average credibility score
        avg_score = db.query(Announcement.credibility_score).filter(
            Announcement.credibility_score.isnot(None)
        ).all()
        avg_credibility = sum([score[0] for score in avg_score]) / len(avg_score) if avg_score else 0
        
        return {
            "total_announcements": total_announcements,
            "analyzed_announcements": analyzed_announcements,
            "pending_announcements": pending_announcements,
            "total_companies": total_companies,
            "average_credibility_score": round(avg_credibility, 2),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")
