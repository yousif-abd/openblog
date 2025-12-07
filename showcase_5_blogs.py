"""
Generate 5 showcase blogs to test the full pipeline
Uses the same pattern as service/api.py
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

from pipeline.core import WorkflowEngine

# Import all stages
from pipeline.blog_generation.stage_00_data_fetch import DataFetchStage
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
from pipeline.blog_generation.stage_03_extraction import ExtractionStage
from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.blog_generation.stage_05_internal_links import InternalLinksStage
from pipeline.blog_generation.stage_06_toc import TableOfContentsStage
from pipeline.blog_generation.stage_07_metadata import MetadataStage
from pipeline.blog_generation.stage_08_faq_paa import FAQPAAStage
from pipeline.blog_generation.stage_09_image import ImageStage
from pipeline.blog_generation.stage_10_cleanup import CleanupStage
from pipeline.blog_generation.stage_12_review_iteration import ReviewIterationStage
from pipeline.blog_generation.stage_11_storage import StorageStage

# 5 diverse keywords to showcase different types of content
SHOWCASE_KEYWORDS = [
    "AI code review tools 2025",
    "microservices architecture best practices",
    "cybersecurity trends enterprises",
    "cloud cost optimization strategies",
    "API design patterns REST GraphQL"
]

def create_engine() -> WorkflowEngine:
    """Create and register all stages."""
    engine = WorkflowEngine()
    engine.register_stages([
        DataFetchStage(),
        PromptBuildStage(),
        GeminiCallStage(),
        ExtractionStage(),
        CitationsStage(),
        InternalLinksStage(),
        TableOfContentsStage(),
        MetadataStage(),
        FAQPAAStage(),
        ImageStage(),
        CleanupStage(),
        ReviewIterationStage(),
        StorageStage(),
    ])
    return engine

async def generate_showcase_blog(keyword: str, index: int):
    """Generate a single blog for showcase."""
    print(f"\n{'='*60}")
    print(f"[{index+1}/5] Generating: {keyword}")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    job_id = f"showcase-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{index}"
    
    # Build job config
    job_config = {
        "primary_keyword": keyword,
        "company_url": "https://techinsights.ai",
        "company_name": "TechInsights",
        "language": "en",
        "country": "US",
        "word_count": 1500,
        "tone": "professional",
        "index": True,
        "company_data": {
            "description": "Leading technology insights and analysis platform",
            "industry": "Technology & Software",
            "target_audience": ["CTOs", "Tech Leaders", "Developers"],
        },
    }
    
    try:
        # Verify API key
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            raise Exception("GOOGLE_API_KEY or GEMINI_API_KEY not configured")
        
        # Set GEMINI_API_KEY for the stages to use
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Create engine for this job
        engine = create_engine()
        
        # Execute workflow
        context = await engine.execute(job_id=job_id, job_config=job_config)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Extract results
        sd = context.structured_data
        article_data = sd.model_dump() if hasattr(sd, 'model_dump') else {}
        
        print(f"\n✅ [{index+1}/5] COMPLETED: {keyword}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Headline: {article_data.get('Headline', 'N/A')[:80]}...")
        print(f"   Word count: {article_data.get('word_count', 0)}")
        
        # Count sections
        sections = [k for k in article_data.keys() if k.startswith('section_') and k.endswith('_title')]
        print(f"   Sections: {len(sections)}")
        print(f"   FAQs: {len(article_data.get('faq_questions', []))}")
        print(f"   Images: {len(article_data.get('images', []))}")
        
        # Check for issues in HTML
        html_content = context.html_content or ""
        issues = []
        
        if 'You can aI' in html_content:
            issues.append("❌ Hallucination detected")
        if '[1]' in html_content or '[2]' in html_content:
            issues.append("⚠️  Academic citations found")
        if '—' in html_content or '&mdash;' in html_content:
            issues.append("⚠️  Em dashes found")
        if '<p><strong>Essential' in html_content or '<p><strong>Key' in html_content:
            issues.append("⚠️  Standalone labels found")
        
        if issues:
            print(f"   Issues: {', '.join(issues)}")
        else:
            print(f"   ✨ Quality: EXCELLENT (no hallucinations, em dashes, or academic citations)")
        
        return {
            'keyword': keyword,
            'success': True,
            'duration': duration,
            'headline': article_data.get('Headline', ''),
            'slug': context.slug or '',
            'issues': issues,
            'word_count': article_data.get('word_count', 0),
            'sections': len(sections)
        }
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        print(f"\n❌ [{index+1}/5] FAILED: {keyword}")
        print(f"   Error: {str(e)[:150]}")
        import traceback
        traceback.print_exc()
        
        return {
            'keyword': keyword,
            'success': False,
            'duration': duration,
            'error': str(e)
        }


async def main():
    """Run showcase generation."""
    print("\n" + "="*60)
    print("BLOG GENERATION SHOWCASE - 5 ARTICLES")
    print("="*60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    overall_start = datetime.now()
    
    # Generate all 5 blogs in parallel
    print("\n🚀 Starting parallel generation of 5 blogs...")
    tasks = [
        generate_showcase_blog(keyword, i) 
        for i, keyword in enumerate(SHOWCASE_KEYWORDS)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    overall_duration = (datetime.now() - overall_start).total_seconds()
    
    # Summary
    print("\n" + "="*60)
    print("SHOWCASE SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
    failed = len(results) - successful
    
    print(f"\n📊 Results: {successful}/{len(results)} successful")
    print(f"⏱️  Total time: {overall_duration/60:.1f} minutes ({overall_duration:.1f}s)")
    if successful > 0:
        print(f"⚡ Avg time per blog: {overall_duration/len(results)/60:.1f} minutes")
    
    if successful > 0:
        print(f"\n📝 Generated Articles:")
        total_issues = 0
        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get('success'):
                issues_count = len(result.get('issues', []))
                total_issues += issues_count
                print(f"\n   {i+1}. {result['keyword']}")
                print(f"      → {result['headline'][:70]}...")
                print(f"      → Duration: {result['duration']:.1f}s")
                print(f"      → {result['word_count']} words | {result['sections']} sections")
                print(f"      → Quality: {'✅ EXCELLENT' if issues_count == 0 else f'⚠️  {issues_count} issues'}")
                if result.get('issues'):
                    for issue in result['issues']:
                        print(f"         {issue}")
        
        print(f"\n✨ Overall Quality Score: {successful - total_issues}/{successful} articles with no issues")
    
    if failed > 0:
        print(f"\n❌ Failed: {failed}")
        for i, result in enumerate(results):
            if isinstance(result, dict) and not result.get('success'):
                print(f"   {i+1}. {result['keyword']}")
                print(f"      → {result.get('error', 'Unknown error')[:120]}")
    
    print("\n" + "="*60)
    print(f"Showcase generation complete at {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
