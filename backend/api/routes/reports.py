from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from services.supabase import get_supabase

from core.database import get_db
from models.file import File as FileModel
from models.report import Report as ReportModel

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/report/{file_id}")
async def get_report(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive forensic report for a file
    
    - **file_id**: Unique file identifier
    - Returns detailed analysis results and evidence
    """
    try:
        # Get file and its reports
        db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
        
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Get all reports for this file
        reports = db.query(ReportModel).filter(ReportModel.file_id == db_file.id).all()
        
        # Organize reports by type
        report_data = {}
        for report in reports:
            if report.analysis_type not in report_data:
                report_data[report.analysis_type] = []
            report_data[report.analysis_type].append({
                "id": report.id,
                "result": report.result,
                "confidence_score": report.confidence_score,
                "evidence_data": report.evidence_data,
                "evidence_link": report.evidence_link,
                "analysis_date": report.analysis_date,
                "processing_time": report.processing_time,
                "model_version": report.model_version
            })
        
        # Build comprehensive report
        comprehensive_report = {
            "file_info": {
                "file_id": db_file.file_id,
                "filename": db_file.original_filename,
                "file_type": db_file.file_type,
                "file_size": db_file.file_size,
                "file_hash": db_file.file_hash,
                "upload_date": db_file.upload_date,
                "analysis_status": db_file.analysis_status
            },
            "overall_verdict": {
                "verdict": db_file.verdict,
                "confidence_score": db_file.confidence_score,
                "analysis_date": db_file.analysis_date
            },
            "detailed_reports": report_data,
            "summary": generate_summary(db_file, reports)
        }
        
        return comprehensive_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report"
        )

@router.get("/reports")
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    file_type: Optional[str] = None,
    verdict: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all reports with optional filtering
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **file_type**: Filter by file type (pdf, image)
    - **verdict**: Filter by verdict (authentic, suspicious, malicious)
    """
    try:
        query = db.query(FileModel)
        
        # Apply filters
        if file_type:
            query = query.filter(FileModel.file_type == file_type)
        if verdict:
            query = query.filter(FileModel.verdict == verdict)
        
        # Get paginated results
        files = query.offset(skip).limit(limit).all()
        
        reports_list = []
        for file in files:
            # Get latest report for each file
            latest_report = db.query(ReportModel).filter(
                ReportModel.file_id == file.id
            ).order_by(ReportModel.analysis_date.desc()).first()
            
            reports_list.append({
                "file_id": file.file_id,
                "filename": file.original_filename,
                "file_type": file.file_type,
                "verdict": file.verdict,
                "confidence_score": file.confidence_score,
                "upload_date": file.upload_date,
                "analysis_date": file.analysis_date,
                "latest_analysis_type": latest_report.analysis_type if latest_report else None
            })
        
        try:
            supabase = get_supabase()
            total_result = supabase.table("analysis_results").select("count", count="exact").execute()
            total_analyses = total_result.count or 0
        except Exception:
            total_analyses = len(reports_list)

        return {
            "reports": reports_list,
            "total": len(reports_list),
            "total_analyses": total_analyses,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Reports listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list reports"
        )

@router.get("/report/{file_id}/download")
async def download_report(
    file_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """
    Download forensic report in specified format
    
    - **file_id**: Unique file identifier
    - **format**: Report format (json, pdf, html)
    """
    try:
        # Get comprehensive report
        report_data = await get_report(file_id, db)
        
        if format.lower() == "json":
            return report_data
        elif format.lower() == "pdf":
            # TODO: Implement PDF generation
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PDF format not yet implemented"
            )
        elif format.lower() == "html":
            # TODO: Implement HTML generation
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="HTML format not yet implemented"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported format. Use: json, pdf, html"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report download error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download report"
        )

def generate_summary(file: FileModel, reports: List[ReportModel]) -> dict:
    """Generate a summary of the forensic analysis"""
    summary = {
        "total_analyses": len(reports),
        "analysis_types": list(set([r.analysis_type for r in reports])),
        "overall_risk_level": "low",
        "key_findings": [],
        "recommendations": []
    }
    
    # Determine overall risk level
    suspicious_count = sum(1 for r in reports if r.is_suspicious)
    if suspicious_count > 0:
        summary["overall_risk_level"] = "high" if suspicious_count >= len(reports) * 0.5 else "medium"
    
    # Generate key findings
    for report in reports:
        if report.is_suspicious:
            summary["key_findings"].append({
                "type": report.analysis_type,
                "finding": f"Suspicious activity detected with {report.confidence_score:.2f} confidence",
                "evidence": report.evidence_data
            })
    
    # Generate recommendations
    if summary["overall_risk_level"] == "high":
        summary["recommendations"].append("File shows strong signs of manipulation. Do not trust this content.")
        summary["recommendations"].append("Consider reporting to relevant authorities if this is official documentation.")
    elif summary["overall_risk_level"] == "medium":
        summary["recommendations"].append("File shows some suspicious characteristics. Verify from original source.")
        summary["recommendations"].append("Cross-reference with other sources before using this content.")
    else:
        summary["recommendations"].append("File appears authentic based on forensic analysis.")
        summary["recommendations"].append("Standard verification practices still recommended.")
    
    return summary
