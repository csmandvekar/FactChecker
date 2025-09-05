from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from core.database import Base


class CompanyFinancial(Base):
    __tablename__ = "company_financials"

    id = Column(Integer, primary_key=True, index=True)
    company_symbol = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    last_quarter_revenue_cr = Column(Float, nullable=True)
    last_quarter_profit_cr = Column(Float, nullable=True)
    market_cap_cr = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<CompanyFinancial(symbol={self.company_symbol}, revenue={self.last_quarter_revenue_cr})>"
