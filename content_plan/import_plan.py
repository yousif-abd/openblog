"""
Content Plan Import CLI

Import content plan from XLSX into the database, optionally triggering
Beck extraction or pipeline runs.

Usage:
    # Import content plan
    python -m content_plan.import_plan --xlsx data/content_plan.xlsx

    # Import and trigger Beck extraction
    python -m content_plan.import_plan --xlsx data/content_plan.xlsx --extract-beck

    # List imported plan
    python -m content_plan.import_plan --list
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(_PROJECT_ROOT / ".env")

from shared.database import OpenBlogDB
from content_plan.plan_parser import parse_content_plan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def list_plan(status: str = None):
    """List content plan entries."""
    db = OpenBlogDB()
    entries = db.get_content_plan(status=status)

    if not entries:
        print("\nNo content plan entries found.")
        return

    print(f"\nContent Plan: {len(entries)} entries")
    print("-" * 80)
    print(f"{'#':<4} {'Status':<12} {'Keyword':<40} {'Rechtsgebiet':<15} {'Date':<12}")
    print("-" * 80)

    for i, entry in enumerate(entries, 1):
        kw = entry.get("keyword", "") or entry.get("title", "")
        if len(kw) > 38:
            kw = kw[:35] + "..."
        print(
            f"{i:<4} {entry.get('status', ''):<12} {kw:<40} "
            f"{entry.get('rechtsgebiet', ''):<15} {entry.get('target_date', ''):<12}"
        )


async def import_and_extract(xlsx_path: str, rechtsgebiet: str = None, use_mock: bool = False):
    """Import plan and run Beck extraction for all entries."""
    from beck_extract.beck_extractor import extract_for_keywords

    db = OpenBlogDB()

    # Parse and import
    entries = parse_content_plan(xlsx_path)
    entry_dicts = [e.model_dump() for e in entries]
    db.import_content_plan(entry_dicts)

    # Extract Beck resources for all keywords
    keywords = [e.keyword or e.title for e in entries]
    result = await extract_for_keywords(
        keywords=keywords,
        rechtsgebiet=rechtsgebiet,
        use_mock=use_mock,
    )

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Content Plan Import - Import XLSX content plan into database"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--xlsx",
        help="Path to content plan XLSX file",
    )
    group.add_argument(
        "--list", action="store_true",
        help="List imported content plan entries",
    )

    parser.add_argument(
        "--sheet",
        help="Sheet name in XLSX (uses first sheet if not specified)",
    )
    parser.add_argument(
        "--extract-beck", action="store_true",
        help="After import, extract Beck-Online resources for all entries",
    )
    parser.add_argument(
        "--rechtsgebiet",
        help="Override rechtsgebiet for Beck extraction",
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Use mock data for Beck extraction",
    )
    parser.add_argument(
        "--status",
        choices=["planned", "in_progress", "completed"],
        help="Filter by status (for --list)",
    )

    args = parser.parse_args()

    if args.list:
        list_plan(status=args.status)
        return

    # Parse XLSX
    entries = parse_content_plan(args.xlsx, sheet_name=args.sheet)

    if not entries:
        print("No entries found in content plan.")
        sys.exit(1)

    # Import to DB
    db = OpenBlogDB()
    entry_dicts = [e.model_dump() for e in entries]
    count = db.import_content_plan(entry_dicts)

    print(f"\nImported {count} content plan entries")
    for e in entries:
        print(f"  - {e.keyword or e.title} ({e.rechtsgebiet or 'no area'})")

    # Optional Beck extraction
    if args.extract_beck:
        print("\nStarting Beck-Online extraction...")
        result = asyncio.run(
            import_and_extract(args.xlsx, rechtsgebiet=args.rechtsgebiet, use_mock=args.mock)
        )
        print(f"Extracted {result['total_resources']} resources for {result['total_keywords']} keywords")

    # Auto-link webinars if any exist
    linked = db.auto_link_webinars_to_keywords()
    if linked:
        print(f"Auto-linked {linked} webinar-keyword pairs")


if __name__ == "__main__":
    main()
