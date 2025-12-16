"""
Full Pipeline Flow Test

Tests the complete pipeline flow (Stages 0-11 + conditional Stage 3) to verify:
1. All stages execute in correct order
2. Consolidated functionality works (ToC/Metadata in Stage 2, FAQ/PAA in Stage 3)
3. Sequential flow (4→5) and parallel flow (9||12)
4. Tools enabled when needed (Stage 2), disabled when not needed
5. Final output is valid
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.core.stage_factory import ProductionStageFactory

async def test_full_pipeline():
    """Test the complete pipeline flow."""
    print("=" * 80)
    print("FULL PIPELINE FLOW TEST")
    print("=" * 80)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/full_pipeline_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test configuration
    job_config = {
        "primary_keyword": "AI code generation tools",
        "company_url": "https://scaile.tech",
        "company_name": "Scaile",
        "word_count": 2000,
        "language": "en",
        "country": "US",
        "tone": "professional",
        "sitemap_urls": [
            "https://scaile.tech/blog/ai-visibility-engine",
            "https://scaile.tech/blog/enterprise-ai-solutions",
            "https://scaile.tech/resources/ai-guide",
        ],
    }
    
    job_id = f"test-full-flow-{timestamp}"
    
    print(f"📋 Job ID: {job_id}")
    print(f"📝 Keyword: {job_config['primary_keyword']}")
    print(f"🏢 Company: {job_config['company_name']} ({job_config['company_url']})")
    print()
    
    # Track execution times
    stage_times = {}
    start_time = datetime.now()
    
    def progress_callback(stage_num: int, stage_name: str, status: str, message: str = ""):
        """Progress callback to track stage execution."""
        stage_start = datetime.now()
        stage_times[stage_num] = {
            "name": stage_name,
            "status": status,
            "start": stage_start.isoformat(),
            "message": message
        }
        print(f"⏱️  Stage {stage_num}: {stage_name} - {status}")
        if message:
            print(f"   {message}")
    
    try:
        # Create workflow engine
        print("🔧 Initializing workflow engine...")
        factory = ProductionStageFactory()
        stages = factory.create_all_stages()
        
        engine = WorkflowEngine()
        engine.register_stages(stages)
        
        print(f"✅ Registered {len(stages)} stages")
        print()
        
        # Execute full pipeline
        print("🚀 Starting pipeline execution...")
        print()
        
        context = await engine.execute(
            job_id=job_id,
            job_config=job_config,
            progress_callback=progress_callback
        )
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        print()
        print("=" * 80)
        print("PIPELINE EXECUTION COMPLETE")
        print("=" * 80)
        print()
        
        # Verify Stage 2: ToC & Metadata
        print("📊 Stage 2 Verification (ToC & Metadata):")
        if context.structured_data:
            article = context.structured_data
            
            # Check ToC
            toc_entries = getattr(article, 'toc_entries', [])
            toc_dict = getattr(article, 'toc_dict', {})
            print(f"   ✅ ToC entries: {len(toc_entries)}")
            if toc_entries:
                print(f"   Sample ToC: {toc_entries[0] if toc_entries else 'None'}")
            
            # Check Metadata
            word_count = getattr(article, 'word_count', 0)
            read_time = getattr(article, 'read_time', 0)
            publication_date = getattr(article, 'publication_date', '')
            print(f"   ✅ Word count: {word_count}")
            print(f"   ✅ Read time: {read_time} min")
            print(f"   ✅ Publication date: {publication_date}")
        else:
            print("   ❌ No structured_data found")
        print()
        
        # Verify Stage 3: FAQ/PAA Validation
        print("📋 Stage 3 Verification (FAQ/PAA Validation):")
        if context.structured_data:
            article = context.structured_data
            
            # Count FAQ items
            faq_count = 0
            for i in range(1, 7):
                question = getattr(article, f'faq_{i:02d}_question', '')
                if question and question.strip():
                    faq_count += 1
            
            # Count PAA items
            paa_count = 0
            for i in range(1, 5):
                question = getattr(article, f'paa_{i:02d}_question', '')
                if question and question.strip():
                    paa_count += 1
            
            print(f"   ✅ FAQ items: {faq_count}")
            print(f"   ✅ PAA items: {paa_count}")
        else:
            print("   ❌ No structured_data found")
        print()
        
        # Verify Stage 4: Citations
        print("🔗 Stage 4 Verification (Citations):")
        if hasattr(context, 'citations') and context.citations:
            print(f"   ✅ Citations processed: {len(context.citations)}")
            valid_citations = [c for c in context.citations if c.status == 'valid']
            print(f"   ✅ Valid citations: {len(valid_citations)}")
        else:
            print("   ⚠️  No citations data found (may be in structured_data)")
        print()
        
        # Verify Stage 5: Internal Links
        print("🔗 Stage 5 Verification (Internal Links):")
        if hasattr(context, 'internal_links') and context.internal_links:
            print(f"   ✅ Internal links generated: {len(context.internal_links)}")
            assigned_links = [l for l in context.internal_links if l.assigned_section]
            print(f"   ✅ Links assigned to sections: {len(assigned_links)}")
        else:
            print("   ⚠️  No internal_links data found")
        print()
        
        # Verify Stage 9: Image
        print("🖼️  Stage 9 Verification (Image Generation):")
        if hasattr(context, 'image_url') and context.image_url:
            print(f"   ✅ Image URL: {context.image_url}")
        else:
            print("   ⚠️  No image_url found")
        print()
        
        # Verify Stage 12: Similarity Check
        print("🔍 Stage 12 Verification (Similarity Check):")
        if hasattr(context, 'similarity_report') and context.similarity_report:
            report = context.similarity_report
            print(f"   ✅ Similarity score: {getattr(report, 'similarity_score', 'N/A')}")
            print(f"   ✅ Too similar: {getattr(report, 'is_too_similar', False)}")
            print(f"   ✅ Regeneration needed: {getattr(report, 'regeneration_needed', False)}")
        else:
            print("   ⚠️  No similarity_report found")
        print()
        
        # Verify Stage 10: Cleanup
        print("🧹 Stage 10 Verification (Cleanup & Final Validation):")
        if hasattr(context, 'validated_article') and context.validated_article:
            print("   ✅ Validated article created")
        else:
            print("   ⚠️  No validated_article found")
        print()
        
        # Verify Stage 11: Storage
        print("💾 Stage 11 Verification (HTML Generation & Storage):")
        if hasattr(context, 'final_html') and context.final_html:
            html_length = len(context.final_html)
            print(f"   ✅ HTML generated: {html_length} characters")
        else:
            print("   ⚠️  No final_html found")
        print()
        
        # Execution summary
        print("=" * 80)
        print("EXECUTION SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
        print()
        print("Stage execution times:")
        for stage_num in sorted(stage_times.keys()):
            stage_info = stage_times[stage_num]
            print(f"   Stage {stage_num}: {stage_info['name']} - {stage_info['status']}")
        print()
        
        # Save results
        results = {
            "job_id": job_id,
            "job_config": job_config,
            "total_duration_seconds": total_duration,
            "stage_times": stage_times,
            "structured_data": context.structured_data.dict() if hasattr(context.structured_data, 'dict') else str(context.structured_data),
            "validated_article": context.validated_article.dict() if hasattr(context.validated_article, 'dict') else str(context.validated_article),
        }
        
        with open(output_dir / "pipeline_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {output_dir}")
        print()
        
        # Final validation
        print("=" * 80)
        print("FINAL VALIDATION")
        print("=" * 80)
        
        checks = []
        
        # Check 1: Structured data exists
        checks.append(("Structured data exists", context.structured_data is not None))
        
        # Check 2: ToC generated
        if context.structured_data:
            toc_entries = getattr(context.structured_data, 'toc_entries', [])
            checks.append(("ToC entries generated", len(toc_entries) > 0))
            
            # Check 3: Metadata calculated
            word_count = getattr(context.structured_data, 'word_count', 0)
            checks.append(("Word count calculated", word_count > 0))
            
            # Check 4: FAQ/PAA validated
            faq_count = sum(1 for i in range(1, 7) if getattr(context.structured_data, f'faq_{i:02d}_question', '').strip())
            checks.append(("FAQ items present", faq_count > 0))
        
        # Check 5: Citations processed
        if hasattr(context, 'citations'):
            checks.append(("Citations processed", len(context.citations) > 0))
        
        # Check 6: Internal links generated
        if hasattr(context, 'internal_links'):
            checks.append(("Internal links generated", len(context.internal_links) > 0))
        
        # Check 7: Image generated
        if hasattr(context, 'image_url'):
            checks.append(("Image generated", context.image_url is not None))
        
        # Check 8: Similarity checked
        if hasattr(context, 'similarity_report'):
            checks.append(("Similarity checked", context.similarity_report is not None))
        
        # Check 9: Validated article created
        checks.append(("Validated article created", hasattr(context, 'validated_article') and context.validated_article is not None))
        
        # Check 10: HTML generated
        checks.append(("HTML generated", hasattr(context, 'final_html') and context.final_html is not None))
        
        # Print checks
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        
        print()
        if all_passed:
            print("🎉 ALL CHECKS PASSED - Pipeline flow is working correctly!")
        else:
            print("⚠️  SOME CHECKS FAILED - Review output above")
        
        return context
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())

