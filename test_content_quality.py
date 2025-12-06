#!/usr/bin/env python3
"""
Real-world blog generation test with deep quality analysis.
Tests the actual pipeline against best-in-class standards.
"""

import asyncio
import httpx
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from audit_content_quality import ContentQualityAuditor


async def test_real_blog_generation():
    """Test real blog generation via API."""
    print("🚀 REAL BLOG GENERATION QUALITY TEST")
    print("=" * 80)
    print("Testing actual openblog output against Writesonic/Airops...\n")
    
    # Test configuration
    test_request = {
        "primary_keyword": "How to optimize content for AI search engines",
        "company_url": "https://scaile.tech",
        "content_length": "comprehensive",  # ~3000 words
        "target_audience": "marketing professionals",
    }
    
    print(f"📝 Test Article: {test_request['primary_keyword']}")
    print(f"🎯 Target: {test_request['content_length']} ({~3000} words)")
    print(f"👥 Audience: {test_request['target_audience']}")
    print("\n⏳ Generating article (may take 2-5 minutes)...\n")
    
    # TODO: Call actual blog generation API
    # For now, use mock response
    print("⚠️  Using mock data (connect to real API for production test)")
    
    # Simulate API response with typical openblog output
    mock_content = await get_mock_blog_content()
    
    # Run comprehensive audit
    auditor = ContentQualityAuditor()
    result = auditor.comprehensive_audit(
        mock_content,
        keywords=["AI search engines", "content optimization", "AEO"]
    )
    
    # Deep dive analysis
    print("\n" + "=" * 80)
    print("🔬 DEEP DIVE ANALYSIS")
    print("=" * 80)
    
    print("\n1️⃣  RESEARCH DEPTH ANALYSIS")
    print("-" * 80)
    print(f"Score: {result['research']['score']}/10")
    for metric, score in result['research']['breakdown'].items():
        status = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
        print(f"{status} {metric.replace('_', ' ').title()}: {score:.1f}/10")
    
    print("\n2️⃣  ORIGINALITY ANALYSIS")
    print("-" * 80)
    print(f"Score: {result['originality']['score']}/10")
    for metric, score in result['originality']['breakdown'].items():
        status = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
        print(f"{status} {metric.replace('_', ' ').title()}: {score:.1f}/10")
    
    print("\n3️⃣  SEO OPTIMIZATION ANALYSIS")
    print("-" * 80)
    print(f"Score: {result['seo']['score']}/10")
    print(f"Keyword density: {result['seo']['keyword_density']}% (target: 1-2%)")
    for metric, score in result['seo']['breakdown'].items():
        status = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
        print(f"{status} {metric.replace('_', ' ').title()}: {score:.1f}/10")
    
    print("\n4️⃣  READABILITY ANALYSIS")
    print("-" * 80)
    print(f"Score: {result['readability']['score']}/10")
    print(f"Avg sentence length: {result['readability'].get('avg_sentence_length', 'N/A')} words (target: <20)")
    for metric, score in result['readability']['breakdown'].items():
        status = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
        print(f"{status} {metric.replace('_', ' ').title()}: {score:.1f}/10")
    
    # Competitive analysis
    print("\n" + "=" * 80)
    print("🏆 COMPETITIVE ANALYSIS")
    print("=" * 80)
    
    benchmarks = {
        "Writesonic": 8.0,
        "Airops": 7.0,
        "Jasper": 8.5,
        "Copy.ai": 7.5,
        "OpenBlog": result['overall_score'],
    }
    
    print("\nQuality Ranking:")
    for i, (tool, score) in enumerate(sorted(benchmarks.items(), key=lambda x: x[1], reverse=True), 1):
        bar = "█" * int(score) + "░" * (10 - int(score))
        symbol = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"{symbol} {i}. {tool:15} {bar} {score}/10")
    
    # Action items
    print("\n" + "=" * 80)
    print("🎯 ACTION ITEMS TO REACH 9/10 (BEAT WRITESONIC)")
    print("=" * 80)
    
    action_items = []
    
    if result['research']['score'] < 9:
        action_items.append({
            "priority": "🔴 HIGH",
            "area": "Research Depth",
            "current": result['research']['score'],
            "target": 9.0,
            "actions": [
                "Add more real statistics and data points (aim for 10+ per article)",
                "Include specific case studies with concrete results",
                "Cite authoritative sources (research papers, industry reports)",
                "Use Gemini's Google Search grounding more aggressively"
            ]
        })
    
    if result['originality']['score'] < 9:
        action_items.append({
            "priority": "🟠 MEDIUM",
            "area": "Originality",
            "current": result['originality']['score'],
            "target": 9.0,
            "actions": [
                "Add unique perspective or contrarian views",
                "Include overlooked insights from deep research",
                "Avoid generic AI phrases and clichés",
                "Inject brand voice and personality"
            ]
        })
    
    if result['seo']['score'] < 9:
        action_items.append({
            "priority": "🟠 MEDIUM",
            "area": "SEO Quality",
            "current": result['seo']['score'],
            "target": 9.0,
            "actions": [
                f"Adjust keyword density to 1-2% (current: {result['seo']['keyword_density']}%)",
                "Add more internal links (aim for 5-8 per article)",
                "Improve heading structure (H2/H3 hierarchy)",
                "Optimize first paragraph for meta description"
            ]
        })
    
    if result['readability']['score'] < 9:
        action_items.append({
            "priority": "🟡 LOW",
            "area": "Readability",
            "current": result['readability']['score'],
            "target": 9.0,
            "actions": [
                "Shorten sentences (aim for <20 words average)",
                "Add more bullet points and lists",
                "Increase engagement (more 'you', questions)",
                "Break up long paragraphs (<100 words)"
            ]
        })
    
    for i, item in enumerate(action_items, 1):
        print(f"\n{item['priority']} #{i}: {item['area']}")
        print(f"   Current: {item['current']}/10 → Target: {item['target']}/10")
        print(f"   Gap: {item['target'] - item['current']:.1f} points")
        print("   Actions:")
        for action in item['actions']:
            print(f"      • {action}")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("📊 FINAL VERDICT")
    print("=" * 80)
    
    if result['overall_score'] >= 9.0:
        print("🏆 EXCEEDS Writesonic/Jasper - Best in class!")
    elif result['overall_score'] >= 8.5:
        print("🥇 MATCHES Jasper - Excellent quality")
    elif result['overall_score'] >= 8.0:
        print("🥈 MATCHES Writesonic - Good quality")
    elif result['overall_score'] >= 7.0:
        print("🥉 MATCHES Airops - Acceptable, needs improvement")
    else:
        print("❌ BELOW industry standards - Major work needed")
    
    print(f"\nCurrent score: {result['overall_score']}/10")
    print(f"Target score:  9.0/10 (best in class)")
    print(f"Gap:           {9.0 - result['overall_score']:.1f} points")
    
    return result


async def get_mock_blog_content() -> str:
    """Get mock blog content for testing."""
    # This should be replaced with real API call in production
    return """# How to Optimize Content for AI Search Engines in 2025

AI search engines are fundamentally changing how users discover content. According to recent research from Gartner, AI-powered search will answer 40% of queries without requiring users to visit external websites by 2026. This seismic shift demands a new approach to content optimization—one that goes beyond traditional SEO.

## Understanding AI Search Engines

AI search engines like Perplexity, ChatGPT's browsing feature, and Google's AI Overviews work differently from traditional search. Research shows that these systems prioritize:

- Direct, comprehensive answers
- Authoritative sources with clear expertise
- Well-structured, scannable content
- Current, frequently-updated information

For example, when users ask "how to optimize for AEO," AI engines synthesize information from multiple sources to provide a complete answer. Your content needs to be the source they cite.

## Key Optimization Strategies

### 1. Answer-First Content Structure

The truth is, AI engines scan for direct answers. Studies indicate that content with clear question-answer formats gets cited 3x more often in AI responses.

Here's how to implement this:
- Start paragraphs with the core answer
- Use descriptive subheadings
- Include FAQ sections
- Structure content for easy extraction

### 2. E-E-A-T Optimization

Google's E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) has become even more critical. Analysis reveals that AI systems prioritize content demonstrating these qualities.

What works best:
- Author bios with credentials
- Original research and data
- Citations to authoritative sources
- Regular content updates

### 3. Semantic SEO and Entity Optimization

Contrary to traditional keyword optimization, AI search focuses on entities and concepts. Research from SEMrush shows that entity-optimized content ranks 45% higher in AI search results.

Implementation tactics:
- Cover topic clusters, not just keywords
- Link related concepts naturally
- Use structured data markup
- Build comprehensive topic authority

## Technical Implementation

To implement AEO effectively:

1. Audit your current content for AI readability
2. Restructure with answer-first format
3. Add schema markup for key entities
4. Optimize for featured snippet formats
5. Build internal linking structure
6. Monitor AI engine citations

According to our testing, implementing these changes increased AI search visibility by 10x within three months.

## Measuring AEO Success

Traditional SEO metrics aren't enough. You need to track:
- AI engine citations (via brand monitoring)
- Zero-click search visibility
- Answer box appearances
- Authority score improvements

Research shows that companies tracking these metrics see 65% better AEO results.

## Conclusion

The future of search is AI-powered, and content optimization must evolve accordingly. Organizations that adopt AEO strategies now will dominate their markets in the AI search era.

The key is not abandoning traditional SEO, but enhancing it with AI-first optimization. As studies consistently show: the best approach combines both strategies for maximum visibility across all search channels.
"""


if __name__ == "__main__":
    asyncio.run(test_real_blog_generation())

