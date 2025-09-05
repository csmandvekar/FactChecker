#!/usr/bin/env python3
"""
End-to-end ingestion for NSE announcements using nsepython:
 - Fetch announcements for a symbol over a date range
 - Download attachment PDF
 - Upload to Supabase Storage (bucket: announcements)
 - Insert into DB (announcements table), dedupe by pdf_url
 - Run analysis to compute credibility and update record

Prereqs:
  pip install nsepython requests PyPDF2
  Set env: SUPABASE_URL, SUPABASE_KEY (if you want storage uploads)
  DATABASE_URL set or defaults to SQLite ./app.db via core.database

Usage:
  python backend/scripts/ingest_nse_announcements.py --symbol TCS --days 30 --save
"""

import os
import sys
import argparse
import logging
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import PyPDF2

# Ensure backend imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from core.database import init_db, get_db  # type: ignore
from models.announcement import Announcement  # type: ignore
from services.supabase import init_supabase, get_supabase  # type: ignore
from services.intelligence_analysis import IntelligenceAnalysisService  # type: ignore

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("ingest_nse")


def format_date_range(days: int) -> tuple[str, str]:
    to_dt = datetime.now().date()
    from_dt = to_dt - timedelta(days=max(0, days))
    return (from_dt.strftime("%d-%m-%Y"), to_dt.strftime("%d-%m-%Y"))


def nse_fetch(symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    from nsepython import nsefetch  # type: ignore
    base = "https://www.nseindia.com/api/corporate-announcements"
    url = f"{base}?index=equities&symbol={symbol}&from_date={from_date}&to_date={to_date}"
    data = nsefetch(url)
    if isinstance(data, dict) and "data" in data:
        return data["data"] or []
    if isinstance(data, list):
        return data
    return []


def extract_pdf_url(item: Dict[str, Any]) -> Optional[str]:
    pdf_url = (
        item.get("pdfUrl")
        or item.get("attchmntFile")
        or item.get("url")
        or (item.get("attachments", [{}])[0].get("pdfUrl") if item.get("attachments") else None)
        or ""
    )
    return pdf_url or None


def download_pdf(session: requests.Session, url: str) -> Optional[bytes]:
    try:
        resp = session.get(url, timeout=(10, 120), allow_redirects=True, stream=True)
        resp.raise_for_status()
        content = resp.content
        ctype = resp.headers.get("content-type", "")
        if "pdf" in ctype.lower() or url.lower().endswith(".pdf"):
            return content
        return content  # some NSE endpoints serve without explicit content-type
    except Exception as exc:
        logger.error("PDF download failed: %s", exc)
        return None


def pdf_text(content: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        texts: List[str] = []
        for page in reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(texts).strip()
    except Exception as exc:
        logger.warning("PDF text extraction error: %s", exc)
        return ""


def upload_to_supabase(content: bytes, symbol: str, dt: datetime) -> Optional[str]:
    try:
        init_supabase()
        client = get_supabase()
        filename = f"{symbol}_{dt.strftime('%Y%m%d_%H%M%S')}.pdf"
        result = client.storage.from_("announcements").upload(
            filename, content, {"content-type": "application/pdf"}
        )
        if isinstance(result, dict) and result.get("error"):
            logger.error("Supabase upload error: %s", result["error"])
            return None
        return filename
    except Exception as exc:
        logger.warning("Supabase upload skipped/failed: %s", exc)
        return None


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/pdf,application/json,text/plain,*/*",
        "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    })
    retries = Retry(
        total=5,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def insert_or_update(db, symbol: str, company_name: str, title: str, ann_dt: datetime, pdf_url: str, storage_path: Optional[str], full_text: str) -> Announcement:
    existing = db.query(Announcement).filter(Announcement.pdf_url == pdf_url).first()
    if existing:
        return existing
    row = Announcement(
        company_name=company_name,
        company_symbol=symbol,
        title=title,
        announcement_date=ann_dt,
        pdf_url=pdf_url,
        storage_path=storage_path,
        full_text=full_text,
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def run_analysis(db, announcement: Announcement) -> None:
    service = IntelligenceAnalysisService()
    # Re-fetch managed entity to ensure session linkage
    ann = db.query(Announcement).filter(Announcement.id == announcement.id).first()
    if not ann:
        return
    import asyncio
    asyncio.run(service.analyze_announcement(ann, db))


def parse_announcement_datetime(item: Dict[str, Any]) -> datetime:
    dt_val = item.get("announcedDate") or item.get("an_dt") or item.get("attachmentDate") or item.get("date") or ""
    if isinstance(dt_val, (int, float)):
        return datetime.fromtimestamp(float(dt_val) / 1000.0)
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(dt_val), fmt)
        except Exception:
            continue
    # Fallback
    return datetime.now()


def main():
    parser = argparse.ArgumentParser(description="Ingest NSE announcements end-to-end")
    parser.add_argument("--symbol", required=True, help="Symbol like TCS, INFY, WIPRO")
    parser.add_argument("--days", type=int, default=7, help="Days lookback (default 7)")
    parser.add_argument("--save", action="store_true", help="Persist to DB and analyze")
    args = parser.parse_args()

    from_date, to_date = format_date_range(args.days)
    print(f"Symbol: {args.symbol}; Range: {from_date} -> {to_date}")

    # Initialize DB and optionally Supabase (lazy inside upload)
    init_db()

    items = nse_fetch(args.symbol, from_date, to_date)
    print(f"Fetched {len(items)} records")

    if not args.save:
        # Just show the first few
        for i, item in enumerate(items[:5], start=1):
            print(f"  {i}. {item.get('subject') or item.get('desc') or 'Announcement'}")
        return

    # Save path
    session = build_session()
    db = next(get_db())
    try:
        ingested = 0
        for item in items:
            subject = item.get("subject") or item.get("desc") or item.get("sub") or "Announcement"
            company_name = item.get("companyName") or item.get("sm_name") or args.symbol
            ann_dt = parse_announcement_datetime(item)
            pdf_url = extract_pdf_url(item)
            if not pdf_url:
                # insert without attachment if none present
                row = insert_or_update(db, args.symbol, company_name, subject, ann_dt, "", None, "")
                # analysis will have no text; skip
                continue

            pdf_content = download_pdf(session, pdf_url)
            if not pdf_content:
                # Insert basic row so at least it appears in UI; skip upload/analysis
                _ = insert_or_update(db, args.symbol, company_name, subject, ann_dt, pdf_url, None, "")
                continue

            storage_path = upload_to_supabase(pdf_content, args.symbol, ann_dt)
            text = pdf_text(pdf_content)

            row = insert_or_update(db, args.symbol, company_name, subject, ann_dt, pdf_url, storage_path, text)
            run_analysis(db, row)
            ingested += 1

        print(f"Saved and analyzed {ingested} announcements")
    finally:
        db.close()


if __name__ == "__main__":
    main()


