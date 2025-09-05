from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON
from sqlalchemy.sql import func
from core.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    company_symbol = Column(String(50), nullable=False, index=True)
    title = Column(Text, nullable=False)
    announcement_date = Column(DateTime, nullable=False, index=True)
    pdf_url = Column(Text, unique=True, nullable=False)
    storage_path = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    status = Column(String(50), default='pending', index=True)  # pending, analyzed, failed
    credibility_score = Column(Float, nullable=True, index=True)
    analysis_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Announcement(id={self.id}, company={self.company_name}, title='{self.title[:50]}...')>"
