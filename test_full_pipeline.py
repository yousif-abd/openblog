#!/usr/bin/env python3
"""
Full Pipeline Test - Run the complete 5-stage pipeline for hypofriend.de

Tests the full pipeline with:
- Company: https://www.hypofriend.de/
- Keywords: 3 mortgage-related keywords
- Language: German
- Market: DE

Run: python test_full_pipeline.py
Run without images: python test_full_pipeline.py --skip-images
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
_BASE_PATH = Path(__file__).parent
if str(_BASE_PATH) not in sys.path:
    sys.path.insert(0, str(_BASE_PATH))

from dotenv import load_dotenv

load_dotenv(_BASE_PATH / ".env")

# Parse args before importing heavy modules
SKIP_IMAGES = "--skip-images" in sys.argv


async def run_test():
    """Run the full pipeline test."""
    from run_pipeline import run_pipeline

    # Test configuration
    company_url = "https://www.hypofriend.de/"
    keywords = [
        "Baufinanzierung Vergleich alle Plattformen",
        "Hypothekenzinsen vergleichen 750 Banken",
        "Europace eHyp Baufinex beste Konditionen",
    ]
    language = "de"
    market = "DE"

    # Output directory
    output_dir = _BASE_PATH / "test_output"
    output_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("OpenBlog Neo - Full Pipeline Test")
    print("=" * 70)
    print(f"Company URL: {company_url}")
    print(f"Language: {language} | Market: {market}")
    print(f"Skip Images: {SKIP_IMAGES}")
    print(f"Keywords ({len(keywords)}):")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i}. {kw}")
    print(f"Output: {output_dir}")
    print("=" * 70)
    print()

    start_time = datetime.now()

    try:
        # Run the full pipeline
        results = await run_pipeline(
            keywords=keywords,
            company_url=company_url,
            language=language,
            market=market,
            skip_images=SKIP_IMAGES,
            max_parallel=1,  # Sequential for clearer test output
            output_dir=output_dir,
            export_formats=["html", "markdown", "json"],
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Save full results
        results_file = output_dir / f"test_results_{results['job_id']}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Print summary
        print()
        print("=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        print(f"Job ID: {results['job_id']}")
        print(f"Company: {results['company']}")
        print(f"Duration: {duration:.1f}s")
        print(f"Articles: {results['articles_successful']}/{results['articles_total']} successful")
        print()

        # Per-article results
        print("Article Results:")
        print("-" * 70)
        for r in results["results"]:
            status = "OK" if r.get("article") and not r.get("error") else "FAILED"
            print(f"  [{status}] {r['keyword']}")
            if r.get("error"):
                print(f"        Error: {r['error']}")
            else:
                # Show stage reports
                for stage, report in r.get("reports", {}).items():
                    print(f"        {stage}: {report}")
                # Show exported files
                if r.get("exported_files"):
                    print(f"        Exported: {list(r['exported_files'].keys())}")

        print()
        print(f"Results saved to: {results_file}")
        print()

        # Generate markdown report
        md_report = output_dir / "test_report.md"
        with open(md_report, "w", encoding="utf-8") as f:
            f.write("# Full Pipeline Test Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Job ID:** `{results['job_id']}`\n\n")
            f.write(f"**Company:** {results['company']}\n\n")
            f.write(f"**Company URL:** {company_url}\n\n")
            f.write(f"**Language:** {language} | **Market:** {market}\n\n")
            f.write(f"**Duration:** {duration:.1f}s\n\n")
            f.write(f"**Skip Images:** {SKIP_IMAGES}\n\n")

            f.write("---\n\n## Keywords\n\n")
            for i, kw in enumerate(keywords, 1):
                f.write(f"{i}. {kw}\n")

            f.write("\n---\n\n## Results Summary\n\n")
            f.write(f"| Metric | Value |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Total Articles | {results['articles_total']} |\n")
            f.write(f"| Successful | {results['articles_successful']} |\n")
            f.write(f"| Failed | {results['articles_failed']} |\n")

            f.write("\n---\n\n## Article Details\n\n")
            for r in results["results"]:
                status = "PASS" if r.get("article") and not r.get("error") else "FAIL"
                f.write(f"### {r['keyword']}\n\n")
                f.write(f"**Status:** {status}\n\n")
                f.write(f"**Slug:** `{r['slug']}`\n\n")
                f.write(f"**Href:** `{r['href']}`\n\n")

                if r.get("error"):
                    f.write(f"**Error:** {r['error']}\n\n")
                else:
                    f.write("**Stage Reports:**\n\n")
                    f.write("| Stage | Details |\n")
                    f.write("|-------|---------|")
                    for stage, report in r.get("reports", {}).items():
                        f.write(f"\n| {stage} | {report} |")
                    f.write("\n\n")

                    if r.get("article"):
                        article = r["article"]
                        f.write(f"**Headline:** {article.get('Headline', 'N/A')}\n\n")
                        meta_desc = article.get("MetaDescription", "")
                        if meta_desc:
                            f.write(f"**Meta Description:** {meta_desc[:200]}...\n\n")

                    if r.get("exported_files"):
                        f.write("**Exported Files:**\n\n")
                        for fmt, path in r["exported_files"].items():
                            f.write(f"- {fmt}: `{path}`\n")
                        f.write("\n")

                f.write("---\n\n")

        print(f"Markdown report: {md_report}")

        # Return success/failure
        if results["articles_failed"] > 0:
            print("\n[FAIL] Some articles failed")
            return 1
        else:
            print("\n[PASS] All articles generated successfully!")
            return 0

    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_test())
    sys.exit(exit_code)
