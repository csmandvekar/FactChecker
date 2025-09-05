#!/usr/bin/env python3
"""
Script to add sample announcements for testing the Market Intelligence module
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db, init_db
from models.announcement import Announcement
from models.company_financial import CompanyFinancial

def add_sample_announcements():
    """Add sample announcements to the database"""
    
    # Initialize database
    init_db()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Sample announcements data
        sample_announcements = [
            {
                "company_name": "Reliance Industries Limited",
                "company_symbol": "RELIANCE",
                "title": "Quarterly Results for Q3 FY2024 - Revenue Growth of 15%",
                "announcement_date": datetime.now() - timedelta(days=1),
                "pdf_url": "https://example.com/reliance_q3_results.pdf",
                "storage_path": "reliance_q3_2024.pdf",
                "full_text": "Reliance Industries Limited announced its quarterly results for Q3 FY2024. The company reported a revenue of ₹2,500 crores, representing a growth of 15% compared to the previous quarter. Net profit stood at ₹450 crores, showing a healthy margin of 18%. The company's performance was driven by strong demand in the petrochemicals segment and continued growth in the digital services business.",
                "status": "analyzed",
                "credibility_score": 8.5,
                "analysis_summary": {
                    "red_flags": [],
                    "sentiment": {"label": "POSITIVE", "score": 0.85},
                    "anomaly_detected": False,
                    "recommendations": ["Low risk: Content appears credible"]
                }
            },
            {
                "company_name": "Tata Consultancy Services Limited",
                "company_symbol": "TCS",
                "title": "Board Meeting Outcome - Dividend Declaration",
                "announcement_date": datetime.now() - timedelta(days=2),
                "pdf_url": "https://example.com/tcs_board_meeting.pdf",
                "storage_path": "tcs_board_meeting_2024.pdf",
                "full_text": "The Board of Directors of Tata Consultancy Services Limited met today and declared an interim dividend of ₹18 per equity share. The company also announced its quarterly results with revenue of ₹1,200 crores and net profit of ₹280 crores. The management expressed confidence in the company's growth prospects for the coming quarters.",
                "status": "analyzed",
                "credibility_score": 9.2,
                "analysis_summary": {
                    "red_flags": [],
                    "sentiment": {"label": "POSITIVE", "score": 0.78},
                    "anomaly_detected": False,
                    "recommendations": ["Low risk: Content appears credible"]
                }
            },
            {
                "company_name": "Infosys Limited",
                "company_symbol": "INFY",
                "title": "Annual General Meeting Notice - FY2024",
                "announcement_date": datetime.now() - timedelta(days=3),
                "pdf_url": "https://example.com/infy_agm_notice.pdf",
                "storage_path": "infy_agm_notice_2024.pdf",
                "full_text": "Infosys Limited hereby gives notice that the 42nd Annual General Meeting of the Company will be held on March 15, 2024. The company reported strong performance with revenue of ₹800 crores and profit of ₹180 crores. The management highlighted the company's focus on digital transformation and cloud services.",
                "status": "analyzed",
                "credibility_score": 8.8,
                "analysis_summary": {
                    "red_flags": [],
                    "sentiment": {"label": "POSITIVE", "score": 0.82},
                    "anomaly_detected": False,
                    "recommendations": ["Low risk: Content appears credible"]
                }
            },
            {
                "company_name": "HDFC Bank Limited",
                "company_symbol": "HDFCBANK",
                "title": "Quarterly Results - Strong Growth in Digital Banking",
                "announcement_date": datetime.now() - timedelta(days=4),
                "pdf_url": "https://example.com/hdfc_q3_results.pdf",
                "storage_path": "hdfc_q3_2024.pdf",
                "full_text": "HDFC Bank reported impressive quarterly results with revenue of ₹1,500 crores and net profit of ₹320 crores. The bank's digital banking segment showed remarkable growth, contributing significantly to the overall performance. The management announced plans for further digital expansion.",
                "status": "analyzed",
                "credibility_score": 7.9,
                "analysis_summary": {
                    "red_flags": ["promotional_hype"],
                    "sentiment": {"label": "POSITIVE", "score": 0.88},
                    "anomaly_detected": False,
                    "recommendations": ["Medium risk: Review flagged issues"]
                }
            },
            {
                "company_name": "ICICI Bank Limited",
                "company_symbol": "ICICIBANK",
                "title": "Board Meeting - Strategic Initiatives Announcement",
                "announcement_date": datetime.now() - timedelta(days=5),
                "pdf_url": "https://example.com/icici_strategic_initiatives.pdf",
                "storage_path": "icici_strategic_2024.pdf",
                "full_text": "ICICI Bank's Board of Directors met to discuss strategic initiatives for the upcoming financial year. The bank reported revenue of ₹1,200 crores and profit of ₹250 crores. Several new initiatives were announced to enhance customer experience and expand the bank's digital footprint.",
                "status": "pending",
                "credibility_score": None,
                "analysis_summary": None
            },
            {
                "company_name": "Bharti Airtel Limited",
                "company_symbol": "BHARTIARTL",
                "title": "5G Network Expansion - Revolutionary Coverage",
                "announcement_date": datetime.now() - timedelta(days=6),
                "pdf_url": "https://example.com/airtel_5g_expansion.pdf",
                "storage_path": "airtel_5g_2024.pdf",
                "full_text": "Bharti Airtel announced a revolutionary expansion of its 5G network coverage, promising unprecedented speeds and guaranteed connectivity. The company claims this will be the most advanced network in the country, with coverage reaching every corner of India. Revenue projections show exponential growth potential.",
                "status": "analyzed",
                "credibility_score": 4.2,
                "analysis_summary": {
                    "red_flags": ["promotional_hype", "unrealistic_projections"],
                    "sentiment": {"label": "POSITIVE", "score": 0.95},
                    "anomaly_detected": True,
                    "recommendations": ["High risk: Consider additional verification", "Review flagged content for promotional language"]
                }
            }
        ]
        
        # Add announcements to database
        for announcement_data in sample_announcements:
            # Check if announcement already exists
            existing = db.query(Announcement).filter(
                Announcement.pdf_url == announcement_data['pdf_url']
            ).first()
            
            if not existing:
                announcement = Announcement(**announcement_data)
                db.add(announcement)
                print(f"✅ Added announcement: {announcement_data['title']}")
            else:
                print(f"⚠️  Announcement already exists: {announcement_data['title']}")
        
        # Add sample company financial data
        sample_financials = [
            {
                "company_symbol": "RELIANCE",
                "company_name": "Reliance Industries Limited",
                "last_quarter_revenue_cr": 2500.0,
                "last_quarter_profit_cr": 450.0,
                "market_cap_cr": 150000.0,
                "pe_ratio": 25.5
            },
            {
                "company_symbol": "TCS",
                "company_name": "Tata Consultancy Services Limited",
                "last_quarter_revenue_cr": 1200.0,
                "last_quarter_profit_cr": 280.0,
                "market_cap_cr": 120000.0,
                "pe_ratio": 30.2
            },
            {
                "company_symbol": "INFY",
                "company_name": "Infosys Limited",
                "last_quarter_revenue_cr": 800.0,
                "last_quarter_profit_cr": 180.0,
                "market_cap_cr": 80000.0,
                "pe_ratio": 28.7
            },
            {
                "company_symbol": "HDFCBANK",
                "company_name": "HDFC Bank Limited",
                "last_quarter_revenue_cr": 1500.0,
                "last_quarter_profit_cr": 320.0,
                "market_cap_cr": 90000.0,
                "pe_ratio": 22.1
            },
            {
                "company_symbol": "ICICIBANK",
                "company_name": "ICICI Bank Limited",
                "last_quarter_revenue_cr": 1200.0,
                "last_quarter_profit_cr": 250.0,
                "market_cap_cr": 75000.0,
                "pe_ratio": 24.3
            },
            {
                "company_symbol": "BHARTIARTL",
                "company_name": "Bharti Airtel Limited",
                "last_quarter_revenue_cr": 600.0,
                "last_quarter_profit_cr": 120.0,
                "market_cap_cr": 45000.0,
                "pe_ratio": 18.5
            }
        ]
        
        # Add company financial data
        for financial_data in sample_financials:
            # Check if company data already exists
            existing = db.query(CompanyFinancial).filter(
                CompanyFinancial.company_symbol == financial_data['company_symbol']
            ).first()
            
            if not existing:
                company_financial = CompanyFinancial(**financial_data)
                db.add(company_financial)
                print(f"✅ Added financial data: {financial_data['company_name']}")
            else:
                print(f"⚠️  Financial data already exists: {financial_data['company_name']}")
        
        # Commit all changes
        db.commit()
        print("\n🎉 Sample data added successfully!")
        print(f"📊 Added {len(sample_announcements)} announcements")
        print(f"🏢 Added {len(sample_financials)} company financial records")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Adding sample announcements and company data...")
    add_sample_announcements()
    print("\n✅ Setup complete! You can now view the announcements in your frontend.")

