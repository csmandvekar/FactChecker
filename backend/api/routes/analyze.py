from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from core.database import get_db
from models.file import File as FileModel
from models.report import Report as ReportModel
from services.pdf_forensics import PDFForensicsService
from services.image_forensics import ImageForensicsService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize forensic services
pdf_service = PDFForensicsService()
image_service = ImageForensicsService()

@router.post("/analyze/pdf/{file_id}")
async def analyze_pdf(
    file_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Analyze PDF file for forensic evidence
    
    - **file_id**: Unique file identifier
    - Runs PDF forensics analysis in background
    """
    try:
        # Get file from database
        db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
        
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        if db_file.file_type != "pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a PDF"
            )
        
        if db_file.analysis_status == "processing":
            return {
                "file_id": file_id,
                "status": "processing",
                "message": "PDF analysis already in progress"
            }
        
        # Update status to processing
        db_file.analysis_status = "processing"
        db.commit()
        
        # Start background analysis
        background_tasks.add_task(
            run_pdf_analysis,
            file_id,
            db_file.storage_path
        )
        
        return {
            "file_id": file_id,
            "status": "processing",
            "message": "PDF analysis started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start PDF analysis"
        )

@router.post("/analyze/image/{file_id}")
async def analyze_image(
    file_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Analyze image file for forensic evidence
    
    - **file_id**: Unique file identifier
    - Runs ELA and CNN analysis in background
    """
    try:
        # Get file from database
        db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
        
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        if db_file.file_type != "image":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not an image"
            )
        
        if db_file.analysis_status == "processing":
            return {
                "file_id": file_id,
                "status": "processing",
                "message": "Image analysis already in progress"
            }
        
        # Update status to processing
        db_file.analysis_status = "processing"
        db.commit()
        
        # Start background analysis
        background_tasks.add_task(
            run_image_analysis,
            file_id,
            db_file.storage_path
        )
        
        return {
            "file_id": file_id,
            "status": "processing",
            "message": "Image analysis started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start image analysis"
        )

async def run_pdf_analysis(file_id: str, storage_path: str):
    """Background task for PDF analysis"""
    try:
        # Get database session
        from core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Run PDF forensics
            analysis_result = await pdf_service.analyze_pdf(storage_path)
            
            # Update file record
            db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
            if db_file:
                db_file.verdict = analysis_result["verdict"]
                db_file.confidence_score = analysis_result["confidence_score"]
                db_file.analysis_status = "completed"
                db_file.analysis_date = datetime.utcnow()
                
                # Create report record
                report = ReportModel(
                    file_id=db_file.id,
                    analysis_type="pdf_forensics",
                    result=analysis_result["verdict"],
                    confidence_score=analysis_result["confidence_score"],
                    evidence_data=analysis_result["evidence"],
                    processing_time=analysis_result.get("processing_time"),
                    model_version="1.0.0"
                )
                
                db.add(report)
                db.commit()
                
                logger.info(f"PDF analysis completed for {file_id}: {analysis_result['verdict']}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"PDF analysis background task error: {e}")
        # Update status to failed
        try:
            db = SessionLocal()
            db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
            if db_file:
                db_file.analysis_status = "failed"
                db.commit()
        except:
            pass
        finally:
            db.close()

async def run_image_analysis(file_id: str, storage_path: str):
    """Background task for image analysis"""
    try:
        # Get database session
        from core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Run image forensics
            analysis_result = await image_service.analyze_image(storage_path)
            
            # Update file record
            db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
            if db_file:
                db_file.verdict = analysis_result["verdict"]
                db_file.confidence_score = analysis_result["confidence_score"]
                db_file.analysis_status = "completed"
                db_file.analysis_date = datetime.utcnow()
                
                # Create report records for both ELA and CNN
                ela_report = ReportModel(
                    file_id=db_file.id,
                    analysis_type="image_ela",
                    result=analysis_result["ela_result"],
                    confidence_score=analysis_result["ela_confidence"],
                    evidence_data=analysis_result["ela_evidence"],
                    evidence_link=analysis_result.get("ela_heatmap_path"),
                    processing_time=analysis_result.get("ela_processing_time"),
                    model_version="1.0.0"
                )
                
                cnn_report = ReportModel(
                    file_id=db_file.id,
                    analysis_type="image_cnn",
                    result=analysis_result["cnn_result"],
                    confidence_score=analysis_result["cnn_confidence"],
                    evidence_data=analysis_result["cnn_evidence"],
                    processing_time=analysis_result.get("cnn_processing_time"),
                    model_version="1.0.0"
                )
                
                db.add(ela_report)
                db.add(cnn_report)
                db.commit()
                
                logger.info(f"Image analysis completed for {file_id}: {analysis_result['verdict']}")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Image analysis background task error: {e}")
        # Update status to failed
        try:
            db = SessionLocal()
            db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
            if db_file:
                db_file.analysis_status = "failed"
                db.commit()
        except:
            pass
        finally:
            db.close()
