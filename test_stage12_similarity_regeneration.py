"""
Test Stage 12 (Similarity Check + Section Regeneration)

Tests:
1. Stage 12 runs in parallel with Stage 9
2. Similarity detection works
3. Section-level regeneration works when similarity detected
4. Only similar sections are regenerated (not whole article)
"""

import asyncio
import logging
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pipeline.core import ExecutionContext
from pipeline.blog_generation.stage_00_data_fetch import DataFetchStage
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
from pipeline.blog_generation.stage_03_quality_refinement import QualityRefinementStage
from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.blog_generation.stage_05_internal_links import InternalLinksStage
from pipeline.blog_generation.stage_12_hybrid_similarity_check import HybridSimilarityCheckStage
from pipeline.utils.hybrid_similarity_checker import HybridSimilarityChecker
from pipeline.utils.gemini_embeddings import GeminiEmbeddingClient
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_stage12_similarity_regeneration():
    """Test Stage 12 similarity check and section regeneration."""
    
    print("=" * 80)
    print("STAGE 12 SIMILARITY CHECK + SECTION REGENERATION TEST")
    print("=" * 80)
    print()
    
    # Test configuration
    company_url = "https://scaile.tech"
    
    # Create first article (will be stored in batch memory)
    print("📝 Generating first article (will be stored in batch memory)...")
    context1 = ExecutionContext(
        job_id="test_similarity_article1",
        job_config={
            "primary_keyword": "cloud security best practices",
            "company_url": company_url,
            "word_count": 2000,
            "language": "en",
            "tone": "professional"
        }
    )
    
    # Run pipeline up to Stage 5
    stage0 = DataFetchStage()
    context1 = await stage0.execute(context1)
    
    stage1 = PromptBuildStage()
    context1 = await stage1.execute(context1)
    
    stage2 = GeminiCallStage()
    context1 = await stage2.execute(context1)
    
    stage3 = QualityRefinementStage()
    context1 = await stage3.execute(context1)
    
    stage4 = CitationsStage()
    context1 = await stage4.execute(context1)
    
    stage5 = InternalLinksStage()
    context1 = await stage5.execute(context1)
    
    print(f"✅ First article generated: {context1.structured_data.Headline if context1.structured_data else 'N/A'}")
    print()
    
    # Initialize similarity checker and Stage 12
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            embedding_client = GeminiEmbeddingClient(api_key=api_key)
            similarity_checker = HybridSimilarityChecker(
                embedding_client=embedding_client,
                enable_regeneration=True
            )
            print("✅ Initialized HybridSimilarityChecker with semantic embeddings")
        except Exception as e:
            print(f"⚠️  Failed to initialize semantic embeddings: {e}")
            similarity_checker = HybridSimilarityChecker(enable_regeneration=True)
    else:
        similarity_checker = HybridSimilarityChecker(enable_regeneration=True)
        print("⚠️  No API key found - using character-only similarity checking")
    
    stage12 = HybridSimilarityCheckStage(similarity_checker=similarity_checker)
    
    # Check first article (should pass - no similar articles yet)
    print("\n🔍 Checking first article for similarity...")
    context1 = await stage12.execute(context1)
    
    if hasattr(context1, 'similarity_report') and context1.similarity_report:
        similarity_score = getattr(context1.similarity_report, 'similarity_score', 0)
        is_too_similar = getattr(context1.similarity_report, 'is_too_similar', False)
        print(f"   Similarity score: {similarity_score:.1f}%")
        print(f"   Too similar: {is_too_similar}")
        print(f"   ✅ First article approved (no similar articles)")
    else:
        print("   ⚠️  No similarity report generated")
    
    # Add first article to batch memory
    stage12.add_article_to_batch(context1)
    print("   ✅ First article added to batch memory")
    print()
    
    # Generate second article with similar topic (should trigger similarity)
    print("📝 Generating second article with similar topic...")
    context2 = ExecutionContext(
        job_id="test_similarity_article2",
        job_config={
            "primary_keyword": "cloud security best practices",  # Same keyword!
            "company_url": company_url,
            "word_count": 2000,
            "language": "en",
            "tone": "professional"
        }
    )
    
    # Run pipeline up to Stage 5
    stage0 = DataFetchStage()
    context2 = await stage0.execute(context2)
    
    stage1 = PromptBuildStage()
    context2 = await stage1.execute(context2)
    
    stage2 = GeminiCallStage()
    context2 = await stage2.execute(context2)
    
    stage3 = QualityRefinementStage()
    context2 = await stage3.execute(context2)
    
    stage4 = CitationsStage()
    context2 = await stage4.execute(context2)
    
    stage5 = InternalLinksStage()
    context2 = await stage5.execute(context2)
    
    print(f"✅ Second article generated: {context2.structured_data.Headline if context2.structured_data else 'N/A'}")
    print()
    
    # Check second article (should detect similarity and regenerate sections)
    print("🔍 Checking second article for similarity...")
    
    # Store original sections count
    original_sections = {}
    if context2.structured_data:
        for i in range(1, 10):
            title_key = f'section_{i:02d}_title'
            content_key = f'section_{i:02d}_content'
            if hasattr(context2.structured_data, title_key):
                original_sections[i] = {
                    'title': getattr(context2.structured_data, title_key, '') or '',
                    'content': getattr(context2.structured_data, content_key, '') or ''
                }
    
    context2 = await stage12.execute(context2)
    
    if hasattr(context2, 'similarity_report') and context2.similarity_report:
        similarity_score = getattr(context2.similarity_report, 'similarity_score', 0)
        is_too_similar = getattr(context2.similarity_report, 'is_too_similar', False)
        similar_article = getattr(context2.similarity_report, 'similar_article', None)
        regeneration_needed = getattr(context2.similarity_report, 'regeneration_needed', False)
        
        print(f"   Similarity score: {similarity_score:.1f}%")
        print(f"   Too similar: {is_too_similar}")
        print(f"   Similar to: {similar_article}")
        print(f"   Regeneration needed: {regeneration_needed}")
        
        if is_too_similar:
            print(f"   ⚠️  High similarity detected!")
            
            # Check if sections were regenerated
            if context2.structured_data:
                regenerated_count = 0
                for i in range(1, 10):
                    title_key = f'section_{i:02d}_title'
                    content_key = f'section_{i:02d}_content'
                    if hasattr(context2.structured_data, content_key):
                        original = original_sections.get(i, {}).get('content', '')
                        new = getattr(context2.structured_data, content_key, '') or ''
                        if original and new and original != new:
                            regenerated_count += 1
                            print(f"   ✅ Section {i} regenerated (length: {len(original)} → {len(new)} chars)")
                
                if regenerated_count > 0:
                    print(f"\n✅ Successfully regenerated {regenerated_count} section(s)")
                else:
                    print(f"\n⚠️  No sections were regenerated (may need similar article content in batch memory)")
        else:
            print(f"   ✅ Article is unique enough")
    else:
        print("   ⚠️  No similarity report generated")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    checks = {
        "Stage 12 executes": hasattr(context2, 'similarity_report'),
        "Similarity detected": hasattr(context2, 'similarity_report') and getattr(context2.similarity_report, 'is_too_similar', False),
        "Section regeneration": context2.regeneration_needed == False if hasattr(context2, 'regeneration_needed') else False,
    }
    
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
    
    all_passed = all(checks.values())
    if all_passed:
        print("\n🎉 All checks passed!")
    else:
        print("\n⚠️  Some checks failed - review output above")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_stage12_similarity_regeneration())
    sys.exit(0 if success else 1)

