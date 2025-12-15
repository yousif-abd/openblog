"""
Test Stage 4: Citations Validation & Formatting
Tests citation parsing, enhancement, and HTML formatting.
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

from pipeline.core.execution_context import ExecutionContext
from pipeline.core.company_context import CompanyContext
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.models.output_schema import ArticleOutput

async def test_stage4_citations():
    """Test Stage 4 citations processing."""
    print("=" * 80)
    print("STAGE 4 CITATIONS TEST")
    print("=" * 80)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/stage4_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create execution context
    context = ExecutionContext(
        job_id="test_stage4_citations",
        job_config={
            "primary_keyword": "cloud security best practices",
            "company_url": "https://scaile.tech",
            "word_count": 2000,
            "language": "en",
            "tone": "professional"
        },
        company_data={
            "company_url": "https://scaile.tech",
            "company_name": "Scaile",
            "industry": "Technology",
            "description": "Scaile is a technology company"
        }
    )
    
    # ============================================================
    # STAGE 1: Build Prompt
    # ============================================================
    print("📝 STAGE 1: Building prompt...")
    stage_1 = PromptBuildStage()
    context = await stage_1.execute(context)
    
    if not context.prompt:
        print("❌ Stage 1 failed")
        return
    
    print(f"✅ Stage 1 complete")
    print()
    
    # ============================================================
    # STAGE 2: Generate Content + Extract
    # ============================================================
    print("🚀 STAGE 2: Generating content with Gemini...")
    print("   (This will take 2-5 minutes)")
    print()
    
    stage_2 = GeminiCallStage()
    context = await stage_2.execute(context)
    
    if not context.structured_data:
        print("❌ Stage 2 failed - no structured_data")
        return
    
    print("✅ Stage 2 complete")
    print()
    
    # ============================================================
    # ANALYZE STAGE 2 OUTPUT
    # ============================================================
    print("📊 ANALYZING STAGE 2 OUTPUT...")
    print()
    
    article = context.structured_data
    sources_text = article.Sources or ""
    
    print(f"Sources field:")
    print(f"  Length: {len(sources_text)} chars")
    print(f"  Preview: {sources_text[:200]}...")
    print()
    
    grounding_urls = getattr(context, 'grounding_urls', [])
    print(f"Grounding URLs: {len(grounding_urls)}")
    if grounding_urls:
        print(f"  Sample domains: {[g.get('domain', g.get('title', ''))[:30] for g in grounding_urls[:5]]}")
    print()
    
    # Save Stage 2 output
    stage2_file = output_dir / "stage2_output.json"
    with open(stage2_file, 'w') as f:
        json.dump(article.model_dump(), f, indent=2, default=str)
    
    # ============================================================
    # STAGE 4: Citations Processing
    # ============================================================
    print("🔗 STAGE 4: Processing citations...")
    print()
    
    stage_4 = CitationsStage()
    
    try:
        context_after_4 = await stage_4.execute(context)
        print("✅ Stage 4 completed successfully")
        print()
    except Exception as e:
        print(f"❌ Stage 4 failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ============================================================
    # ANALYZE STAGE 4 OUTPUT
    # ============================================================
    print("📊 ANALYZING STAGE 4 OUTPUT...")
    print()
    
    citations_html = context_after_4.parallel_results.get("citations_html", "")
    citations_count = context_after_4.parallel_results.get("citations_count", 0)
    citations_list = context_after_4.parallel_results.get("citations_list")
    validated_citation_map = context_after_4.parallel_results.get("validated_citation_map", {})
    
    print(f"Citations HTML:")
    print(f"  Length: {len(citations_html)} chars")
    print(f"  Count: {citations_count}")
    print()
    
    if citations_list:
        print(f"Citation Details:")
        for citation in citations_list.citations[:10]:  # Show first 10
            print(f"  [{citation.number}]: {citation.url[:80]}...")
            print(f"      Title: {citation.title[:60]}...")
        if len(citations_list.citations) > 10:
            print(f"  ... and {len(citations_list.citations) - 10} more")
        print()
    
    print(f"Validated Citation Map: {len(validated_citation_map)} entries")
    print()
    
    # Analyze URL quality
    if citations_list:
        domain_only = 0
        full_urls = 0
        for citation in citations_list.citations:
            url = citation.url
            if url.startswith('http://') or url.startswith('https://'):
                # Check if it's domain-only (no path or just /)
                from urllib.parse import urlparse
                parsed = urlparse(url)
                path_parts = [p for p in parsed.path.split('/') if p]
                if len(path_parts) <= 1:
                    domain_only += 1
                else:
                    full_urls += 1
        
        print(f"URL Quality:")
        print(f"  Domain-only URLs: {domain_only}")
        print(f"  Full URLs: {full_urls}")
        if citations_count > 0:
            full_url_pct = (full_urls / citations_count) * 100
            print(f"  Full URL percentage: {full_url_pct:.1f}%")
        print()
    
    # Save Stage 4 output
    stage4_file = output_dir / "stage4_output.json"
    stage4_data = {
        "citations_html": citations_html,
        "citations_count": citations_count,
        "citations": [
            {
                "number": c.number,
                "url": c.url,
                "title": c.title
            }
            for c in (citations_list.citations if citations_list else [])
        ],
        "validated_citation_map": validated_citation_map
    }
    with open(stage4_file, 'w') as f:
        json.dump(stage4_data, f, indent=2, default=str)
    
    # Save HTML preview
    html_preview_file = output_dir / "citations_html_preview.html"
    with open(html_preview_file, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Stage 4 Citations Output</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; }}
        h1 {{ color: #333; }}
        .citations {{ margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>Stage 4 Citations Output</h1>
    <p><strong>Total Citations:</strong> {citations_count}</p>
    <div class="citations">
        {citations_html}
    </div>
</body>
</html>""")
    
    # ============================================================
    # VERIFICATION
    # ============================================================
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    print()
    
    # Check 1: Citations extracted
    print("1. Citations Extraction:")
    if citations_count > 0:
        print(f"   ✅ PASS: {citations_count} citations extracted")
    else:
        print(f"   ❌ FAIL: No citations extracted")
    print()
    
    # Check 2: HTML formatting
    print("2. HTML Formatting:")
    if citations_html and len(citations_html) > 0:
        print(f"   ✅ PASS: HTML generated ({len(citations_html)} chars)")
    else:
        print(f"   ❌ FAIL: No HTML generated")
    print()
    
    # Check 3: URL quality
    print("3. URL Quality:")
    if citations_count > 0:
        full_url_pct = (full_urls / citations_count) * 100
        if full_url_pct >= 70:
            print(f"   ✅ PASS: {full_url_pct:.1f}% full URLs (target: 70%+)")
        else:
            print(f"   ⚠️  WARNING: {full_url_pct:.1f}% full URLs (target: 70%+)")
    print()
    
    # Check 4: Grounding URL usage
    print("4. Grounding URL Enhancement:")
    if grounding_urls and citations_count > 0:
        print(f"   ✅ INFO: {len(grounding_urls)} grounding URLs available")
        print(f"      Citations enhanced with specific URLs from Stage 2")
    else:
        print(f"   ⚠️  INFO: No grounding URLs available")
    print()
    
    # Check 5: Citation map
    print("5. Citation Map:")
    if len(validated_citation_map) == citations_count:
        print(f"   ✅ PASS: Citation map matches citation count")
    else:
        print(f"   ⚠️  WARNING: Citation map size ({len(validated_citation_map)}) != count ({citations_count})")
    print()
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("=" * 80)
    print(f"✅ Test complete! Output saved to: {output_dir}")
    print("=" * 80)
    print()
    print("Files created:")
    print(f"  - {stage2_file.name}")
    print(f"  - {stage4_file.name}")
    print(f"  - {html_preview_file.name}")
    print()
    
    print("FINAL SUMMARY:")
    print(f"  Citations extracted: {citations_count}")
    print(f"  Full URLs: {full_urls}/{citations_count} ({full_url_pct:.1f}%)" if citations_count > 0 else "  Full URLs: N/A")
    print(f"  HTML generated: {'✅' if citations_html else '❌'}")

if __name__ == "__main__":
    asyncio.run(test_stage4_citations())

