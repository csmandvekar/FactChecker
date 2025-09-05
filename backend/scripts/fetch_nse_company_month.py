#!/usr/bin/env python3
"""
Fetch all NSE corporate announcements for a single company over a date range
(default past 30 days) and optionally save them to the database.

Usage examples (from repo root):
  # Fetch and save past 30 days for TCS
  python backend/scripts/fetch_nse_company_month.py --symbol TCS --days 30 --save

  # Fetch only (print summary), no DB write
  python backend/scripts/fetch_nse_company_month.py --symbol INFY --days 30
"""

import os
import sys
import argparse
import logging

# Ensure backend imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from scripts.real_nse_scraper import RealNSEScraper  # type: ignore

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("fetch_nse_company_month")


def main():
    parser = argparse.ArgumentParser(description="Fetch NSE announcements for a single company over a date range")
    parser.add_argument("--symbol", required=True, help="Company symbol (e.g., TCS, INFY, WIPRO)")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back (default: 30)")
    parser.add_argument("--save", action="store_true", help="Save results to database")
    args = parser.parse_args()

    scraper = RealNSEScraper()
    # Initialize/warm session to avoid anti-bot issues
    ok = scraper.initialize_session()
    if not ok:
        logger.warning("Session warm-up may have failed; proceeding anyway...")

    # Build date range and fetch (no keyword filter)
    from_date, to_date = scraper.get_date_range(args.days)
    anns = scraper.fetch_company_announcements(args.symbol, from_date, to_date)

    print(f"Symbol: {args.symbol}")
    print(f"Date range: {from_date} -> {to_date}")
    print(f"Fetched: {len(anns)} announcements")

    if anns:
        print("\nSample (first up to 5):")
        for i, ann in enumerate(anns[:5], start=1):
            dt = ann.announcement_date.strftime("%Y-%m-%d")
            print(f"  {i}. {dt} - {ann.company_name} - {ann.subject}")

    if args.save:
        inserted = scraper.save_to_database(anns)
        print(f"\nSaved to DB: {inserted} new rows")


if __name__ == "__main__":
    main()


