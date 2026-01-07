"""
Tests for Smart URL Classifier.

Tests the hybrid classification approach for sites without standard /blog/ patterns.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from smart_classifier import (
    SmartClassifier,
    SitemapEntry,
    ClassificationResult,
    URLScore,
    smart_classify,
    TOOL_KEYWORDS,
    BLOG_TITLE_PATTERNS,
)


# =============================================================================
# Test Data
# =============================================================================

# Hypofriend-style URLs (no /blog/ pattern)
HYPOFRIEND_URLS = [
    # Tool/calculator pages
    "https://hypofriend.de/de/baufinanzierung-rechner",
    "https://hypofriend.de/de/tilgungsrechner",
    "https://hypofriend.de/de/budgetrechner",
    "https://hypofriend.de/de/hauskauf-rechner",
    "https://hypofriend.de/en/mortgage-calculator",
    # Blog/content pages
    "https://hypofriend.de/de/wie-viel-haus-kann-ich-mir-leisten",
    "https://hypofriend.de/de/immobilienkredit-tipps",
    "https://hypofriend.de/de/was-kostet-ein-haus-in-berlin",
    "https://hypofriend.de/de/eigenkapital-beim-hauskauf",
    "https://hypofriend.de/de/beste-baufinanzierung-2024",
    "https://hypofriend.de/en/how-to-buy-house-germany",
    # Other pages
    "https://hypofriend.de/de/ueber-uns",
    "https://hypofriend.de/de/kontakt",
    "https://hypofriend.de/de/impressum",
    "https://hypofriend.de/en/about",
]

# Standard blog URLs for comparison
STANDARD_BLOG_URLS = [
    "https://example.com/blog/how-to-save-money",
    "https://example.com/blog/investment-tips",
    "https://example.com/news/market-update",
]


# =============================================================================
# Unit Tests - SitemapEntry
# =============================================================================

class TestSitemapEntry:
    """Tests for SitemapEntry dataclass."""

    def test_path_parsing(self):
        """Test URL path parsing."""
        entry = SitemapEntry(url="https://example.com/de/some-article")
        assert entry.path_depth == 2
        assert entry.path_segments == ["de", "some-article"]

    def test_root_url(self):
        """Test root URL handling."""
        entry = SitemapEntry(url="https://example.com/")
        assert entry.path_depth == 0
        assert entry.path_segments == []

    def test_deep_path(self):
        """Test deep path handling."""
        entry = SitemapEntry(url="https://example.com/a/b/c/d/e")
        assert entry.path_depth == 5
        assert entry.path_segments == ["a", "b", "c", "d", "e"]

    def test_metadata(self):
        """Test metadata storage."""
        entry = SitemapEntry(
            url="https://example.com/page",
            priority=0.8,
            changefreq="weekly",
            lastmod="2024-01-01"
        )
        assert entry.priority == 0.8
        assert entry.changefreq == "weekly"
        assert entry.lastmod == "2024-01-01"


# =============================================================================
# Unit Tests - URLScore
# =============================================================================

class TestURLScore:
    """Tests for URLScore dataclass."""

    def test_blog_classification(self):
        """Test blog classification with high blog score."""
        score = URLScore(url="https://example.com/article", blog_score=0.8, tool_score=0.2)
        assert score.classification == "blog"

    def test_tool_classification(self):
        """Test tool classification with high tool score."""
        score = URLScore(url="https://example.com/calc", blog_score=0.1, tool_score=0.7)
        assert score.classification == "tool"

    def test_other_classification(self):
        """Test other classification when scores are close."""
        score = URLScore(url="https://example.com/page", blog_score=0.4, tool_score=0.4)
        assert score.classification == "other"

    def test_edge_case_threshold(self):
        """Test classification at the 0.3 threshold boundary."""
        # Exactly at threshold - should be other
        score = URLScore(url="https://example.com/page", blog_score=0.5, tool_score=0.2)
        assert score.classification == "blog"  # 0.5 > 0.2 + 0.3

        score = URLScore(url="https://example.com/page", blog_score=0.5, tool_score=0.25)
        assert score.classification == "other"  # 0.5 <= 0.25 + 0.3


# =============================================================================
# Unit Tests - SmartClassifier URL Analysis
# =============================================================================

class TestSmartClassifierURLAnalysis:
    """Tests for URL structure analysis."""

    @pytest.fixture
    def classifier(self):
        return SmartClassifier(enable_ai_fallback=False)

    def test_tool_keyword_detection(self, classifier):
        """Test detection of tool keywords in URLs."""
        entries = [
            SitemapEntry(url="https://example.com/de/baufinanzierung-rechner"),
            SitemapEntry(url="https://example.com/de/tilgungsrechner"),
            SitemapEntry(url="https://example.com/en/calculator"),
        ]

        scores = classifier._analyze_url_structure(entries)

        for url in ["https://example.com/de/baufinanzierung-rechner",
                    "https://example.com/de/tilgungsrechner",
                    "https://example.com/en/calculator"]:
            assert scores[url].tool_score > 0, f"Expected tool signal for {url}"
            assert "tool_keyword" in scores[url].signals or "tool_keyword_partial" in scores[url].signals

    def test_language_prefix_signal(self, classifier):
        """Test language prefix detection."""
        entries = [
            SitemapEntry(url="https://example.com/de/some-article"),
            SitemapEntry(url="https://example.com/en/another-article"),
            SitemapEntry(url="https://example.com/fr/un-article"),
        ]

        scores = classifier._analyze_url_structure(entries)

        for entry in entries:
            assert "lang_prefix" in scores[entry.url].signals

    def test_slug_format_signal(self, classifier):
        """Test slug format detection."""
        entries = [
            SitemapEntry(url="https://example.com/de/wie-viel-haus-kann-ich-mir-leisten"),
        ]

        scores = classifier._analyze_url_structure(entries)
        url = entries[0].url
        assert "slug_format" in scores[url].signals

    def test_no_false_positives_for_non_tools(self, classifier):
        """Test that content pages don't get tool signals."""
        entries = [
            SitemapEntry(url="https://example.com/de/immobilienkredit-tipps"),
            SitemapEntry(url="https://example.com/de/was-kostet-ein-haus"),
        ]

        scores = classifier._analyze_url_structure(entries)

        for entry in entries:
            assert "tool_keyword" not in scores[entry.url].signals
            assert "tool_keyword_partial" not in scores[entry.url].signals


# =============================================================================
# Unit Tests - Sitemap Metadata Signals
# =============================================================================

class TestSitemapMetadataSignals:
    """Tests for sitemap metadata analysis."""

    @pytest.fixture
    def classifier(self):
        return SmartClassifier(enable_ai_fallback=False)

    def test_high_priority_signal(self, classifier):
        """Test high priority adds blog signal."""
        entries = [
            SitemapEntry(url="https://example.com/article", priority=0.8),
            SitemapEntry(url="https://example.com/tool", priority=0.2),
        ]

        scores = {e.url: URLScore(url=e.url) for e in entries}
        classifier._apply_sitemap_signals(scores, entries)

        assert "high_priority" in scores["https://example.com/article"].signals
        assert "low_priority" in scores["https://example.com/tool"].signals

    def test_changefreq_signal(self, classifier):
        """Test changefreq adds appropriate signals."""
        entries = [
            SitemapEntry(url="https://example.com/blog", changefreq="daily"),
            SitemapEntry(url="https://example.com/static", changefreq="never"),
        ]

        scores = {e.url: URLScore(url=e.url) for e in entries}
        classifier._apply_sitemap_signals(scores, entries)

        assert "frequent_update" in scores["https://example.com/blog"].signals
        assert "rare_update" in scores["https://example.com/static"].signals


# =============================================================================
# Unit Tests - Cluster Analysis
# =============================================================================

class TestClusterAnalysis:
    """Tests for URL cluster analysis."""

    @pytest.fixture
    def classifier(self):
        return SmartClassifier(enable_ai_fallback=False)

    def test_matching_depth_signal(self, classifier):
        """Test matching depth adds blog signal."""
        known_blogs = [
            "https://example.com/de/article-1",
            "https://example.com/de/article-2",
            "https://example.com/de/article-3",
        ]

        scores = {
            "https://example.com/de/article-4": URLScore(url="https://example.com/de/article-4"),
            "https://example.com/tool": URLScore(url="https://example.com/tool"),
        }

        classifier._apply_cluster_signals(scores, known_blogs)

        assert "matching_depth" in scores["https://example.com/de/article-4"].signals
        assert "matching_depth" not in scores["https://example.com/tool"].signals

    def test_matching_prefix_signal(self, classifier):
        """Test matching prefix pattern adds blog signal."""
        known_blogs = [
            "https://example.com/de/artikel/topic-1",
            "https://example.com/de/artikel/topic-2",
        ]

        scores = {
            "https://example.com/de/artikel/topic-3": URLScore(url="https://example.com/de/artikel/topic-3"),
            "https://example.com/de/other/page": URLScore(url="https://example.com/de/other/page"),
        }

        classifier._apply_cluster_signals(scores, known_blogs)

        assert "matching_prefix" in scores["https://example.com/de/artikel/topic-3"].signals
        assert "matching_prefix" not in scores["https://example.com/de/other/page"].signals


# =============================================================================
# Unit Tests - Title Pattern Matching
# =============================================================================

class TestTitlePatterns:
    """Tests for title-based classification."""

    @pytest.fixture
    def classifier(self):
        return SmartClassifier(enable_ai_fallback=False)

    def test_blog_title_patterns(self, classifier):
        """Test blog title pattern detection."""
        samples = {
            "https://example.com/article": {
                "title": "Wie viel Haus kann ich mir leisten?",
                "description": "",
                "h1": "",
            }
        }

        scores = {
            "https://example.com/article": URLScore(url="https://example.com/article"),
        }

        classifier._apply_title_signals(scores, samples)

        assert "blog_title_pattern" in scores["https://example.com/article"].signals

    def test_tool_title_patterns(self, classifier):
        """Test tool title pattern detection."""
        samples = {
            "https://example.com/calc": {
                "title": "Baufinanzierung Rechner - Berechnen Sie Ihre Rate",
                "description": "",
                "h1": "",
            }
        }

        scores = {
            "https://example.com/calc": URLScore(url="https://example.com/calc"),
        }

        classifier._apply_title_signals(scores, samples)

        assert "tool_title_pattern" in scores["https://example.com/calc"].signals

    def test_question_title_signal(self, classifier):
        """Test question-style title detection."""
        samples = {
            "https://example.com/faq": {
                "title": "What is the best mortgage rate?",
                "description": "",
                "h1": "",
            }
        }

        scores = {
            "https://example.com/faq": URLScore(url="https://example.com/faq"),
        }

        classifier._apply_title_signals(scores, samples)

        assert "question_title" in scores["https://example.com/faq"].signals


# =============================================================================
# Integration Tests
# =============================================================================

class TestSmartClassifierIntegration:
    """Integration tests for the full classification flow."""

    @pytest.mark.asyncio
    async def test_classify_with_known_blogs(self):
        """Test classification with pre-identified blog URLs."""
        classifier = SmartClassifier(enable_ai_fallback=False)

        entries = [
            SitemapEntry(url="https://example.com/de/new-article"),
        ]
        known_blogs = [
            "https://example.com/de/article-1",
            "https://example.com/de/article-2",
        ]

        result = await classifier.classify(entries, known_blogs)

        assert "https://example.com/de/article-1" in result.blog_urls
        assert "https://example.com/de/article-2" in result.blog_urls
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_classify_hypofriend_style_urls(self):
        """Test classification of Hypofriend-style URLs."""
        classifier = SmartClassifier(
            sample_size=5,
            enable_ai_fallback=False,
        )

        # Create entries for tool pages
        entries = [
            SitemapEntry(url="https://hypofriend.de/de/baufinanzierung-rechner"),
            SitemapEntry(url="https://hypofriend.de/de/tilgungsrechner"),
            SitemapEntry(url="https://hypofriend.de/de/budgetrechner"),
        ]

        result = await classifier.classify(entries, known_blog_urls=[])

        # All should be classified as tools due to -rechner suffix
        assert len(result.tool_urls) >= 2
        assert result.method_used in ["url_analysis", "title_sampling"]

    @pytest.mark.asyncio
    async def test_empty_entries(self):
        """Test handling of empty entries list."""
        classifier = SmartClassifier(enable_ai_fallback=False)

        result = await classifier.classify([], known_blog_urls=["https://example.com/blog/1"])

        assert result.blog_urls == ["https://example.com/blog/1"]
        assert result.confidence == 1.0
        assert result.method_used == "pattern_only"

    @pytest.mark.asyncio
    async def test_method_determination(self):
        """Test correct method reporting."""
        classifier = SmartClassifier(enable_ai_fallback=False)

        # With no sampling needed
        entries = [SitemapEntry(url="https://example.com/de/rechner")]
        result = await classifier.classify(entries)

        assert result.method_used == "url_analysis"


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestSmartClassifyFunction:
    """Tests for the smart_classify convenience function."""

    @pytest.mark.asyncio
    async def test_basic_usage(self):
        """Test basic smart_classify usage."""
        urls = [
            "https://example.com/de/rechner",
            "https://example.com/de/article",
        ]

        result = await smart_classify(urls, sample_size=2, enable_ai=False)

        assert isinstance(result, ClassificationResult)
        assert result.method_used in ["url_analysis", "title_sampling"]

    @pytest.mark.asyncio
    async def test_with_metadata(self):
        """Test smart_classify with sitemap metadata."""
        urls = ["https://example.com/de/article"]
        metadata = {
            "https://example.com/de/article": {
                "priority": 0.9,
                "changefreq": "daily",
            }
        }

        result = await smart_classify(urls, metadata=metadata, enable_ai=False)

        # High priority should add blog signal
        assert isinstance(result, ClassificationResult)


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_malformed_urls(self):
        """Test handling of malformed URLs."""
        classifier = SmartClassifier(enable_ai_fallback=False)

        entries = [
            SitemapEntry(url="not-a-valid-url"),
            SitemapEntry(url=""),
        ]

        # Should not raise, just handle gracefully
        result = await classifier.classify(entries)
        assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_unicode_urls(self):
        """Test handling of Unicode in URLs."""
        classifier = SmartClassifier(enable_ai_fallback=False)

        entries = [
            SitemapEntry(url="https://example.com/de/über-uns"),
            SitemapEntry(url="https://example.com/de/日本語"),
        ]

        result = await classifier.classify(entries)
        assert isinstance(result, ClassificationResult)

    @pytest.mark.asyncio
    async def test_very_long_urls(self):
        """Test handling of very long URLs."""
        classifier = SmartClassifier(enable_ai_fallback=False)

        long_path = "/".join(["segment"] * 100)
        entries = [
            SitemapEntry(url=f"https://example.com{long_path}"),
        ]

        result = await classifier.classify(entries)
        assert isinstance(result, ClassificationResult)


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
