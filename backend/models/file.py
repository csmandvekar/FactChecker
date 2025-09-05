from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base
import uuid

class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, image, video, audio
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA256 hash
    storage_path = Column(String(500), nullable=False)
    storage_type = Column(String(20), default="local")  # local, s3, minio
    
    # Analysis results
    verdict = Column(String(20), nullable=True)  # authentic, suspicious, malicious
    confidence_score = Column(Float, nullable=True)
    analysis_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Metadata
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    analysis_date = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    reports = relationship("Report", back_populates="file", cascade="all, delete-orphan")
    user = relationship("User", back_populates="files")
    
    def __repr__(self):
        return f"<File(id={self.id}, filename='{self.filename}', verdict='{self.verdict}')>"
    
    @property
    def is_analyzed(self):
        return self.analysis_status == "completed"
    
    @property
    def is_suspicious(self):
        return self.verdict in ["suspicious", "malicious"]
