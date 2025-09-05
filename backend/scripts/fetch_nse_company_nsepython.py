#!/usr/bin/env python3
"""
Fetch NSE corporate announcements using nsepython's nsefetch helper, which
handles NSE cookies/headers. Can print and optionally save to DB.

Setup:
  pip install nsepython

Usage:
  # Print only
  python backend/scripts/fetch_nse_company_nsepython.py --symbol TCS --days 30

  # Save to DB
  python backend/scripts/fetch_nse_company_nsepython.py --symbol INFY --days 30 --save
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Ensure backend imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from core.database import init_db, get_db  # type: ignore
from models.announcement import Announcement  # type: ignore

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("nse_nsepython")


def format_date_range(days: int) -> tuple[str, str]:
    to_dt = datetime.now().date() - timedelta(days=1)
    from_dt = to_dt - timedelta(days=max(0, days - 1))
    return (from_dt.strftime("%d-%m-%Y"), to_dt.strftime("%d-%m-%Y"))


def fetch_announcements(symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    try:
        from nsepython import nsefetch  # type: ignore
    except Exception as exc:
        raise RuntimeError("nsepython is not installed. Run: pip install nsepython") from exc

    base = "https://www.nseindia.com/api/corporate-announcements"
    url = f"{base}?index=equities&symbol={symbol}&from_date={from_date}&to_date={to_date}"

    # nsefetch returns parsed JSON with proper cookies/headers management
    data = nsefetch(url)
    if isinstance(data, dict) and "data" in data:
        return data["data"] or []
    if isinstance(data, list):
        return data
    return []


def save_to_db(symbol: str, items: List[Dict[str, Any]]) -> int:
    init_db()
    db = next(get_db())
    inserted = 0
    try:
        for item in items:
            subject = item.get("subject") or item.get("sub") or "Announcement"
            dt_val = item.get("announcedDate") or item.get("attachmentDate") or item.get("date") or ""
            if isinstance(dt_val, (int, float)):
                ann_dt = datetime.fromtimestamp(float(dt_val) / 1000.0)
            else:
                ann_dt = None
                for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
                    try:
                        ann_dt = datetime.strptime(str(dt_val), fmt)
                        break
                    except Exception:
                        continue
                if ann_dt is None:
                    ann_dt = datetime.now()

            pdf_url = (
                item.get("pdfUrl")
                or item.get("url")
                or (item.get("attachments", [{}])[0].get("pdfUrl") if item.get("attachments") else None)
                or ""
            )
            if not pdf_url:
                continue

            exists = db.query(Announcement).filter(Announcement.pdf_url == pdf_url).first()
            if exists:
                continue

            company_name = item.get("companyName") or item.get("symbolName") or symbol
            row = Announcement(
                company_name=company_name,
                company_symbol=symbol,
                title=subject,
                announcement_date=ann_dt,
                pdf_url=pdf_url,
                storage_path=None,
                full_text=None,
                status="pending",
            )
            db.add(row)
            inserted += 1
        db.commit()
        return inserted
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Fetch NSE announcements via nsepython")
    parser.add_argument("--symbol", required=True, help="Company symbol (e.g., TCS, INFY, WIPRO)")
    parser.add_argument("--days", type=int, default=30, help="Days lookback (default 30)")
    parser.add_argument("--save", action="store_true", help="Save to database")
    args = parser.parse_args()

    from_date, to_date = format_date_range(args.days)
    print(f"Symbol: {args.symbol}; Range: {from_date} -> {to_date}")

    items = fetch_announcements(args.symbol, from_date, to_date)
    print(f"Fetched {len(items)} records")
    for i, item in enumerate(items[:5], start=1):
        subj = item.get("subject") or item.get("sub") or "Announcement"
        print(f"  {i}. {subj}")
        print(f"{item}")

    if args.save:
        inserted = save_to_db(args.symbol, items)
        print(f"Saved {inserted} new rows to DB")


if __name__ == "__main__":
    main()


