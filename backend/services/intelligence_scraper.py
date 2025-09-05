import logging
import requests
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
import PyPDF2
import io

from models.announcement import Announcement
from services.supabase import get_supabase

logger = logging.getLogger(__name__)


class IntelligenceScraperService:
    def __init__(self):
        self.bse_url = "https://www.bseindia.com/corporates/List_Scrips.aspx"
        self.nse_url = "https://www.nseindia.com/corporates/corporate-announcements"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def run_full_scrape(self, db: Session):
        """Run the complete scraping process"""
        try:
            logger.info("Starting full scraping process")
            
            # 1. Scrape BSE announcements
            bse_announcements = await self._scrape_bse_announcements()
            logger.info(f"Found {len(bse_announcements)} BSE announcements")
            
            # 2. Scrape NSE announcements
            nse_announcements = await self._scrape_nse_announcements()
            logger.info(f"Found {len(nse_announcements)} NSE announcements")
            
            # 3. Process and save announcements
            all_announcements = bse_announcements + nse_announcements
            saved_count = 0
            
            for announcement_data in all_announcements:
                try:
                    # Check if announcement already exists
                    existing = db.query(Announcement).filter(
                        Announcement.pdf_url == announcement_data['pdf_url']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Download and process PDF
                    pdf_content = await self._download_pdf(announcement_data['pdf_url'])
                    if pdf_content:
                        # Upload to Supabase Storage
                        storage_path = await self._upload_to_storage(
                            pdf_content, 
                            announcement_data['company_symbol'],
                            announcement_data['announcement_date']
                        )
                        
                        # Extract text from PDF
                        full_text = self._extract_pdf_text(pdf_content)
                        
                        # Create announcement record
                        announcement = Announcement(
                            company_name=announcement_data['company_name'],
                            company_symbol=announcement_data['company_symbol'],
                            title=announcement_data['title'],
                            announcement_date=announcement_data['announcement_date'],
                            pdf_url=announcement_data['pdf_url'],
                            storage_path=storage_path,
                            full_text=full_text,
                            status='pending'
                        )
                        
                        db.add(announcement)
                        saved_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing announcement: {e}")
                    continue
            
            db.commit()
            logger.info(f"Scraping completed. Saved {saved_count} new announcements")
            
        except Exception as e:
            logger.error(f"Error in full scraping process: {e}")
            raise
    
    async def _scrape_bse_announcements(self) -> List[Dict[str, Any]]:
        """Scrape BSE corporate announcements"""
        announcements = []
        
        try:
            # This is a simplified example - BSE's actual structure may be different
            # You'll need to inspect the actual BSE website structure
            
            # For now, return mock data to demonstrate the structure
            mock_announcements = [
                {
                    "company_name": "Reliance Industries Limited",
                    "company_symbol": "RELIANCE",
                    "title": "Quarterly Results for Q3 FY2024",
                    "announcement_date": datetime.now() - timedelta(days=1),
                    "pdf_url": "https://example.com/reliance_q3_results.pdf"
                },
                {
                    "company_name": "Tata Consultancy Services Limited",
                    "company_symbol": "TCS",
                    "title": "Board Meeting Outcome",
                    "announcement_date": datetime.now() - timedelta(days=2),
                    "pdf_url": "https://example.com/tcs_board_meeting.pdf"
                }
            ]
            
            return mock_announcements
            
        except Exception as e:
            logger.error(f"Error scraping BSE announcements: {e}")
            return []
    
    async def _scrape_nse_announcements(self) -> List[Dict[str, Any]]:
        """Scrape NSE corporate announcements"""
        announcements = []
        
        try:
            # This is a simplified example - NSE's actual structure may be different
            # You'll need to inspect the actual NSE website structure
            
            # For now, return mock data to demonstrate the structure
            mock_announcements = [
                {
                    "company_name": "Infosys Limited",
                    "company_symbol": "INFY",
                    "title": "Annual General Meeting Notice",
                    "announcement_date": datetime.now() - timedelta(days=3),
                    "pdf_url": "https://example.com/infy_agm_notice.pdf"
                }
            ]
            
            return mock_announcements
            
        except Exception as e:
            logger.error(f"Error scraping NSE announcements: {e}")
            return []
    
    async def _download_pdf(self, pdf_url: str) -> Optional[bytes]:
        """Download PDF content from URL"""
        try:
            response = self.session.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('application/pdf'):
                return response.content
            else:
                logger.warning(f"URL {pdf_url} does not return PDF content")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {e}")
            return None
    
    async def _upload_to_storage(self, pdf_content: bytes, company_symbol: str, announcement_date: datetime) -> str:
        """Upload PDF to Supabase Storage"""
        try:
            # Generate unique filename
            timestamp = announcement_date.strftime("%Y%m%d_%H%M%S")
            filename = f"{company_symbol}_{timestamp}.pdf"
            
            # Upload to Supabase Storage
            supabase = get_supabase()
            result = supabase.storage.from_("announcements").upload(
                filename,
                pdf_content,
                {"content-type": "application/pdf"}
            )
            
            if result.get('error'):
                logger.error(f"Error uploading to storage: {result['error']}")
                return None
            
            return filename
            
        except Exception as e:
            logger.error(f"Error uploading to storage: {e}")
            return None
    
    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text content from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    async def scrape_historical_data(self, db: Session):
        """Scrape historical financial data for companies"""
        try:
            logger.info("Starting historical data scraping")
            
            # List of NIFTY 50 companies (simplified)
            nifty_50_companies = [
                {"symbol": "RELIANCE", "name": "Reliance Industries Limited"},
                {"symbol": "TCS", "name": "Tata Consultancy Services Limited"},
                {"symbol": "INFY", "name": "Infosys Limited"},
                {"symbol": "HDFCBANK", "name": "HDFC Bank Limited"},
                {"symbol": "ICICIBANK", "name": "ICICI Bank Limited"},
                # Add more companies as needed
            ]
            
            for company in nifty_50_companies:
                try:
                    # Check if company data already exists
                    existing = db.query(CompanyFinancial).filter(
                        CompanyFinancial.company_symbol == company["symbol"]
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Scrape financial data (mock data for now)
                    financial_data = await self._scrape_company_financials(company["symbol"])
                    
                    if financial_data:
                        company_financial = CompanyFinancial(
                            company_symbol=company["symbol"],
                            company_name=company["name"],
                            last_quarter_revenue_cr=financial_data.get("revenue"),
                            last_quarter_profit_cr=financial_data.get("profit"),
                            market_cap_cr=financial_data.get("market_cap"),
                            pe_ratio=financial_data.get("pe_ratio")
                        )
                        
                        db.add(company_financial)
                        
                except Exception as e:
                    logger.error(f"Error scraping data for {company['symbol']}: {e}")
                    continue
            
            db.commit()
            logger.info("Historical data scraping completed")
            
        except Exception as e:
            logger.error(f"Error in historical data scraping: {e}")
            raise
    
    async def _scrape_company_financials(self, symbol: str) -> Optional[Dict[str, float]]:
        """Scrape financial data for a specific company"""
        try:
            # This is a placeholder - you would implement actual scraping logic here
            # For example, scraping from Screener.in or other financial data sources
            
            # Mock data for demonstration
            mock_data = {
                "RELIANCE": {"revenue": 2500.0, "profit": 450.0, "market_cap": 150000.0, "pe_ratio": 25.5},
                "TCS": {"revenue": 1200.0, "profit": 280.0, "market_cap": 120000.0, "pe_ratio": 30.2},
                "INFY": {"revenue": 800.0, "profit": 180.0, "market_cap": 80000.0, "pe_ratio": 28.7},
                "HDFCBANK": {"revenue": 1500.0, "profit": 320.0, "market_cap": 90000.0, "pe_ratio": 22.1},
                "ICICIBANK": {"revenue": 1200.0, "profit": 250.0, "market_cap": 75000.0, "pe_ratio": 24.3}
            }
            
            return mock_data.get(symbol)
            
        except Exception as e:
            logger.error(f"Error scraping financials for {symbol}: {e}")
            return None
