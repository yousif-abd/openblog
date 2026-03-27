"""
Webinar Processing CLI

Process webinar recordings from Google Drive, generate transcripts and key points,
store in database, and optionally generate newsletter content.

Usage:
    # Process all new videos in Drive folder
    python -m webinar.process_webinars --folder-id FOLDER_ID

    # Process a single file from Drive
    python -m webinar.process_webinars --file-id FILE_ID

    # Process a local file (no Drive needed)
    python -m webinar.process_webinars --local /path/to/video.mp4

    # Generate newsletter for a month
    python -m webinar.process_webinars --newsletter 2026-03

    # List processed webinars
    python -m webinar.process_webinars --list
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
from webinar.webinar_processor import process_folder, process_webinar, process_local_file
from webinar.newsletter_formatter import NewsletterFormatter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def list_webinars():
    """List all processed webinars."""
    db = OpenBlogDB()
    webinars = db.get_all_webinars()

    if not webinars:
        print("\nNo processed webinars found.")
        return

    print(f"\nProcessed Webinars: {len(webinars)}")
    print("-" * 80)

    for w in webinars:
        duration = (w.get("duration_seconds", 0) or 0) // 60
        key_points = w.get("key_points", [])
        n_kp = len(key_points) if isinstance(key_points, list) else 0
        print(
            f"  [{w.get('id')}] {w.get('title', w.get('filename', '?'))}"
            f" | {duration} min | {n_kp} key points"
            f" | {w.get('rechtsgebiet', '?')}"
            f" | {w.get('newsletter_month', '?')}"
        )


def show_newsletter(month: str, output: str = None):
    """Generate and display/save newsletter."""
    formatter = NewsletterFormatter()
    result = formatter.format_monthly(month)

    if not result["webinars"]:
        print(f"\nNo webinars found for {month}")
        return

    print(f"\nNewsletter for {month}: {len(result['webinars'])} webinars")
    print("=" * 60)
    print(result["plain_text"])

    if output:
        output_path = Path(output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output.endswith(".html"):
            content = result["html_snippet"]
        else:
            content = result["plain_text"]

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\nSaved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Webinar Processing - Transcribe and extract key points from webinar recordings"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--folder-id",
        help="Google Drive folder ID to process all new videos",
    )
    group.add_argument(
        "--file-id",
        help="Process a single Google Drive file by ID",
    )
    group.add_argument(
        "--local",
        help="Process a local video/audio file",
    )
    group.add_argument(
        "--newsletter",
        metavar="YYYY-MM",
        help="Generate newsletter for a specific month",
    )
    group.add_argument(
        "--list", action="store_true",
        help="List all processed webinars",
    )

    parser.add_argument(
        "--output", "-o",
        help="Output file path (for newsletter: .html or .txt)",
    )
    parser.add_argument(
        "--link-keywords", nargs="+",
        help="Manually link this webinar to specific keywords",
    )

    args = parser.parse_args()

    if args.list:
        list_webinars()
        return

    if args.newsletter:
        show_newsletter(args.newsletter, output=args.output)
        return

    # Process webinars
    if args.folder_id:
        results = asyncio.run(process_folder(folder_id=args.folder_id))
    elif args.file_id:
        result = asyncio.run(
            process_webinar(drive_file_id=args.file_id, filename=args.file_id)
        )
        results = [result]
    elif args.local:
        result = asyncio.run(process_local_file(file_path=args.local))
        results = [result]
    else:
        parser.print_help()
        sys.exit(1)

    # Manual keyword linking
    if args.link_keywords and results:
        db = OpenBlogDB()
        for result in results:
            if not result.error:
                # Find webinar ID
                webinars = db.get_all_webinars()
                for w in webinars:
                    if w.get("drive_file_id") == result.drive_file_id:
                        for kw in args.link_keywords:
                            db.link_webinar_to_keyword(w["id"], kw)
                            print(f"  Linked '{result.title}' → '{kw}'")
                        break

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"Webinar Processing Complete")
    print(f"{'=' * 50}")
    print(f"Processed: {len(results)}")

    for r in results:
        if r.error:
            print(f"  ✗ {r.filename}: {r.error}")
        else:
            duration = r.duration_seconds // 60 if r.duration_seconds else 0
            print(
                f"  ✓ {r.title or r.filename} | {duration} min | "
                f"{len(r.key_points)} key points | {r.ai_calls} AI calls"
            )


if __name__ == "__main__":
    main()
