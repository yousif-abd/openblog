"""
Stage 2 Stress Tests - Edge cases and malformed inputs.

Run: python test_stage2.py
"""

import sys
from pathlib import Path

# Add parent to path
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

import json
from typing import Dict, Any

# Test results tracking
PASSED = 0
FAILED = 0
ERRORS = []


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
# Models Tests (shared/models.py)
# =============================================================================

print("\n=== Testing shared/models.py ===")

from shared.models import ArticleOutput, Source, ComparisonTable

@test("Source: valid URL")
def test_source_valid():
    s = Source(title="Test", url="https://example.com")
    assert s.url == "https://example.com"

test_source_valid()

@test("Source: empty URL raises error")
def test_source_empty_url():
    try:
        Source(title="Test", url="")
        assert False, "Should have raised"
    except ValueError:
        pass

test_source_empty_url()

@test("Source: None URL raises error")
def test_source_none_url():
    try:
        Source(title="Test", url=None)
        assert False, "Should have raised"
    except (ValueError, TypeError):
        pass

test_source_none_url()

@test("Source: invalid URL format raises error")
def test_source_invalid_url():
    try:
        Source(title="Test", url="not-a-url")
        assert False, "Should have raised"
    except ValueError:
        pass

test_source_invalid_url()

@test("ArticleOutput: converts dict sources to Source objects")
def test_article_converts_sources():
    article = ArticleOutput(
        Headline="Test Headline",
        Teaser="Test teaser",
        Direct_Answer="Test direct answer for the article",
        Intro="Test intro paragraph for the article",
        Meta_Title="Test Meta Title",
        Meta_Description="Test meta description for SEO",
        section_01_title="Section 1",
        section_01_content="<p>Content</p>",
        Sources=[
            {"title": "Source 1", "url": "https://example.com/1"},
            {"title": "Source 2", "url": "https://example.com/2"},
        ]
    )
    assert len(article.Sources) == 2
    assert isinstance(article.Sources[0], Source)

test_article_converts_sources()

@test("ArticleOutput: filters invalid sources silently")
def test_article_filters_invalid_sources():
    article = ArticleOutput(
        Headline="Test Headline",
        Teaser="Test teaser",
        Direct_Answer="Test direct answer for the article",
        Intro="Test intro paragraph for the article",
        Meta_Title="Test Meta Title",
        Meta_Description="Test meta description for SEO",
        section_01_title="Section 1",
        section_01_content="<p>Content</p>",
        Sources=[
            {"title": "Valid", "url": "https://example.com"},
            {"title": "Empty URL", "url": ""},
            {"title": "None URL", "url": None},
            {"title": "Whitespace URL", "url": "   "},
        ]
    )
    assert len(article.Sources) == 1
    assert article.Sources[0].title == "Valid"

test_article_filters_invalid_sources()

@test("ArticleOutput: truncates long headline")
def test_article_truncates_headline():
    long_headline = "A" * 150
    article = ArticleOutput(
        Headline=long_headline,
        Teaser="Test teaser",
        Direct_Answer="Test direct answer for the article",
        Intro="Test intro paragraph for the article",
        Meta_Title="Test Meta Title",
        Meta_Description="Test meta description for SEO",
        section_01_title="Section 1",
        section_01_content="<p>Content</p>",
    )
    assert len(article.Headline) <= 100
    assert article.Headline.endswith("...")

test_article_truncates_headline()

@test("ArticleOutput: truncates long meta title")
def test_article_truncates_meta_title():
    article = ArticleOutput(
        Headline="Test Headline",
        Teaser="Test teaser",
        Direct_Answer="Test direct answer for the article",
        Intro="Test intro paragraph for the article",
        Meta_Title="A" * 80,
        Meta_Description="Test meta description for SEO",
        section_01_title="Section 1",
        section_01_content="<p>Content</p>",
    )
    assert len(article.Meta_Title) <= 55

test_article_truncates_meta_title()

@test("ArticleOutput: truncates long meta description")
def test_article_truncates_meta_desc():
    article = ArticleOutput(
        Headline="Test Headline",
        Teaser="Test teaser",
        Direct_Answer="Test direct answer for the article",
        Intro="Test intro paragraph for the article",
        Meta_Title="Test Meta Title",
        Meta_Description="A" * 200,
        section_01_title="Section 1",
        section_01_content="<p>Content</p>",
    )
    assert len(article.Meta_Description) <= 160

test_article_truncates_meta_desc()

@test("ArticleOutput: rejects empty required fields")
def test_article_rejects_empty_required():
    try:
        ArticleOutput(
            Headline="",  # Empty
            Teaser="Test",
            Direct_Answer="Test",
            Intro="Test",
            Meta_Title="Test",
            Meta_Description="Test",
            section_01_title="Test",
            section_01_content="Test",
        )
        assert False, "Should have raised"
    except ValueError:
        pass

test_article_rejects_empty_required()

@test("ArticleOutput: converts dict tables to ComparisonTable objects")
def test_article_converts_tables():
    article = ArticleOutput(
        Headline="Test Headline",
        Teaser="Test teaser",
        Direct_Answer="Test direct answer for the article",
        Intro="Test intro paragraph for the article",
        Meta_Title="Test Meta Title",
        Meta_Description="Test meta description for SEO",
        section_01_title="Section 1",
        section_01_content="<p>Content</p>",
        tables=[
            {"title": "Comparison", "headers": ["A", "B"], "rows": [["1", "2"]]}
        ]
    )
    assert len(article.tables) == 1
    assert isinstance(article.tables[0], ComparisonTable)

test_article_converts_tables()

@test("ComparisonTable: validates column count")
def test_table_column_count():
    try:
        ComparisonTable(
            title="Test",
            headers=["A", "B", "C"],
            rows=[["1", "2"]]  # Missing column
        )
        assert False, "Should have raised"
    except ValueError:
        pass

test_table_column_count()

@test("ComparisonTable: rejects too few columns")
def test_table_min_columns():
    try:
        ComparisonTable(
            title="Test",
            headers=["A"],  # Need at least 2
            rows=[["1"]]
        )
        assert False, "Should have raised"
    except ValueError:
        pass

test_table_min_columns()


# =============================================================================
# Image Prompts Tests (image_prompts.py)
# =============================================================================

print("\n=== Testing image_prompts.py ===")

from image_prompts import build_image_prompt

@test("Image prompt: None company_data")
def test_prompt_none_company():
    prompt = build_image_prompt("AI Testing", None, "en", "hero", None)
    assert "professional" in prompt.lower()
    assert "AI Testing" in prompt

test_prompt_none_company()

@test("Image prompt: empty company_data")
def test_prompt_empty_company():
    prompt = build_image_prompt("AI Testing", {}, "en", "hero", None)
    assert "professional" in prompt.lower()

test_prompt_empty_company()

@test("Image prompt: preserves A/B Testing")
def test_prompt_preserves_ab_testing():
    prompt = build_image_prompt("A/B Testing Best Practices", {}, "en", "hero", None)
    assert "A/B Testing" in prompt or "a/b testing" in prompt.lower()

test_prompt_preserves_ab_testing()

@test("Image prompt: removes 'The' at start")
def test_prompt_removes_the():
    prompt = build_image_prompt("The Complete Guide", {}, "en", "hero", None)
    assert not prompt.startswith("The ")
    assert "Complete" not in prompt  # "Complete" should also be removed

test_prompt_removes_the()

@test("Image prompt: None values in avoid_list")
def test_prompt_none_in_avoid_list():
    visual_identity = {
        "avoid_in_images": [None, "people", None, "", "   "]
    }
    prompt = build_image_prompt("Test", {}, "en", "hero", visual_identity)
    assert "None" not in prompt
    assert "people" in prompt

test_prompt_none_in_avoid_list()

@test("Image prompt: None image_style_prompt")
def test_prompt_none_style():
    visual_identity = {
        "image_style_prompt": None
    }
    prompt = build_image_prompt("Test", {}, "en", "hero", visual_identity)
    assert "professional" in prompt.lower()

test_prompt_none_style()

@test("Image prompt: empty string industry")
def test_prompt_empty_industry():
    company = {"industry": ""}
    prompt = build_image_prompt("Test", company, "en", "hero", None)
    assert "professional" in prompt.lower()

test_prompt_empty_industry()

@test("Image prompt: all positions")
def test_prompt_all_positions():
    for pos in ["hero", "mid", "bottom"]:
        prompt = build_image_prompt("Test", {}, "en", pos, None)
        assert prompt  # Not empty

test_prompt_all_positions()

@test("Image prompt: unknown position fallback")
def test_prompt_unknown_position():
    prompt = build_image_prompt("Test", {}, "en", "unknown", None)
    assert "wide shot" in prompt

test_prompt_unknown_position()


# =============================================================================
# HTML Renderer Tests (shared/html_renderer.py)
# =============================================================================

print("\n=== Testing shared/html_renderer.py ===")

from shared.html_renderer import HTMLRenderer

@test("HTML: strips XSS from headline (removes tags)")
def test_html_strips_headline():
    article = {
        "Headline": "<script>alert('xss')</script>Test",
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": "<p>Content</p>",
    }
    html = HTMLRenderer.render(article)
    # HTMLRenderer._strip_html removes tags entirely (safer than escaping)
    assert "<script>" not in html
    assert "alert('xss')" not in html
    assert ">Test<" in html  # The "Test" text should remain

test_html_strips_headline()

@test("HTML: sanitizes script tags in section content")
def test_html_sanitizes_scripts():
    article = {
        "Headline": "Test",
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": "<p>Hello</p><script>evil()</script><p>World</p>",
    }
    html = HTMLRenderer.render(article)
    assert "<script>" not in html
    assert "evil()" not in html
    assert "Hello" in html
    assert "World" in html

test_html_sanitizes_scripts()

@test("HTML: sanitizes onclick handlers")
def test_html_sanitizes_onclick():
    article = {
        "Headline": "Test",
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": '<p onclick="evil()">Click me</p>',
    }
    html = HTMLRenderer.render(article)
    assert "onclick" not in html
    assert "evil()" not in html

test_html_sanitizes_onclick()

@test("HTML: sanitizes javascript: URLs")
def test_html_sanitizes_js_urls():
    article = {
        "Headline": "Test",
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": '<a href="javascript:alert(1)">Click</a>',
    }
    html = HTMLRenderer.render(article)
    assert "javascript:" not in html

test_html_sanitizes_js_urls()

@test("HTML: handles None source URL in dict")
def test_html_none_source_url():
    article = {
        "Headline": "Test",
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": "<p>Content</p>",
        "Sources": [
            {"title": "Good", "url": "https://example.com"},
            {"title": "Bad", "url": None},
        ]
    }
    html = HTMLRenderer.render(article)
    assert "Good" in html
    assert "example.com" in html
    # Should not crash

test_html_none_source_url()

@test("HTML: handles Source objects")
def test_html_source_objects():
    article = {
        "Headline": "Test",
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": "<p>Content</p>",
        "Sources": [
            Source(title="Source 1", url="https://example.com/1"),
            Source(title="Source 2", url="https://example.com/2"),
        ]
    }
    html = HTMLRenderer.render(article)
    assert "Source 1" in html
    assert "Source 2" in html

test_html_source_objects()

@test("HTML: limits alt text length")
def test_html_alt_text_length():
    article = {
        "Headline": "A" * 200,  # Very long headline
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": "<p>Content</p>",
        "image_01_url": "https://example.com/image.jpg",
    }
    html = HTMLRenderer.render(article)
    # Check that alt attribute exists and isn't too long
    import re
    alt_match = re.search(r'alt="([^"]*)"', html)
    if alt_match:
        alt_text = alt_match.group(1)
        assert len(alt_text) <= 130  # 125 + some buffer for "..."

test_html_alt_text_length()

@test("HTML: dynamic language attribute")
def test_html_language_attr():
    article = {
        "Headline": "Test",
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": "<p>Content</p>",
    }
    html = HTMLRenderer.render(article, language="de")
    assert 'lang="de"' in html

test_html_language_attr()

@test("HTML: adds rel=noopener to external links")
def test_html_noopener():
    article = {
        "Headline": "Test",
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": "<p>Content</p>",
        "Sources": [{"title": "Test", "url": "https://example.com"}]
    }
    html = HTMLRenderer.render(article)
    assert 'rel="noopener noreferrer"' in html

test_html_noopener()

@test("HTML: renders tables with escaping")
def test_html_table_escaping():
    article = {
        "Headline": "Test",
        "Teaser": "Test",
        "Intro": "Test",
        "Meta_Title": "Test",
        "Meta_Description": "Test",
        "section_01_title": "Section",
        "section_01_content": "<p>Content</p>",
        "tables": [
            {
                "title": "<script>evil</script>",
                "headers": ["<b>A</b>", "B"],
                "rows": [["<script>x</script>", "2"]]
            }
        ]
    }
    html = HTMLRenderer.render(article)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

test_html_table_escaping()


# =============================================================================
# Image Creator Tests (image_creator.py)
# =============================================================================

print("\n=== Testing image_creator.py ===")

from image_creator import generate_alt_text, _mock_url

@test("Alt text: normal headline")
def test_alt_normal():
    alt = generate_alt_text("How to Use AI for Sales")
    assert alt == "Article image: How to Use AI for Sales"

test_alt_normal()

@test("Alt text: truncates long headline")
def test_alt_truncates():
    alt = generate_alt_text("A" * 200)
    assert len(alt) <= 125
    assert alt.endswith("...")

test_alt_truncates()

@test("Alt text: truncates at word boundary")
def test_alt_word_boundary():
    alt = generate_alt_text("Word " * 30)
    assert len(alt) <= 125
    assert not alt.endswith(" ...")  # Should end with word...

test_alt_word_boundary()

@test("Mock URL: returns real placeholder URL")
def test_mock_url_real():
    url = _mock_url("test prompt")
    assert url.startswith("https://placehold.co/")
    assert "Mock" in url

test_mock_url_real()


# =============================================================================
# Blog Writer Tests (blog_writer.py)
# =============================================================================

print("\n=== Testing blog_writer.py ===")

from blog_writer import _format_company_context, _build_custom_instructions, get_system_instruction

@test("Company context: handles empty dict")
def test_context_empty():
    result = _format_company_context({})
    assert "Unknown" in result  # Falls back to Unknown for company name

test_context_empty()

@test("Company context: handles None values")
def test_context_none_values():
    result = _format_company_context({
        "company_name": None,
        "industry": None,
        "products": None,
    })
    assert result  # Should not crash

test_context_none_values()

@test("Company context: formats authors as dict")
def test_context_authors_dict():
    result = _format_company_context({
        "company_name": "Test Co",
        "authors": [
            {"name": "John Doe", "title": "CEO"},
            {"name": "Jane Smith", "title": ""},
        ]
    })
    assert "John Doe" in result
    assert "CEO" in result
    assert "Jane Smith" in result

test_context_authors_dict()

@test("Company context: handles empty voice_persona")
def test_context_empty_voice():
    result = _format_company_context({
        "company_name": "Test",
        "voice_persona": {}
    })
    assert "Test" in result

test_context_empty_voice()

@test("Custom instructions: both batch and keyword")
def test_instructions_both():
    result = _build_custom_instructions("Batch instruction", "Keyword instruction")
    assert "Batch instruction" in result
    assert "Keyword instruction" in result
    assert "Additional" in result

test_instructions_both()

@test("Custom instructions: only batch")
def test_instructions_batch_only():
    result = _build_custom_instructions("Batch only", None)
    assert "Batch only" in result
    assert "Additional" not in result

test_instructions_batch_only()

@test("Custom instructions: only keyword")
def test_instructions_keyword_only():
    result = _build_custom_instructions(None, "Keyword only")
    assert "Keyword only" in result

test_instructions_keyword_only()

@test("Custom instructions: neither")
def test_instructions_neither():
    result = _build_custom_instructions(None, None)
    assert result == ""

test_instructions_neither()

@test("System instruction: injects date")
def test_system_instruction_date():
    result = get_system_instruction()
    import datetime
    year = str(datetime.datetime.now().year)
    assert year in result

test_system_instruction_date()


# =============================================================================
# Stage 2 Integration Tests
# =============================================================================

print("\n=== Testing stage_2.py (integration) ===")

from stage_2 import Stage2Input, Stage2Output, CompanyContext

@test("Stage2Input: validates keyword min length")
def test_input_keyword_min():
    try:
        Stage2Input(
            keyword="",
            company_context=CompanyContext()
        )
        assert False, "Should have raised"
    except ValueError:
        pass

test_input_keyword_min()

@test("Stage2Input: validates word_count range")
def test_input_word_count_range():
    try:
        Stage2Input(
            keyword="test",
            company_context=CompanyContext(),
            word_count=100  # Below minimum of 500
        )
        assert False, "Should have raised"
    except ValueError:
        pass

test_input_word_count_range()

@test("Stage2Input: accepts valid input")
def test_input_valid():
    input_data = Stage2Input(
        keyword="AI Sales Automation",
        company_context=CompanyContext(
            company_name="Test Corp",
            industry="SaaS"
        ),
        word_count=2000,
        language="en",
        country="United States"
    )
    assert input_data.keyword == "AI Sales Automation"
    assert input_data.word_count == 2000

test_input_valid()

@test("Stage2Output: generates job_id if not provided")
def test_output_job_id():
    # Create a minimal valid article
    article = ArticleOutput(
        Headline="Test Headline",
        Teaser="Test teaser",
        Direct_Answer="Test direct answer for the article",
        Intro="Test intro paragraph for the article",
        Meta_Title="Test Meta Title",
        Meta_Description="Test meta description for SEO",
        section_01_title="Section 1",
        section_01_content="<p>Content</p>",
    )
    output = Stage2Output(keyword="test", article=article)
    assert output.job_id  # Should be auto-generated UUID
    assert len(output.job_id) == 36  # UUID format

test_output_job_id()


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
