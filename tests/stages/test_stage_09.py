"""
Tests for Stage 9: Image Generation

Tests:
- ImageGenerator client initialization
- Image prompt generation (English, German, French, Spanish)
- Image generation (mock mode)
- Alt text generation
- Stage execution
- Conditional skip (if image already exists)
"""

import pytest
from pipeline.core import ExecutionContext
from pipeline.models.image_generator import ImageGenerator
from pipeline.models.output_schema import ArticleOutput
from pipeline.prompts.image_prompt import generate_image_prompt
from pipeline.blog_generation.stage_06_image import ImageStage


@pytest.fixture
def valid_article():
    """Create article for image generation."""
    return ArticleOutput(
        Headline="Complete Guide to Python Programming in 2024",
        Teaser="Learn Python step by step.",
        Direct_Answer="Python is a versatile programming language.",
        Intro="Introduction to Python.",
        Meta_Title="Python Guide",
        Meta_Description="Learn Python",
    )


@pytest.fixture
def valid_company_data():
    """Create valid company data."""
    return {
        "company_name": "Tech Co",
        "industry": "Technology",
        "description": "A leading technology company",
    }


@pytest.fixture
def valid_job_config():
    """Create valid job configuration."""
    return {
        "primary_keyword": "python",
        "gpt_language": "en",
    }


@pytest.fixture
def valid_context(valid_article, valid_company_data, valid_job_config):
    """Create valid ExecutionContext for Stage 9."""
    return ExecutionContext(
        job_id="test-job-123",
        job_config=valid_job_config,
        company_data=valid_company_data,
        language="en",
        prompt="Test prompt",
        raw_article="Test article",
        structured_data=valid_article,
    )


class TestImagePromptGeneration:
    """Test image prompt generation."""

    def test_generate_english_prompt(self, valid_article, valid_company_data, valid_job_config):
        """Test English prompt generation."""
        prompt = generate_image_prompt(
            headline=valid_article.Headline,
            company_data=valid_company_data,
            job_config=valid_job_config,
        )

        assert prompt is not None
        assert len(prompt) > 100
        assert "Python" in prompt
        assert "1200x630" in prompt
        assert "professional" in prompt.lower()

    def test_generate_german_prompt(self, valid_article, valid_company_data):
        """Test German prompt generation."""
        config = {"gpt_language": "de"}
        prompt = generate_image_prompt(
            headline=valid_article.Headline,
            company_data=valid_company_data,
            job_config=config,
        )

        assert prompt is not None
        assert len(prompt) > 100
        assert "1200x630" in prompt

    def test_generate_french_prompt(self, valid_article, valid_company_data):
        """Test French prompt generation."""
        config = {"gpt_language": "fr"}
        prompt = generate_image_prompt(
            headline=valid_article.Headline,
            company_data=valid_company_data,
            job_config=config,
        )

        assert prompt is not None
        assert len(prompt) > 100
        assert "1200x630" in prompt

    def test_generate_spanish_prompt(self, valid_article, valid_company_data):
        """Test Spanish prompt generation."""
        config = {"gpt_language": "es"}
        prompt = generate_image_prompt(
            headline=valid_article.Headline,
            company_data=valid_company_data,
            job_config=config,
        )

        assert prompt is not None
        assert len(prompt) > 100
        assert "1200x630" in prompt

    def test_prompt_includes_industry(self, valid_article, valid_company_data, valid_job_config):
        """Test prompt includes industry information."""
        prompt = generate_image_prompt(
            headline=valid_article.Headline,
            company_data=valid_company_data,
            job_config=valid_job_config,
        )

        assert "Technology" in prompt or "technology" in prompt.lower()

    def test_prompt_with_empty_industry(self, valid_article, valid_job_config):
        """Test prompt generation with missing industry."""
        company_data = {"company_name": "Test Co"}
        prompt = generate_image_prompt(
            headline=valid_article.Headline,
            company_data=company_data,
            job_config=valid_job_config,
        )

        assert prompt is not None
        assert len(prompt) > 100


class TestImageGenerator:
    """Test image generator client."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = ImageGenerator()
        assert generator is not None
        assert generator.mock_mode is True  # Default to mock if no API key

    def test_generator_mock_mode(self):
        """Test generator in mock mode."""
        generator = ImageGenerator()
        assert generator.mock_mode is True

    def test_generate_image_mock(self):
        """Test image generation in mock mode."""
        generator = ImageGenerator()
        prompt = "A beautiful landscape with mountains"
        image_url = generator.generate_image(prompt)

        assert image_url is not None
        assert "mock-cdn.example.com" in image_url or isinstance(image_url, str)

    def test_generate_image_empty_prompt(self):
        """Test image generation with empty prompt."""
        generator = ImageGenerator()
        image_url = generator.generate_image("")

        assert image_url is None

    def test_generate_image_whitespace_prompt(self):
        """Test image generation with whitespace prompt."""
        generator = ImageGenerator()
        image_url = generator.generate_image("   ")

        assert image_url is None

    def test_generate_alt_text_short_headline(self):
        """Test alt text generation for short headline."""
        generator = ImageGenerator()
        headline = "Short Title"
        alt_text = generator.generate_alt_text(headline)

        assert alt_text == "Article image: Short Title"
        assert len(alt_text) <= 125

    def test_generate_alt_text_long_headline(self):
        """Test alt text generation for long headline."""
        generator = ImageGenerator()
        headline = "This is a very long headline that exceeds 125 characters when combined with the article image prefix text"
        alt_text = generator.generate_alt_text(headline)

        assert len(alt_text) <= 125
        assert "Article image:" in alt_text

    def test_generator_repr(self):
        """Test string representation."""
        generator = ImageGenerator()
        repr_str = repr(generator)

        assert "ImageGenerator" in repr_str
        assert "model=" in repr_str


class TestImageStage:
    """Test Stage 9: Image Generation."""

    @pytest.mark.asyncio
    async def test_execute_success(self, valid_context):
        """Test successful Stage 9 execution."""
        stage = ImageStage()
        result = await stage.execute(valid_context)

        assert "image_url" in result.parallel_results
        assert "image_alt_text" in result.parallel_results
        # Alt text should be generated
        assert len(result.parallel_results["image_alt_text"]) > 0

    @pytest.mark.asyncio
    async def test_execute_no_structured_data(self):
        """Test execution with no structured data."""
        context = ExecutionContext(
            job_id="test",
            job_config={},
            company_data={},
            language="en",
            prompt="test",
            raw_article="test",
            structured_data=None,
        )

        stage = ImageStage()
        result = await stage.execute(context)

        assert result.parallel_results["image_url"] == ""
        assert result.parallel_results["image_alt_text"] == ""

    @pytest.mark.asyncio
    async def test_execute_skip_existing_image(self, valid_context):
        """Test conditional skip when image already exists."""
        # Add existing image to structured data
        valid_context.structured_data.image_url = "https://example.com/image.jpg"

        stage = ImageStage()
        result = await stage.execute(valid_context)

        # Should skip and use existing image
        assert result.parallel_results["image_url"] == "https://example.com/image.jpg"
        assert len(result.parallel_results["image_alt_text"]) > 0

    @pytest.mark.asyncio
    async def test_execute_generates_alt_text(self, valid_context):
        """Test that alt text is generated."""
        stage = ImageStage()
        result = await stage.execute(valid_context)

        alt_text = result.parallel_results["image_alt_text"]
        assert "Article image:" in alt_text
        assert valid_context.structured_data.Headline in alt_text

    def test_stage_repr(self):
        """Test string representation."""
        stage = ImageStage()
        repr_str = repr(stage)

        assert "ImageStage" in repr_str
        assert "stage_num=9" in repr_str


class TestImageIntegration:
    """Integration tests for image generation."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, valid_context):
        """Test complete image generation workflow."""
        stage = ImageStage()
        result = await stage.execute(valid_context)

        # Check all results are populated
        assert "image_url" in result.parallel_results
        assert "image_alt_text" in result.parallel_results

        # Check alt text is valid
        alt_text = result.parallel_results["image_alt_text"]
        assert len(alt_text) > 0
        assert len(alt_text) <= 125
        assert "Article image:" in alt_text

    @pytest.mark.asyncio
    async def test_workflow_with_different_companies(self, valid_article):
        """Test workflow with different company data."""
        companies = [
            {"company_name": "Finance Co", "industry": "Finance", "description": "Financial services"},
            {
                "company_name": "Healthcare Inc",
                "industry": "Healthcare",
                "description": "Healthcare provider",
            },
            {
                "company_name": "Tech Startup",
                "industry": "Technology",
                "description": "Tech company",
            },
        ]

        for company_data in companies:
            context = ExecutionContext(
                job_id="test-job",
                job_config={"primary_keyword": "test", "gpt_language": "en"},
                company_data=company_data,
                language="en",
                prompt="Test prompt",
                raw_article="Test article",
                structured_data=valid_article,
            )

            stage = ImageStage()
            result = await stage.execute(context)

            assert "image_url" in result.parallel_results
            assert "image_alt_text" in result.parallel_results
            assert len(result.parallel_results["image_alt_text"]) > 0

    @pytest.mark.asyncio
    async def test_workflow_multi_language(self, valid_article, valid_company_data):
        """Test workflow with different languages."""
        languages = ["en", "de", "fr", "es"]

        for lang in languages:
            context = ExecutionContext(
                job_id=f"test-job-{lang}",
                job_config={"primary_keyword": "test", "gpt_language": lang},
                company_data=valid_company_data,
                language=lang,
                prompt="Test prompt",
                raw_article="Test article",
                structured_data=valid_article,
            )

            stage = ImageStage()
            result = await stage.execute(context)

            assert "image_url" in result.parallel_results
            assert "image_alt_text" in result.parallel_results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
