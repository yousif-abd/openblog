"""
Test Stage 5 link embedding with production content from Stages 0-4
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

from pipeline.core.execution_context import ExecutionContext
from pipeline.blog_generation.stage_00_data_fetch import DataFetchStage
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
from pipeline.blog_generation.stage_03_quality_refinement import QualityRefinementStage
from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.blog_generation.stage_05_internal_links import InternalLinksStage

async def test_stage5_link_embedding():
    """Test Stage 5 link embedding with full pipeline content."""
    print("=" * 80)
    print("STAGE 5 LINK EMBEDDING TEST (Production Content)")
    print("=" * 80)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/stage5_embedding_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create execution context
    context = ExecutionContext(
        job_id="test_link_embedding",
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
    
    try:
        # Stage 0: Data Fetch
        print("🔍 Stage 0: Data Fetch & Sitemap Crawling...")
        stage0 = DataFetchStage()
        context = await stage0.execute(context)
        print(f"✅ Stage 0 complete")
        print()
        
        # Stage 1: Prompt Build
        print("📝 Stage 1: Building prompt...")
        stage1 = PromptBuildStage()
        context = await stage1.execute(context)
        print(f"✅ Stage 1 complete")
        print()
        
        # Stage 2: Content Generation
        print("🤖 Stage 2: Generating content...")
        stage2 = GeminiCallStage()
        context = await stage2.execute(context)
        if not context.structured_data:
            print("❌ Stage 2 failed - no structured_data generated")
            return
        print(f"✅ Stage 2 complete")
        print()
        
        # Save original content (before link embedding)
        original_content = {}
        for i in range(1, 7):
            field_name = f"section_{i:02d}_content"
            if hasattr(context.structured_data, field_name):
                original_content[field_name] = getattr(context.structured_data, field_name)
        
        # Stage 3: Quality Refinement
        print("✨ Stage 3: Quality refinement...")
        stage3 = QualityRefinementStage()
        context = await stage3.execute(context)
        print(f"✅ Stage 3 complete")
        print()
        
        # Stage 4: Citations
        print("🔗 Stage 4: Citations...")
        stage4 = CitationsStage()
        context = await stage4.execute(context)
        print(f"✅ Stage 4 complete")
        print()
        
        # Stage 5: Internal Links (with embedding)
        print("📎 Stage 5: Internal Links Generation & Embedding...")
        stage5 = InternalLinksStage()
        context = await stage5.execute(context)
        
        section_internal_links = context.parallel_results.get("section_internal_links", {})
        print(f"✅ Stage 5 complete")
        print()
        
        # Compare before/after for sections with embedded links
        print("=" * 80)
        print("LINK EMBEDDING RESULTS")
        print("=" * 80)
        print()
        
        embedded_sections = []
        for section_num, links in section_internal_links.items():
            if links:
                field_name = f"section_{section_num:02d}_content"
                original = original_content.get(field_name, "")
                if hasattr(context.structured_data, field_name):
                    updated = getattr(context.structured_data, field_name)
                    
                    # Count links in updated content
                    link_count = updated.count('<a href=')
                    
                    if link_count > 0:
                        embedded_sections.append({
                            "section": section_num,
                            "links_assigned": len(links),
                            "links_embedded": link_count,
                            "original_length": len(original),
                            "updated_length": len(updated),
                            "original_preview": original[:200] + "..." if len(original) > 200 else original,
                            "updated_preview": updated[:300] + "..." if len(updated) > 300 else updated
                        })
                        
                        print(f"Section {section_num}:")
                        print(f"   Links assigned: {len(links)}")
                        print(f"   Links embedded: {link_count}")
                        print(f"   Original length: {len(original)} chars")
                        print(f"   Updated length: {len(updated)} chars")
                        print()
                        
                        # Show link details
                        print(f"   Assigned links:")
                        for link in links:
                            print(f"      - {link.get('title', 'N/A')}")
                        print()
                        
                        # Show before/after preview
                        print(f"   Original content preview:")
                        print(f"      {original[:150]}...")
                        print()
                        print(f"   Updated content preview (with embedded links):")
                        print(f"      {updated[:200]}...")
                        print()
                        print("-" * 80)
                        print()
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Stages 0-4: Production content generated")
        print(f"✅ Stage 5: Links embedded in {len(embedded_sections)} section(s)")
        print()
        
        if embedded_sections:
            total_links_embedded = sum(s["links_embedded"] for s in embedded_sections)
            print(f"   Total links embedded: {total_links_embedded}")
            print(f"   Sections with embedded links:")
            for s in embedded_sections:
                print(f"      - Section {s['section']}: {s['links_embedded']} link(s)")
        else:
            print("   ⚠️ No links were embedded (check if links were assigned)")
        
        print()
        print(f"📁 Output saved to: {output_dir}")
        
        # Save detailed results
        with open(output_dir / "link_embedding_results.json", "w") as f:
            json.dump({
                "embedded_sections": embedded_sections,
                "section_internal_links": {
                    str(k): v for k, v in section_internal_links.items()
                },
                "total_sections_with_links": len(embedded_sections),
                "total_links_embedded": sum(s["links_embedded"] for s in embedded_sections) if embedded_sections else 0
            }, f, indent=2)
        
        # Save sample section content (before/after)
        if embedded_sections:
            sample_section = embedded_sections[0]
            section_num = sample_section["section"]
            field_name = f"section_{section_num:02d}_content"
            
            with open(output_dir / f"section_{section_num}_before_after.html", "w") as f:
                f.write("<!DOCTYPE html>\n<html><head><title>Before/After Link Embedding</title></head><body>\n")
                f.write("<h2>BEFORE (Original Content)</h2>\n")
                f.write(f"<div>{original_content.get(field_name, '')}</div>\n")
                f.write("<h2>AFTER (With Embedded Links)</h2>\n")
                if hasattr(context.structured_data, field_name):
                    f.write(f"<div>{getattr(context.structured_data, field_name)}</div>\n")
                f.write("</body></html>\n")
        
        print()
        print("✅ LINK EMBEDDING TEST COMPLETE")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    asyncio.run(test_stage5_link_embedding())

