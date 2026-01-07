"""
Stage 1 Tests - Unit tests and integration test for Stage 1: Set Context

Tests cover:
1. stage1_models.py - Data models, slug generation, input/output validation
2. sitemap_crawler.py - URL classification patterns
3. opencontext.py - Basic detection fallback (no API key)
4. Integration test - Full Stage 1 run with real company (hypofriend.de)

Run: python test_stage1.py
Run integration only: python test_stage1.py --integration
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent to path for shared imports
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from dotenv import load_dotenv

load_dotenv(_parent / ".env")

# Test results tracking
PASSED = 0
FAILED = 0
ERRORS = []

# Check for integration-only mode
RUN_INTEGRATION_ONLY = "--integration" in sys.argv


def test(name: str):
    """Decorator for test functions."""

    def decorator(func):
        def wrapper():
            global PASSED, FAILED, ERRORS
            try:
                func()
                PASSED += 1
                print(f"  [PASS] {name}")
            except AssertionError as e:
                FAILED += 1
                ERRORS.append(f"{name}: {e}")
                print(f"  [FAIL] {name}: {e}")
            except Exception as e:
                FAILED += 1
                ERRORS.append(f"{name}: {type(e).__name__}: {e}")
                print(f"  [ERROR] {name}: {type(e).__name__}: {e}")

        return wrapper

    return decorator


# =============================================================================
# Skip unit tests if running integration only
# =============================================================================

if not RUN_INTEGRATION_ONLY:

    # =============================================================================
    # Slug Generation Tests (stage1_models.py)
    # =============================================================================

    print("\n=== Testing generate_slug ===")

    from stage1_models import generate_slug

    @test("Slug: basic keyword")
    def test_slug_basic():
        result = generate_slug("AI Sales Automation")
        assert result == "ai-sales-automation", f"Got: {result}"

    test_slug_basic()

    @test("Slug: handles special characters")
    def test_slug_special_chars():
        result = generate_slug("What's the Best CRM?")
        assert result == "whats-the-best-crm", f"Got: {result}"

    test_slug_special_chars()

    @test("Slug: handles multiple spaces")
    def test_slug_multiple_spaces():
        result = generate_slug("AI   powered   tools")
        assert result == "ai-powered-tools", f"Got: {result}"

    test_slug_multiple_spaces()

    @test("Slug: handles underscores")
    def test_slug_underscores():
        result = generate_slug("sales_automation_guide")
        assert result == "sales-automation-guide", f"Got: {result}"

    test_slug_underscores()

    @test("Slug: handles leading/trailing hyphens")
    def test_slug_leading_trailing():
        result = generate_slug("  -AI Tools-  ")
        assert result == "ai-tools", f"Got: {result}"

    test_slug_leading_trailing()

    @test("Slug: empty keyword returns 'article'")
    def test_slug_empty():
        result = generate_slug("")
        assert result == "article", f"Got: {result}"

    test_slug_empty()

    @test("Slug: None keyword returns 'article'")
    def test_slug_none():
        result = generate_slug(None)
        assert result == "article", f"Got: {result}"

    test_slug_none()

    @test("Slug: only special chars returns 'article'")
    def test_slug_only_special():
        result = generate_slug("!!!")
        assert result == "article", f"Got: {result}"

    test_slug_only_special()

    @test("Slug: truncates at max_length")
    def test_slug_max_length():
        long_keyword = (
            "This is a very long keyword that should be truncated at a word boundary"
        )
        result = generate_slug(long_keyword, max_length=30)
        assert len(result) <= 30, f"Got length {len(result)}: {result}"
        # Should truncate at word boundary
        assert not result.endswith("-"), f"Should not end with hyphen: {result}"

    test_slug_max_length()

    @test("Slug: preserves numbers")
    def test_slug_numbers():
        result = generate_slug("Top 10 AI Tools 2024")
        assert result == "top-10-ai-tools-2024", f"Got: {result}"

    test_slug_numbers()

    # =============================================================================
    # URL Classification Tests (sitemap_crawler.py)
    # =============================================================================

    print("\n=== Testing URL Classification ===")

    from sitemap_crawler import classify_url

    @test("Classify: blog URL")
    def test_classify_blog():
        assert classify_url("https://example.com/blog/post-1") == "blog"
        assert classify_url("https://example.com/news/update") == "blog"
        assert classify_url("https://example.com/articles/guide") == "blog"
        assert classify_url("https://example.com/insights/2024") == "blog"

    test_classify_blog()

    @test("Classify: product URL")
    def test_classify_product():
        assert classify_url("https://example.com/products/ai-tool") == "product"
        assert classify_url("https://example.com/solutions/enterprise") == "product"
        assert classify_url("https://example.com/pricing") == "product"
        assert classify_url("https://example.com/features") == "product"

    test_classify_product()

    @test("Classify: service URL")
    def test_classify_service():
        assert classify_url("https://example.com/services/consulting") == "service"
        assert classify_url("https://example.com/consulting") == "service"

    test_classify_service()

    @test("Classify: docs URL")
    def test_classify_docs():
        assert classify_url("https://example.com/docs/api") == "docs"
        assert classify_url("https://example.com/documentation") == "docs"
        assert classify_url("https://example.com/help/getting-started") == "docs"
        assert classify_url("https://example.com/faq") == "docs"

    test_classify_docs()

    @test("Classify: resource URL")
    def test_classify_resource():
        assert classify_url("https://example.com/resources/whitepaper") == "resource"
        assert classify_url("https://example.com/case-studies/client") == "resource"
        assert classify_url("https://example.com/webinars") == "resource"
        assert classify_url("https://example.com/ebooks/guide") == "resource"

    test_classify_resource()

    @test("Classify: other URL")
    def test_classify_other():
        assert classify_url("https://example.com/") == "other"
        assert classify_url("https://example.com/random-page") == "other"

    test_classify_other()

    @test("Classify: case insensitive")
    def test_classify_case_insensitive():
        assert classify_url("https://example.com/BLOG/post") == "blog"
        assert classify_url("https://example.com/Products/item") == "product"

    test_classify_case_insensitive()

    # =============================================================================
    # Stage1Input Model Tests
    # =============================================================================

    print("\n=== Testing Stage1Input ===")

    from stage1_models import Stage1Input, KeywordConfig, CompanyContext

    @test("Stage1Input: simple string keywords")
    def test_input_simple_keywords():
        input_data = Stage1Input(
            keywords=["keyword 1", "keyword 2"], company_url="https://example.com"
        )
        configs = input_data.get_keyword_configs()
        assert len(configs) == 2
        assert configs[0].keyword == "keyword 1"
        assert configs[1].keyword == "keyword 2"
        assert configs[0].word_count == 2000  # default

    test_input_simple_keywords()

    @test("Stage1Input: dict keywords with overrides")
    def test_input_dict_keywords():
        input_data = Stage1Input(
            keywords=[
                {"keyword": "topic 1", "word_count": 1500},
                {"keyword": "topic 2", "word_count": 3000},
            ],
            company_url="https://example.com",
        )
        configs = input_data.get_keyword_configs()
        assert len(configs) == 2
        assert configs[0].word_count == 1500
        assert configs[1].word_count == 3000

    test_input_dict_keywords()

    @test("Stage1Input: mixed keywords (strings and dicts)")
    def test_input_mixed_keywords():
        input_data = Stage1Input(
            keywords=[
                "simple keyword",
                {"keyword": "custom keyword", "word_count": 2500},
            ],
            company_url="https://example.com",
        )
        configs = input_data.get_keyword_configs()
        assert len(configs) == 2
        assert configs[0].keyword == "simple keyword"
        assert configs[0].word_count == 2000  # uses default
        assert configs[1].keyword == "custom keyword"
        assert configs[1].word_count == 2500

    test_input_mixed_keywords()

    @test("Stage1Input: batch instructions applied to all")
    def test_input_batch_instructions():
        input_data = Stage1Input(
            keywords=["kw1", "kw2"],
            company_url="https://example.com",
            batch_instructions="Write in formal tone",
        )
        configs = input_data.get_keyword_configs()
        assert configs[0].instructions == "Write in formal tone"
        assert configs[1].instructions == "Write in formal tone"

    test_input_batch_instructions()

    @test("Stage1Input: combined batch + keyword instructions")
    def test_input_combined_instructions():
        input_data = Stage1Input(
            keywords=[
                {"keyword": "topic", "keyword_instructions": "Focus on enterprise"}
            ],
            company_url="https://example.com",
            batch_instructions="Write in formal tone",
        )
        configs = input_data.get_keyword_configs()
        assert "formal tone" in configs[0].instructions
        assert "enterprise" in configs[0].instructions
        assert "Additional" in configs[0].instructions

    test_input_combined_instructions()

    @test("Stage1Input: normalizes URL without http")
    def test_input_url_normalization():
        input_data = Stage1Input(keywords=["test"], company_url="example.com")
        assert input_data.company_url == "https://example.com"

    test_input_url_normalization()

    @test("Stage1Input: preserves URL with http")
    def test_input_url_with_http():
        input_data = Stage1Input(keywords=["test"], company_url="http://example.com")
        assert input_data.company_url == "http://example.com"

    test_input_url_with_http()

    @test("Stage1Input: custom default_word_count")
    def test_input_custom_default_word_count():
        input_data = Stage1Input(
            keywords=["kw1", "kw2"],
            company_url="https://example.com",
            default_word_count=3000,
        )
        configs = input_data.get_keyword_configs()
        assert configs[0].word_count == 3000
        assert configs[1].word_count == 3000

    test_input_custom_default_word_count()

    # =============================================================================
    # Stage1Output Model Tests
    # =============================================================================

    print("\n=== Testing Stage1Output ===")

    from stage1_models import Stage1Output, ArticleJob, SitemapData

    @test("Stage1Output: generates job_id")
    def test_output_job_id():
        output = Stage1Output(
            articles=[ArticleJob(keyword="test", slug="test", href="/magazine/test")],
            language="en",
            market="US",
            company_context=CompanyContext(company_name="Test Co"),
        )
        assert output.job_id  # Should be auto-generated
        assert len(output.job_id) == 36  # UUID format

    test_output_job_id()

    @test("Stage1Output: generates created_at")
    def test_output_created_at():
        output = Stage1Output(
            articles=[ArticleJob(keyword="test", slug="test", href="/magazine/test")],
            language="en",
            market="US",
            company_context=CompanyContext(company_name="Test Co"),
        )
        assert output.created_at  # Should be auto-generated
        assert "T" in output.created_at  # ISO format

    test_output_created_at()

    # =============================================================================
    # CompanyContext Tests
    # =============================================================================

    print("\n=== Testing CompanyContext ===")

    from stage1_models import VoicePersona, VisualIdentity, AuthorInfo

    @test("CompanyContext: from_dict handles empty dict")
    def test_context_empty_dict():
        ctx = CompanyContext.from_dict({})
        assert ctx.company_name == ""
        assert ctx.tone == "professional"  # default

    test_context_empty_dict()

    @test("CompanyContext: from_dict handles None")
    def test_context_none():
        ctx = CompanyContext.from_dict(None)
        assert ctx.company_name == ""

    test_context_none()

    @test("CompanyContext: from_dict parses nested voice_persona")
    def test_context_voice_persona():
        data = {
            "company_name": "Test Co",
            "voice_persona": {
                "icp_profile": "B2B SaaS buyers",
                "voice_style": "Professional and friendly",
                "language_style": {"formality": "formal", "complexity": "technical"},
            },
        }
        ctx = CompanyContext.from_dict(data)
        assert ctx.voice_persona.icp_profile == "B2B SaaS buyers"
        assert ctx.voice_persona.language_style.formality == "formal"

    test_context_voice_persona()

    @test("CompanyContext: from_dict parses nested visual_identity")
    def test_context_visual_identity():
        data = {
            "company_name": "Test Co",
            "visual_identity": {
                "brand_colors": ["#FF5733", "#333333"],
                "visual_style": "minimalist",
                "blog_image_examples": [
                    {"url": "https://example.com/img.jpg", "description": "Hero image"}
                ],
            },
        }
        ctx = CompanyContext.from_dict(data)
        assert len(ctx.visual_identity.brand_colors) == 2
        assert ctx.visual_identity.visual_style == "minimalist"
        assert len(ctx.visual_identity.blog_image_examples) == 1

    test_context_visual_identity()

    @test("CompanyContext: from_dict parses authors")
    def test_context_authors():
        data = {
            "company_name": "Test Co",
            "authors": [
                {"name": "John Doe", "title": "CEO"},
                {"name": "Jane Smith", "title": None},  # None should become ""
            ],
        }
        ctx = CompanyContext.from_dict(data)
        assert len(ctx.authors) == 2
        assert ctx.authors[0].name == "John Doe"
        assert ctx.authors[0].title == "CEO"
        assert ctx.authors[1].title == ""  # None converted to empty string

    test_context_authors()

    @test("CompanyContext: from_dict skips authors without name")
    def test_context_authors_no_name():
        data = {
            "company_name": "Test Co",
            "authors": [
                {"name": "Valid Author", "title": "Writer"},
                {"title": "No Name"},  # Should be skipped
            ],
        }
        ctx = CompanyContext.from_dict(data)
        assert len(ctx.authors) == 1
        assert ctx.authors[0].name == "Valid Author"

    test_context_authors_no_name()

    # =============================================================================
    # ArticleJob Tests
    # =============================================================================

    print("\n=== Testing ArticleJob ===")

    @test("ArticleJob: creates valid job")
    def test_article_job_valid():
        job = ArticleJob(keyword="AI Sales", slug="ai-sales", href="/magazine/ai-sales")
        assert job.keyword == "AI Sales"
        assert job.slug == "ai-sales"
        assert job.href == "/magazine/ai-sales"
        assert job.word_count is None  # optional

    test_article_job_valid()

    @test("ArticleJob: with word_count override")
    def test_article_job_word_count():
        job = ArticleJob(
            keyword="AI Sales",
            slug="ai-sales",
            href="/magazine/ai-sales",
            word_count=3000,
        )
        assert job.word_count == 3000

    test_article_job_word_count()

    @test("ArticleJob: with keyword_instructions")
    def test_article_job_instructions():
        job = ArticleJob(
            keyword="AI Sales",
            slug="ai-sales",
            href="/magazine/ai-sales",
            keyword_instructions="Focus on enterprise use cases",
        )
        assert job.keyword_instructions == "Focus on enterprise use cases"

    test_article_job_instructions()

    # =============================================================================
    # SitemapData Tests
    # =============================================================================

    print("\n=== Testing SitemapData ===")

    @test("SitemapData: default empty values")
    def test_sitemap_data_empty():
        data = SitemapData()
        assert data.total_pages == 0
        assert data.blog_urls == []
        assert data.product_urls == []

    test_sitemap_data_empty()

    @test("SitemapData: with values")
    def test_sitemap_data_values():
        data = SitemapData(
            total_pages=100,
            blog_urls=["https://example.com/blog/1"],
            product_urls=["https://example.com/products/a"],
        )
        assert data.total_pages == 100
        assert len(data.blog_urls) == 1
        assert len(data.product_urls) == 1

    test_sitemap_data_values()

    # =============================================================================
    # OpenContext Basic Detection Tests
    # =============================================================================

    print("\n=== Testing OpenContext Basic Detection ===")

    from opencontext import basic_company_detection

    @test("Basic detection: extracts company name from domain")
    def test_basic_detection_domain():
        ctx = basic_company_detection("https://acme-corp.com")
        assert ctx.company_name == "Acme Corp"
        assert ctx.company_url == "https://acme-corp.com"

    test_basic_detection_domain()

    @test("Basic detection: handles www prefix")
    def test_basic_detection_www():
        ctx = basic_company_detection("https://www.example.com")
        assert ctx.company_name == "Example"

    test_basic_detection_www()

    @test("Basic detection: normalizes URL without http")
    def test_basic_detection_no_http():
        ctx = basic_company_detection("example.com")
        assert ctx.company_url == "https://example.com"

    test_basic_detection_no_http()

    @test("Basic detection: returns professional tone")
    def test_basic_detection_tone():
        ctx = basic_company_detection("https://example.com")
        assert ctx.tone == "professional"

    test_basic_detection_tone()

    # =============================================================================
    # SitemapCrawler URL Validation Tests
    # =============================================================================

    print("\n=== Testing SitemapCrawler URL Validation ===")

    from sitemap_crawler import SitemapCrawler

    @test("Crawler: rejects javascript: URLs")
    def test_crawler_reject_javascript():
        crawler = SitemapCrawler()
        assert crawler._is_valid_url("javascript:alert(1)") == False

    test_crawler_reject_javascript()

    @test("Crawler: rejects file: URLs")
    def test_crawler_reject_file():
        crawler = SitemapCrawler()
        assert crawler._is_valid_url("file:///etc/passwd") == False

    test_crawler_reject_file()

    @test("Crawler: rejects data: URLs")
    def test_crawler_reject_data():
        crawler = SitemapCrawler()
        assert crawler._is_valid_url("data:text/html,<script>") == False

    test_crawler_reject_data()

    @test("Crawler: accepts https URLs")
    def test_crawler_accept_https():
        crawler = SitemapCrawler()
        assert crawler._is_valid_url("https://example.com/page") == True

    test_crawler_accept_https()

    @test("Crawler: accepts http URLs")
    def test_crawler_accept_http():
        crawler = SitemapCrawler()
        assert crawler._is_valid_url("http://example.com/page") == True

    test_crawler_accept_http()

    @test("Crawler: rejects empty URL")
    def test_crawler_reject_empty():
        crawler = SitemapCrawler()
        assert crawler._is_valid_url("") == False
        assert crawler._is_valid_url(None) == False

    test_crawler_reject_empty()

    @test("Crawler: rejects URL without host")
    def test_crawler_reject_no_host():
        crawler = SitemapCrawler()
        assert crawler._is_valid_url("https://") == False

    test_crawler_reject_no_host()


# =============================================================================
# Integration Test - Full Stage 1 with hypofriend.de
# =============================================================================

print("\n=== Integration Test: Full Stage 1 (hypofriend.de) ===")

from stage1_models import Stage1Input
from stage_1 import run_stage_1


async def run_integration_test():
    """
    Run Stage 1 exactly as the main pipeline does.

    This mirrors the exact input format from run_pipeline.py:
        input_data = Stage1Input(
            keywords=keywords,
            company_url=company_url,
            language=language,
            market=market,
        )
        context = await run_stage_1(input_data)
    """
    global PASSED, FAILED, ERRORS

    # Exact input as used by run_pipeline.py
    input_data = Stage1Input(
        keywords=[
            "Baufinanzierung Vergleich alle Plattformen",
            "Hypothekenzinsen vergleichen 750 Banken",
            "Europace eHyp Baufinex beste Konditionen",
        ],
        company_url="https://www.hypofriend.de/",
        language="de",
        market="DE",
    )

    print(f"\n  Input:")
    print(f"    Company URL: {input_data.company_url}")
    print(f"    Keywords: {input_data.keywords}")
    print(f"    Language: {input_data.language}")
    print(f"    Market: {input_data.market}")
    print()

    try:
        # Run Stage 1 (this is the actual test)
        context = await run_stage_1(input_data)

        # Validate output structure
        print(f"\n  Output:")
        print(f"    Job ID: {context.job_id}")
        print(f"    Company: {context.company_context.company_name}")
        print(f"    Industry: {context.company_context.industry}")
        print(f"    Articles: {len(context.articles)}")
        for article in context.articles:
            print(f"      - {article.keyword} -> {article.href}")
        print(f"    Sitemap: {context.sitemap.total_pages} pages")
        print(f"      Blog URLs: {len(context.sitemap.blog_urls)}")
        print(f"      Product URLs: {len(context.sitemap.product_urls)}")
        print(f"      Resource URLs: {len(context.sitemap.resource_urls)}")
        print(f"    OpenContext called: {context.opencontext_called}")
        print(f"    AI calls: {context.ai_calls}")

        # Assertions
        assert context.job_id, "job_id should be generated"
        assert (
            len(context.articles) == 3
        ), f"Expected 3 articles, got {len(context.articles)}"
        assert (
            context.language == "de"
        ), f"Expected language 'de', got {context.language}"
        assert context.market == "DE", f"Expected market 'DE', got {context.market}"

        # Check article slugs are generated (non-empty, URL-safe)
        for i, article in enumerate(context.articles):
            assert article.slug, f"Article {i} slug should not be empty"
            assert (
                " " not in article.slug
            ), f"Article {i} slug should not contain spaces: {article.slug}"
            assert (
                article.slug.islower() or article.slug.replace("-", "").isalnum()
            ), f"Article {i} slug should be lowercase: {article.slug}"
            print(f"    Slug {i}: '{input_data.keywords[i]}' -> '{article.slug}'")

        # Check hrefs
        for article in context.articles:
            assert article.href.startswith(
                "/magazine/"
            ), f"href should start with /magazine/: {article.href}"

        # Company context should have some data (either from OpenContext or basic detection)
        assert context.company_context.company_url, "company_url should be set"

        # Sitemap should have found some URLs (even if none match blog patterns)
        assert (
            context.sitemap.total_pages > 0
        ), f"Sitemap should have found URLs, got {context.sitemap.total_pages}"

        PASSED += 1
        print(f"\n  [PASS] Integration: Full Stage 1 run")

        # Save output for inspection
        output_path = Path(__file__).parent / "test_output_stage1.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(context.model_dump(), f, indent=2, ensure_ascii=False)
        print(f"\n  Output saved to: {output_path}")

        # Save markdown report for monitoring
        md_path = Path(__file__).parent / "test_output_stage1.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Stage 1 Test Report\n\n")
            f.write(f"**Generated:** {context.created_at}\n\n")
            f.write(f"**Job ID:** `{context.job_id}`\n\n")
            f.write(f"**Company URL:** {input_data.company_url}\n\n")
            f.write(
                f"**Language:** {context.language} | **Market:** {context.market}\n\n"
            )
            f.write(
                f"**OpenContext Called:** {context.opencontext_called} | **AI Calls:** {context.ai_calls}\n\n"
            )

            # Company Context Section
            f.write(f"---\n\n## Company Context\n\n")
            cc = context.company_context
            f.write(f"| Field | Value |\n")
            f.write(f"|-------|-------|\n")
            f.write(f"| Company Name | {cc.company_name} |\n")
            f.write(f"| Industry | {cc.industry} |\n")
            f.write(
                f"| Description | {cc.description[:200] + '...' if len(cc.description) > 200 else cc.description} |\n"
            )
            f.write(f"| Target Audience | {cc.target_audience} |\n")
            f.write(f"| Tone | {cc.tone} |\n")
            f.write(f"\n")

            if cc.products:
                f.write(f"### Products/Services\n\n")
                for p in cc.products[:10]:
                    f.write(f"- {p}\n")
                if len(cc.products) > 10:
                    f.write(f"- ... and {len(cc.products) - 10} more\n")
                f.write(f"\n")

            if cc.competitors:
                f.write(f"### Competitors\n\n")
                for c in cc.competitors[:10]:
                    f.write(f"- {c}\n")
                f.write(f"\n")

            if cc.pain_points:
                f.write(f"### Pain Points\n\n")
                for p in cc.pain_points[:10]:
                    f.write(f"- {p}\n")
                f.write(f"\n")

            if cc.value_propositions:
                f.write(f"### Value Propositions\n\n")
                for v in cc.value_propositions[:10]:
                    f.write(f"- {v}\n")
                f.write(f"\n")

            # Voice Persona
            if cc.voice_persona and cc.voice_persona.icp_profile:
                f.write(f"### Voice Persona\n\n")
                vp = cc.voice_persona
                f.write(f"**ICP Profile:** {vp.icp_profile}\n\n")
                f.write(f"**Voice Style:** {vp.voice_style}\n\n")
                if vp.language_style:
                    f.write(
                        f"**Language Style:** {vp.language_style.formality}, {vp.language_style.complexity}, {vp.language_style.perspective}\n\n"
                    )
                if vp.do_list:
                    f.write(f"**Do:** {', '.join(vp.do_list[:5])}\n\n")
                if vp.dont_list:
                    f.write(f"**Don't:** {', '.join(vp.dont_list[:5])}\n\n")

            # Visual Identity
            if cc.visual_identity:
                vi = cc.visual_identity
                f.write(f"### Visual Identity\n\n")
                if vi.brand_colors:
                    f.write(f"**Brand Colors:** {', '.join(vi.brand_colors)}\n\n")
                if vi.visual_style:
                    f.write(f"**Visual Style:** {vi.visual_style}\n\n")
                if vi.mood:
                    f.write(f"**Mood:** {vi.mood}\n\n")
                if vi.image_style_prompt:
                    f.write(f"**Image Style Prompt:** {vi.image_style_prompt}\n\n")
                if vi.blog_image_examples:
                    f.write(f"**Blog Image Examples:**\n\n")
                    for img in vi.blog_image_examples[:5]:
                        f.write(
                            f"- [{img.image_type}]({img.url}): {img.description[:100]}...\n"
                        )
                    f.write(f"\n")

            # Authors
            if cc.authors:
                f.write(f"### Authors\n\n")
                for author in cc.authors:
                    f.write(f"- **{author.name}**")
                    if author.title:
                        f.write(f" - {author.title}")
                    f.write(f"\n")
                    if author.bio:
                        f.write(f"  - {author.bio[:150]}...\n")
                    if author.linkedin_url:
                        f.write(f"  - LinkedIn: {author.linkedin_url}\n")
                f.write(f"\n")

            # Articles Section
            f.write(f"---\n\n## Articles Generated\n\n")
            f.write(f"| Keyword | Slug | Href | Word Count |\n")
            f.write(f"|---------|------|------|------------|\n")
            for article in context.articles:
                f.write(
                    f"| {article.keyword} | {article.slug} | {article.href} | {article.word_count or 'default'} |\n"
                )
            f.write(f"\n")

            # Sitemap Section
            f.write(f"---\n\n## Sitemap Analysis\n\n")
            sm = context.sitemap
            f.write(f"**Total Pages Found:** {sm.total_pages}\n\n")

            f.write(f"| Category | Count |\n")
            f.write(f"|----------|-------|\n")
            f.write(f"| Blog | {len(sm.blog_urls)} |\n")
            f.write(f"| Product | {len(sm.product_urls)} |\n")
            f.write(f"| Service | {len(sm.service_urls)} |\n")
            f.write(f"| Resource | {len(sm.resource_urls)} |\n")
            f.write(f"| Docs | {len(sm.docs_urls)} |\n")
            f.write(f"| Other | {len(sm.other_urls)} |\n")
            f.write(f"\n")

            # Blog URLs (most relevant for internal linking)
            if sm.blog_urls:
                f.write(f"### Blog URLs (for internal linking)\n\n")
                for url in sm.blog_urls[:50]:
                    f.write(f"- {url}\n")
                if len(sm.blog_urls) > 50:
                    f.write(f"\n*... and {len(sm.blog_urls) - 50} more blog URLs*\n")
                f.write(f"\n")

            # Product URLs
            if sm.product_urls:
                f.write(f"### Product URLs\n\n")
                for url in sm.product_urls[:20]:
                    f.write(f"- {url}\n")
                if len(sm.product_urls) > 20:
                    f.write(
                        f"\n*... and {len(sm.product_urls) - 20} more product URLs*\n"
                    )
                f.write(f"\n")

            # Resource URLs
            if sm.resource_urls:
                f.write(f"### Resource URLs\n\n")
                for url in sm.resource_urls[:20]:
                    f.write(f"- {url}\n")
                if len(sm.resource_urls) > 20:
                    f.write(
                        f"\n*... and {len(sm.resource_urls) - 20} more resource URLs*\n"
                    )
                f.write(f"\n")

            # Docs URLs
            if sm.docs_urls:
                f.write(f"### Documentation URLs\n\n")
                for url in sm.docs_urls[:20]:
                    f.write(f"- {url}\n")
                if len(sm.docs_urls) > 20:
                    f.write(f"\n*... and {len(sm.docs_urls) - 20} more docs URLs*\n")
                f.write(f"\n")

        print(f"  Markdown report saved to: {md_path}")

    except AssertionError as e:
        FAILED += 1
        ERRORS.append(f"Integration test: {e}")
        print(f"\n  [FAIL] Integration: {e}")
    except Exception as e:
        FAILED += 1
        ERRORS.append(f"Integration test: {type(e).__name__}: {e}")
        print(f"\n  [ERROR] Integration: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


# Run integration test
asyncio.run(run_integration_test())


# =============================================================================
# Summary
# =============================================================================

print("\n" + "=" * 50)
print(f"RESULTS: {PASSED} passed, {FAILED} failed")
print("=" * 50)

if ERRORS:
    print("\nFailures:")
    for error in ERRORS:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("\nAll tests passed!")
    sys.exit(0)
