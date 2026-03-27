"""
Beck-Online Resource Extraction CLI

Standalone command to pre-extract legal resources from Beck-Online
and store them in the SQLite database for later article generation.

Usage:
    # Extract for specific titles
    python -m beck_extract.beck_extract --titles "Kündigungsschutz" "Mieterhöhung 2026"

    # Extract for all planned articles
    python -m beck_extract.beck_extract --from-plan

    # Use mock data (no Beck credentials needed)
    python -m beck_extract.beck_extract --titles "Kündigung" --mock

    # List stored resources
    python -m beck_extract.beck_extract --list
    python -m beck_extract.beck_extract --list --keyword "Kündigungsschutz"
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(_PROJECT_ROOT / ".env")

from shared.database import OpenBlogDB
from beck_extract.beck_extractor import (
    extract_for_keywords,
    extract_from_content_plan,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def list_resources(keyword: str = None, rechtsgebiet: str = None):
    """List stored Beck resources."""
    db = OpenBlogDB()

    if keyword:
        resources = db.get_beck_resources(keyword)
        print(f"\nBeck resources for '{keyword}': {len(resources)} found")
    elif rechtsgebiet:
        resources = db.get_beck_resources_by_rechtsgebiet(rechtsgebiet)
        print(f"\nBeck resources for rechtsgebiet '{rechtsgebiet}': {len(resources)} found")
    else:
        # List all unique keywords
        conn = db._get_conn()
        try:
            rows = conn.execute(
                "SELECT keyword, rechtsgebiet, COUNT(*) as count "
                "FROM beck_resources GROUP BY keyword_normalized ORDER BY keyword"
            ).fetchall()
            print(f"\nStored Beck resources: {len(rows)} keywords")
            print("-" * 60)
            for row in rows:
                print(f"  {row['keyword']} ({row['rechtsgebiet']}) - {row['count']} resources")
            return
        finally:
            conn.close()

    if resources:
        for i, res in enumerate(resources, 1):
            print(f"\n  [{i}] {res.get('gericht', '?')} - {res.get('aktenzeichen', '?')}")
            print(f"      Datum: {res.get('datum', '?')}")
            leitsatz = res.get("leitsatz", "")
            if leitsatz:
                print(f"      Leitsatz: {leitsatz[:120]}...")
            print(f"      URL: {res.get('url', '?')}")


def main():
    parser = argparse.ArgumentParser(
        description="Beck-Online Resource Extraction - Pre-extract legal resources for article generation"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--titles", nargs="+",
        help="Article titles/keywords to extract resources for"
    )
    group.add_argument(
        "--from-plan", action="store_true",
        help="Extract resources for all planned articles in content plan"
    )
    group.add_argument(
        "--list", action="store_true",
        help="List stored resources"
    )

    parser.add_argument(
        "--rechtsgebiet",
        help="German legal area (auto-detected if not provided)"
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Use mock data (no Beck credentials needed)"
    )
    parser.add_argument(
        "--keyword",
        help="Filter keyword for --list"
    )
    parser.add_argument(
        "--output", "-o",
        help="Save extraction results as JSON"
    )

    args = parser.parse_args()

    if args.list:
        list_resources(keyword=args.keyword, rechtsgebiet=args.rechtsgebiet)
        return

    if args.titles:
        result = asyncio.run(
            extract_for_keywords(
                keywords=args.titles,
                rechtsgebiet=args.rechtsgebiet,
                use_mock=args.mock,
            )
        )
    elif args.from_plan:
        result = asyncio.run(
            extract_from_content_plan(
                rechtsgebiet=args.rechtsgebiet,
                use_mock=args.mock,
            )
        )
    else:
        parser.print_help()
        sys.exit(1)

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"Beck Extraction Complete")
    print(f"{'=' * 50}")
    print(f"Keywords processed: {result['total_keywords']}")
    print(f"Total resources stored: {result['total_resources']}")
    if result["errors"]:
        print(f"Errors: {len(result['errors'])}")
        for err in result["errors"]:
            print(f"  - {err}")

    for r in result["results"]:
        status = f"{r['resources_count']} resources" if not r.get("error") else f"ERROR: {r['error']}"
        print(f"  {r['keyword']}: {status}")

    # Save output if requested
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
