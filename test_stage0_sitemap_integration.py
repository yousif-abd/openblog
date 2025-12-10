#!/usr/bin/env python3
"""
Test script for Stage 0 sitemap integration.

Tests the enhanced Stage 0 with sitemap crawling capabilities.
"""

import asyncio
import logging
from pipeline.blog_generation.stage_00_data_fetch import DataFetchStage
from pipeline.core.execution_context import ExecutionContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_stage0_sitemap_integration():
    """Test Stage 0 with sitemap integration."""
    
    # Test cases with different company URLs
    test_cases = [
        {
            "name": "Stripe - Content-heavy site",
            "job_config": {
                "primary_keyword": "payment processing API",
                "company_url": "https://stripe.com",
            }
        },
        {
            "name": "Anthropic - AI company",
            "job_config": {
                "primary_keyword": "large language models",
                "company_url": "https://anthropic.com",
            }
        },
        {
            "name": "No sitemap - fallback test",
            "job_config": {
                "primary_keyword": "test keyword",
                "company_url": "https://example.com",
            }
        },
    ]
    
    stage = DataFetchStage()
    
    for test_case in test_cases:
        logger.info(f"\n🧪 Testing: {test_case['name']}")
        
        try:
            # Create execution context
            context = ExecutionContext(
                job_id=f"test-{test_case['name'].lower().replace(' ', '-')}",
                job_config=test_case['job_config']
            )
            
            # Execute Stage 0
            result_context = await stage.execute(context)
            
            # Display results
            logger.info(f"✅ Stage 0 Results for {test_case['name']}:")
            logger.info(f"   Company: {result_context.company_data.get('company_name', 'Unknown')}")
            logger.info(f"   Language: {result_context.language}")
            
            # Sitemap analysis
            if hasattr(result_context, 'sitemap_data') and result_context.sitemap_data:
                sitemap = result_context.sitemap_data
                logger.info(f"   📊 Sitemap Analysis:")
                logger.info(f"      Total pages: {sitemap.get('total_pages', 0)}")
                logger.info(f"      Blog pages: {sitemap.get('blog_count', 0)}")
                logger.info(f"      Site type: {sitemap.get('site_structure', {}).get('site_type', 'unknown')}")
                logger.info(f"      Content volume: {sitemap.get('site_structure', {}).get('content_volume', 'unknown')}")
                
                # Sample blog URLs
                blog_urls = sitemap.get('blog_urls', [])
                if blog_urls:
                    logger.info(f"   📝 Sample blog URLs:")
                    for url in blog_urls[:3]:
                        logger.info(f"      - {url}")
            else:
                logger.info(f"   ⚠️ No sitemap data found")
            
            # Internal links 
            blog_page = result_context.blog_page
            links = blog_page.get('links', '')
            if links:
                logger.info(f"   🔗 Internal links generated: {len(links.split('\\n'))} links")
                # Show first 2 links
                link_lines = links.split('\n')[:2]
                for link in link_lines:
                    logger.info(f"      {link}")
            else:
                logger.info(f"   ⚠️ No internal links generated")
                
        except Exception as e:
            logger.error(f"❌ Error testing {test_case['name']}: {e}")
        
        await asyncio.sleep(2)  # Be nice to servers


async def test_sitemap_link_formatting():
    """Test the link formatting functions."""
    
    logger.info(f"\n🔗 Testing Link Formatting:")
    
    stage = DataFetchStage()
    
    # Test sitemap link formatting
    blog_urls = [
        "https://stripe.com/blog/payment-processing-trends",
        "https://stripe.com/blog/api-best-practices", 
        "https://stripe.com/blog/fintech-innovation-2024"
    ]
    
    formatted_sitemap_links = stage._format_sitemap_links(blog_urls)
    logger.info(f"✅ Sitemap link formatting:")
    for line in formatted_sitemap_links.split('\\n'):
        logger.info(f"   {line}")
    
    # Test legacy link formatting
    legacy_urls = [
        "/blog/payment-processing",
        "/resources/api-guide",
        "/documentation/webhooks"
    ]
    
    formatted_legacy_links = stage._format_legacy_links(legacy_urls)
    logger.info(f"\\n✅ Legacy link formatting:")
    for line in formatted_legacy_links.split('\\n'):
        logger.info(f"   {line}")


async def main():
    """Run all tests."""
    logger.info("🚀 Testing Stage 0 Sitemap Integration")
    
    await test_sitemap_link_formatting()
    await test_stage0_sitemap_integration()
    
    logger.info("✅ All Stage 0 sitemap integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())