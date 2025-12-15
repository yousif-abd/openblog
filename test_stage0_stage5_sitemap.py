"""
Test Stage 0 (Sitemap Crawling) and Stage 5 (Internal Links Generation)
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
from pipeline.blog_generation.stage_05_internal_links import InternalLinksStage

async def test_stage0_stage5():
    """Test Stage 0 sitemap crawling and Stage 5 internal links generation."""
    print("=" * 80)
    print("STAGE 0 & STAGE 5 SITEMAP TEST")
    print("=" * 80)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/stage0_stage5_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test configuration
    company_url = "https://scaile.tech"  # Change this to your test company
    
    # Create execution context
    context = ExecutionContext(
        job_id="test_sitemap",
        job_config={
            "primary_keyword": "cloud security best practices",
            "company_url": company_url,
            "word_count": 2000,
            "language": "en",
            "tone": "professional"
        }
    )
    
    try:
        # ============================================================
        # STAGE 0: Data Fetch & Sitemap Crawling
        # ============================================================
        print("🔍 Stage 0: Data Fetch & Sitemap Crawling...")
        print(f"   Company URL: {company_url}")
        print()
        
        stage0 = DataFetchStage()
        context = await stage0.execute(context)
        
        if not context.sitemap_data:
            print("❌ Stage 0 failed - no sitemap_data found")
            return
        
        sitemap_data = context.sitemap_data
        print(f"✅ Stage 0 complete")
        print(f"   Total pages: {sitemap_data.get('total_pages', 0)}")
        print(f"   Blog pages: {sitemap_data.get('blog_count', 0)}")
        print()
        
        # Show breakdown
        page_summary = sitemap_data.get('page_summary', {})
        print("   Page breakdown:")
        for label, count in page_summary.items():
            print(f"      {label}: {count}")
        print()
        
        # Show sample URLs
        print("   Sample URLs:")
        blog_urls = sitemap_data.get('blog_urls', [])[:5]
        for url in blog_urls:
            print(f"      - {url}")
        print()
        
        # Save Stage 0 output
        with open(output_dir / "stage0_sitemap_data.json", "w") as f:
            json.dump({
                "total_pages": sitemap_data.get('total_pages', 0),
                "blog_count": sitemap_data.get('blog_count', 0),
                "page_summary": page_summary,
                "blog_urls": sitemap_data.get('blog_urls', [])[:20],
                "resource_urls": sitemap_data.get('resource_urls', [])[:10],
                "product_urls": sitemap_data.get('product_urls', [])[:10],
            }, f, indent=2)
        
        # ============================================================
        # STAGE 5: Internal Links Generation
        # ============================================================
        print("🔗 Stage 5: Internal Links Generation...")
        print()
        
        # Create mock structured_data for Stage 5 (it only needs headline and section titles)
        # Use a simple object that mimics ArticleOutput structure
        class MockArticle:
            def __init__(self):
                self.Headline = "Cloud Security Best Practices 2025"
                self.section_01_title = "Understanding Cloud Security Fundamentals"
                self.section_02_title = "Key Security Challenges in Cloud Environments"
                self.section_03_title = "Best Practices for Cloud Security"
                self.section_04_title = "Implementing Multi-Factor Authentication"
                self.section_05_title = "Data Encryption Strategies"
                self.section_06_title = "Compliance and Regulatory Requirements"
                self.section_07_title = None
                self.section_08_title = None
                self.section_09_title = None
        
        context.structured_data = MockArticle()
        
        stage5 = InternalLinksStage()
        context = await stage5.execute(context)
        
        internal_links_html = context.parallel_results.get("internal_links_html", "")
        internal_links_count = context.parallel_results.get("internal_links_count", 0)
        internal_links_list = context.parallel_results.get("internal_links_list")
        section_internal_links = context.parallel_results.get("section_internal_links", {})
        
        print(f"✅ Stage 5 complete")
        print(f"   Internal links generated: {internal_links_count}")
        print(f"   HTML size: {len(internal_links_html)} chars")
        print()
        
        # Create reverse mapping: URL -> section number
        url_to_section = {}
        if section_internal_links:
            for section_num, links in section_internal_links.items():
                for link in links:
                    url_to_section[link.get('url', '')] = section_num
        
        # Show generated links with section assignments
        if internal_links_list and hasattr(internal_links_list, 'links'):
            print("   Generated links:")
            for i, link in enumerate(internal_links_list.links[:10], 1):
                section_num = url_to_section.get(link.url, None)
                section_info = f" → Section {section_num}" if section_num else " → (not assigned to section)"
                print(f"      {i}. {link.title}")
                print(f"         URL: {link.url}")
                print(f"         Relevance: {link.relevance}/10{section_info}")
                print()
        
        # Show section assignments
        if section_internal_links:
            print("   Section link assignments:")
            for section_num, links in section_internal_links.items():
                if links:
                    print(f"      Section {section_num}: {len(links)} link(s)")
                    for link in links:
                        print(f"         - {link.get('title', 'N/A')} → {link.get('url', 'N/A')}")
            print()
        
        # Save Stage 5 output
        with open(output_dir / "stage5_internal_links.json", "w") as f:
            json.dump({
                "internal_links_count": internal_links_count,
                "html_size": len(internal_links_html),
                "html_preview": internal_links_html[:500] + "..." if len(internal_links_html) > 500 else internal_links_html,
                "links": [
                    {
                        "title": link.title,
                        "url": link.url,
                        "relevance": link.relevance,
                        "assigned_section": url_to_section.get(link.url, None)
                    }
                    for link in (internal_links_list.links[:10] if internal_links_list and hasattr(internal_links_list, 'links') else [])
                ],
                "section_assignments": section_internal_links
            }, f, indent=2)
        
        # Save HTML output
        if internal_links_html:
            with open(output_dir / "stage5_internal_links.html", "w") as f:
                f.write(internal_links_html)
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Stage 0: Sitemap crawled ({sitemap_data.get('total_pages', 0)} pages)")
        print(f"   - Blog pages: {sitemap_data.get('blog_count', 0)}")
        print(f"   - Page types: {len(page_summary)}")
        print()
        print(f"✅ Stage 5: Internal links generated ({internal_links_count} links)")
        print(f"   - HTML formatted: {len(internal_links_html)} chars")
        print(f"   - Sections with links: {len([s for s in section_internal_links.values() if s])}")
        print()
        print(f"📁 Output saved to: {output_dir}")
        print()
        print("✅ STAGE 0 & STAGE 5 TEST PASSED")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    asyncio.run(test_stage0_stage5())

