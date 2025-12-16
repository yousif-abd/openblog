"""
Quick test for Stage 12 - verify it compiles and basic structure works.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.local')

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import ExecutionContext
from pipeline.blog_generation.stage_12_hybrid_similarity_check import HybridSimilarityCheckStage
from pipeline.utils.hybrid_similarity_checker import HybridSimilarityChecker

async def quick_test():
    """Quick test - just verify Stage 12 initializes and can extract data."""
    print("=" * 80)
    print("QUICK STAGE 12 TEST")
    print("=" * 80)
    
    # Create minimal context with structured_data
    context = ExecutionContext(
        job_id="test_quick",
        job_config={"primary_keyword": "test keyword"}
    )
    
    # Mock structured_data
    class MockArticle:
        def dict(self):
            return {
                "Headline": "Test Article",
                "section_01_title": "Test Section",
                "section_01_content": "<p>Test content</p>",
                "primary_keyword": "test keyword"
            }
    
    context.structured_data = MockArticle()
    
    # Initialize Stage 12
    try:
        similarity_checker = HybridSimilarityChecker(enable_regeneration=True)
        stage12 = HybridSimilarityCheckStage(similarity_checker=similarity_checker)
        print("✅ Stage 12 initialized successfully")
        
        # Test data extraction
        article_data = stage12._extract_article_data(context)
        if article_data:
            print(f"✅ Data extraction works: {len(article_data)} fields")
        else:
            print("❌ Data extraction failed")
            return False
        
        # Test similarity check (should pass - no similar articles)
        context = await stage12.execute(context)
        
        if hasattr(context, 'similarity_report'):
            print(f"✅ Similarity check executed: score={getattr(context.similarity_report, 'similarity_score', 0):.1f}%")
            return True
        else:
            print("❌ No similarity report generated")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    print("\n" + ("✅ Test passed!" if success else "❌ Test failed!"))
    sys.exit(0 if success else 1)

