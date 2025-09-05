# from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List
# import magic
# import logging
# from pathlib import Path

# from core.database import get_db
# from core.config import settings
# from services.storage import storage_service
# from models.file import File as FileModel
# from models.user import User

# logger = logging.getLogger(__name__)
# router = APIRouter()

# def validate_file_type(file_content: bytes, filename: str) -> str:
#     """Validate file type and return file type category"""
#     # Get MIME type using python-magic
#     mime_type = magic.from_buffer(file_content, mime=True)
    
#     # Check file extension
#     file_extension = Path(filename).suffix.lower()
    
#     # Validate against allowed extensions
#     if file_extension not in settings.ALLOWED_EXTENSIONS:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"File type {file_extension} not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
#         )
    
#     # Determine file type category
#     if file_extension == ".pdf":
#         if mime_type != "application/pdf":
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Invalid PDF file"
#             )
#         return "pdf"
#     elif file_extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]:
#         if not mime_type.startswith("image/"):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Invalid image file"
#             )
#         return "image"
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Unsupported file type: {file_extension}"
#         )

# @router.post("/upload")
# async def upload_file(
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     """
#     Upload a file for forensic analysis
    
#     - **file**: File to upload (PDF or image)
#     - Returns file_id for analysis
#     """
#     try:
#         # Read file content
#         file_content = await file.read()
        
#         # Validate file size
#         if len(file_content) > settings.MAX_FILE_SIZE:
#             raise HTTPException(
#                 status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
#                 detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
#             )
        
#         # Validate file type
#         file_type = validate_file_type(file_content, file.filename)
        
#         # Save file to storage
#         from io import BytesIO
#         file_stream = BytesIO(file_content)
#         storage_metadata = storage_service.save_file(file_stream, file.filename, file_type)
        
#         # Create database record
#         db_file = FileModel(
#             file_id=storage_metadata["file_id"],
#             filename=storage_metadata["filename"],
#             original_filename=storage_metadata["original_filename"],
#             file_type=storage_metadata["file_type"],
#             mime_type=magic.from_buffer(file_content, mime=True),
#             file_size=len(file_content),
#             file_hash=storage_metadata["file_hash"],
#             storage_path=storage_metadata["storage_path"],
#             storage_type=storage_metadata["storage_type"],
#             analysis_status="pending"
#         )
        
#         db.add(db_file)
#         db.commit()
#         db.refresh(db_file)
        
#         logger.info(f"File uploaded successfully: {db_file.file_id}")
        
#         return {
#             "file_id": db_file.file_id,
#             "filename": db_file.original_filename,
#             "file_type": db_file.file_type,
#             "file_size": db_file.file_size,
#             "status": "uploaded",
#             "message": "File uploaded successfully. Ready for analysis."
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"File upload error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to upload file"
#         )

# @router.get("/upload/status/{file_id}")
# async def get_upload_status(
#     file_id: str,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get upload and analysis status for a file
    
#     - **file_id**: Unique file identifier
#     """
#     try:
#         db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
        
#         if not db_file:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="File not found"
#             )
        
#         return {
#             "file_id": db_file.file_id,
#             "filename": db_file.original_filename,
#             "file_type": db_file.file_type,
#             "analysis_status": db_file.analysis_status,
#             "verdict": db_file.verdict,
#             "confidence_score": db_file.confidence_score,
#             "upload_date": db_file.upload_date,
#             "analysis_date": db_file.analysis_date
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Status check error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to get file status"
#         )

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
from pathlib import Path
import mimetypes

from core.database import get_db
from core.config import settings
from models.file import File as FileModel
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

def _detect_mime_type(file_content: bytes) -> str:
    """Detect MIME type using filetype library if available; otherwise return empty string."""
    try:
        import filetype  # Pure Python file type detection
        kind = filetype.guess(file_content)
        return kind.mime if kind else ""
    except Exception:
        return ""

def validate_file_type(file_content: bytes, filename: str) -> str:
    """Validate file type and return file type category"""
    # Try filetype library; fall back to mimetypes by filename
    mime_type = _detect_mime_type(file_content) or (mimetypes.guess_type(filename)[0] or "")
    
    # Check file extension
    file_extension = Path(filename).suffix.lower()
    
    # Validate against allowed extensions
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Determine file type category
    if file_extension == ".pdf":
        if mime_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )
        return "pdf"
    elif file_extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]:
        if not mime_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
        return "image"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}"
        )

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a file for forensic analysis
    
    - **file**: File to upload (PDF or image)
    - Returns file_id for analysis
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Validate file type
        file_type = validate_file_type(file_content, file.filename)
        
        # Get the storage service instance only when it's needed (lazy import)
        from services.storage import get_storage_service
        storage_service = get_storage_service()
        
        # Save file to storage
        from io import BytesIO
        file_stream = BytesIO(file_content)
        storage_metadata = storage_service.save_file(file_stream, file.filename, file_type)
        
        # Create database record
        db_file = FileModel(
            file_id=storage_metadata["file_id"],
            filename=storage_metadata["filename"],
            original_filename=storage_metadata["original_filename"],
            file_type=storage_metadata["file_type"],
            # Use the same detection function for consistent MIME type detection
            mime_type=_detect_mime_type(file_content) or (mimetypes.guess_type(file.filename)[0] or ""),
            file_size=len(file_content),
            file_hash=storage_metadata["file_hash"],
            storage_path=storage_metadata["storage_path"],
            storage_type=storage_metadata["storage_type"],
            analysis_status="pending"
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        logger.info(f"File uploaded successfully: {db_file.file_id}")
        
        return {
            "file_id": db_file.file_id,
            "filename": db_file.original_filename,
            "file_type": db_file.file_type,
            "file_size": db_file.file_size,
            "status": "uploaded",
            "message": "File uploaded successfully. Ready for analysis."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

@router.get("/upload/status/{file_id}")
async def get_upload_status(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    Get upload and analysis status for a file
    
    - **file_id**: Unique file identifier
    """
    try:
        db_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
        
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return {
            "file_id": db_file.file_id,
            "filename": db_file.original_filename,
            "file_type": db_file.file_type,
            "analysis_status": db_file.analysis_status,
            "verdict": db_file.verdict,
            "confidence_score": db_file.confidence_score,
            "upload_date": db_file.upload_date,
            "analysis_date": db_file.analysis_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file status"
        )

