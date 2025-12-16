"""
Test script to verify Stages 6-8 consolidation into Stages 2-3.

Tests:
1. Stage 2 generates ToC labels and metadata
2. Stage 3 validates FAQ/PAA
3. All results are stored in parallel_results correctly
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv('.env.local')

from pipeline.core import ExecutionContext, WorkflowEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_consolidation():
    """Test that Stages 6-8 consolidation works correctly."""
    
    # Create minimal job config (as dict, matching test patterns)
    job_config = {
        "primary_keyword": "cloud security best practices",
        "company_url": "https://scaile.tech",
        "word_count": 2000,
        "language": "en",
        "tone": "professional"
    }
    
    # Create minimal company data (as dict)
    company_data = {
        "company_name": "SCAILE",
        "company_url": "https://scaile.tech",
        "industry": "AI Development Tools",
        "description": "SCAILE provides AI-powered development tools",
    }
    
    # Initialize context
    context = ExecutionContext(
        job_id="test_consolidation",
        job_config=job_config,
        company_data=company_data,
    )
    
    logger.info("=" * 80)
    logger.info("Testing Stages 6-8 Consolidation")
    logger.info("=" * 80)
    
    try:
        # Run pipeline up to Stage 3 (includes ToC, Metadata, FAQ/PAA)
        logger.info("\n🚀 Running pipeline Stages 0-3...")
        
        # Run stages individually to test consolidation
        from pipeline.blog_generation.stage_00_data_fetch import DataFetchStage
        from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
        from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
        from pipeline.blog_generation.stage_03_quality_refinement import QualityRefinementStage
        
        # Stage 0
        logger.info("Running Stage 0...")
        stage0 = DataFetchStage()
        context = await stage0.execute(context)
        
        # Stage 1
        logger.info("Running Stage 1...")
        stage1 = PromptBuildStage()
        context = await stage1.execute(context)
        
        # Stage 2 (includes ToC + Metadata generation)
        logger.info("Running Stage 2 (includes ToC + Metadata)...")
        stage2 = GeminiCallStage()
        context = await stage2.execute(context)
        
        # Stage 3 (includes FAQ/PAA validation)
        logger.info("Running Stage 3 (includes FAQ/PAA validation)...")
        stage3 = QualityRefinementStage()
        context = await stage3.execute(context)
        
        # Check Stage 2 outputs (ToC and Metadata)
        logger.info("\n" + "=" * 80)
        logger.info("Stage 2 Results (ToC + Metadata)")
        logger.info("=" * 80)
        
        if "toc_dict" in context.parallel_results:
            toc_dict = context.parallel_results["toc_dict"]
            logger.info(f"✅ ToC labels generated: {len(toc_dict)} entries")
            for key, label in list(toc_dict.items())[:5]:
                logger.info(f"   {key}: {label}")
        else:
            logger.error("❌ ToC labels NOT found in parallel_results")
        
        if "metadata" in context.parallel_results:
            metadata = context.parallel_results["metadata"]
            logger.info(f"✅ Metadata generated:")
            logger.info(f"   Word count: {getattr(metadata, 'word_count', 'N/A')}")
            logger.info(f"   Read time: {getattr(metadata, 'read_time', 'N/A')} min")
            logger.info(f"   Publication date: {getattr(metadata, 'publication_date', 'N/A')}")
        else:
            logger.error("❌ Metadata NOT found in parallel_results")
        
        # Check Stage 3 outputs (FAQ/PAA validation)
        logger.info("\n" + "=" * 80)
        logger.info("Stage 3 Results (FAQ/PAA Validation)")
        logger.info("=" * 80)
        
        if "faq_items" in context.parallel_results:
            faq_items = context.parallel_results["faq_items"]
            faq_count = getattr(faq_items, 'count', lambda: len(faq_items.items) if hasattr(faq_items, 'items') else 0)()
            logger.info(f"✅ FAQ items validated: {faq_count} items")
            if hasattr(faq_items, 'items'):
                for item in faq_items.items[:3]:
                    logger.info(f"   Q: {item.question[:60]}...")
        else:
            logger.error("❌ FAQ items NOT found in parallel_results")
        
        if "paa_items" in context.parallel_results:
            paa_items = context.parallel_results["paa_items"]
            paa_count = getattr(paa_items, 'count', lambda: len(paa_items.items) if hasattr(paa_items, 'items') else 0)()
            logger.info(f"✅ PAA items validated: {paa_count} items")
            if hasattr(paa_items, 'items'):
                for item in paa_items.items[:3]:
                    logger.info(f"   Q: {item.question[:60]}...")
        else:
            logger.error("❌ PAA items NOT found in parallel_results")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("Consolidation Test Summary")
        logger.info("=" * 80)
        
        checks = {
            "ToC labels": "toc_dict" in context.parallel_results,
            "Metadata": "metadata" in context.parallel_results,
            "FAQ items": "faq_items" in context.parallel_results,
            "PAA items": "paa_items" in context.parallel_results,
        }
        
        all_passed = all(checks.values())
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            logger.info(f"{status} {check_name}")
        
        if all_passed:
            logger.info("\n🎉 All consolidation checks passed!")
        else:
            logger.error("\n❌ Some consolidation checks failed!")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_consolidation())
    sys.exit(0 if success else 1)

