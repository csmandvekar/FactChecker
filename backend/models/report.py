from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # pdf_forensics, image_ela, cnn_detection
    
    # Analysis results
    result = Column(String(20), nullable=False)  # authentic, suspicious, malicious
    confidence_score = Column(Float, nullable=True)
    
    # Evidence and details
    evidence_data = Column(JSON, nullable=True)  # Detailed forensic evidence
    evidence_link = Column(String(500), nullable=True)  # Link to evidence file (heatmap, etc.)
    
    # Analysis metadata
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())
    processing_time = Column(Float, nullable=True)  # Time taken for analysis in seconds
    
    # Technical details
    model_version = Column(String(50), nullable=True)  # Version of analysis model used
    analysis_parameters = Column(JSON, nullable=True)  # Parameters used for analysis
    
    # Relationships
    file = relationship("File", back_populates="reports")
    
    def __repr__(self):
        return f"<Report(id={self.id}, file_id={self.file_id}, type='{self.analysis_type}', result='{self.result}')>"
    
    @property
    def is_suspicious(self):
        return self.result in ["suspicious", "malicious"]
    
    @property
    def confidence_level(self):
        if self.confidence_score is None:
            return "unknown"
        elif self.confidence_score >= 0.8:
            return "high"
        elif self.confidence_score >= 0.6:
            return "medium"
        else:
            return "low"
