"""
Test Stage 4 Refactored Sequential Flow
Tests the new sequential citation processing flow.
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
from pipeline.blog_generation.stage_03_quality_refinement import QualityRefinementStage
from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.models.output_schema import ArticleOutput

async def test_stage4_refactored():
    """Test Stage 4 refactored sequential flow."""
    print("=" * 80)
    print("STAGE 4 REFACTORED FLOW TEST")
    print("=" * 80)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/stage4_refactored_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create execution context
    context = ExecutionContext(
        job_id="test_stage4_refactored",
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
    # STAGE 2: Generate Content
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
    print(f"   Sources field length: {len(context.structured_data.Sources or '')} chars")
    print(f"   Grounding URLs: {len(getattr(context, 'grounding_urls', []))}")
    print()
    
    # Save Stage 2 output
    stage2_file = output_dir / "stage2_output.json"
    with open(stage2_file, 'w') as f:
        json.dump(context.structured_data.model_dump(), f, indent=2, default=str)
    
    # ============================================================
    # STAGE 3: Quality Refinement (includes domain-only enhancement)
    # ============================================================
    print("🔧 STAGE 3: Quality refinement (includes domain-only URL enhancement)...")
    stage_3 = QualityRefinementStage()
    context = await stage_3.execute(context)
    
    print("✅ Stage 3 complete")
    print(f"   Sources field length after enhancement: {len(context.structured_data.Sources or '')} chars")
    print()
    
    # Save Stage 3 output
    stage3_file = output_dir / "stage3_output.json"
    with open(stage3_file, 'w') as f:
        json.dump(context.structured_data.model_dump(), f, indent=2, default=str)
    
    # ============================================================
    # STAGE 4: Citations (Refactored Sequential Flow)
    # ============================================================
    print("🔗 STAGE 4: Citations processing (refactored sequential flow)...")
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
    # ANALYZE RESULTS
    # ============================================================
    print("=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
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
            if citation.meta_description:
                print(f"      Meta: {citation.meta_description[:50]}...")
        if len(citations_list.citations) > 10:
            print(f"  ... and {len(citations_list.citations) - 10} more")
        print()
    
    print(f"Validated Citation Map: {len(validated_citation_map)} entries")
    print()
    
    # Check body citations were updated
    print("Body Citation Updates:")
    original_sources = context.structured_data.Sources or ""
    updated_sources = context_after_4.structured_data.Sources or ""
    
    # Check if any body fields changed
    body_fields_changed = 0
    for field in ['Intro', 'Direct_Answer'] + [f'section_{i:02d}_content' for i in range(1, 10)]:
        original = getattr(context.structured_data, field, '') or ''
        updated = getattr(context_after_4.structured_data, field, '') or ''
        if original != updated:
            body_fields_changed += 1
    
    print(f"  Body fields updated: {body_fields_changed}")
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
                "title": c.title,
                "meta_description": c.meta_description
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
    <title>Stage 4 Citations Output (Refactored)</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; }}
        h1 {{ color: #333; }}
        .citations {{ margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>Stage 4 Citations Output (Refactored Sequential Flow)</h1>
    <p><strong>Total Citations:</strong> {citations_count}</p>
    <p><strong>Body Fields Updated:</strong> {body_fields_changed}</p>
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
    
    # Check 3: Meta description support
    print("3. Meta Description Support:")
    if citations_list:
        meta_count = sum(1 for c in citations_list.citations if c.meta_description)
        print(f"   ✅ INFO: {meta_count}/{len(citations_list.citations)} citations have meta_description")
    print()
    
    # Check 4: Body citation updates
    print("4. Body Citation Updates:")
    if body_fields_changed > 0:
        print(f"   ✅ PASS: {body_fields_changed} body fields updated")
    else:
        print(f"   ⚠️  INFO: No body fields updated (may be normal if no broken citations)")
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
    print(f"  - {stage3_file.name}")
    print(f"  - {stage4_file.name}")
    print(f"  - {html_preview_file.name}")
    print()
    
    print("FINAL SUMMARY:")
    print(f"  Citations extracted: {citations_count}")
    print(f"  HTML generated: {'✅' if citations_html else '❌'}")
    print(f"  Body fields updated: {body_fields_changed}")
    print(f"  Meta descriptions: {meta_count if citations_list else 0}/{citations_count}")

if __name__ == "__main__":
    asyncio.run(test_stage4_refactored())


