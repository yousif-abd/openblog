"""
Blog Writer - Calls Gemini to generate the article.

Uses shared GeminiClient for consistency across all stages:
- Gemini 3 Flash Preview
- URL Context + Google Search grounding
- Structured JSON output

Prompts are externalized to prompts/ folder for easy iteration.

Requires:
- GEMINI_API_KEY environment variable
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent to path for shared imports
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from article_schema import ArticleOutput

try:
    from shared.gemini_client import GeminiClient
except ImportError:
    GeminiClient = None

logger = logging.getLogger(__name__)

# Prompts directory
PROMPTS_DIR = Path(__file__).parent / "prompts"


# =============================================================================
# Prompt Loading
# =============================================================================

def _load_prompt(filename: str, fallback: str = "") -> str:
    """Load prompt from external file, with fallback."""
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    logger.warning(f"Prompt file not found: {path}, using fallback")
    return fallback


# Fallback prompts (used if files don't exist)
_FALLBACK_SYSTEM = '''You are an expert content writer. Write like a skilled human, not AI.

HARD RULES:
- Use Google Search for all stats/facts - NEVER invent them
- Only use exact URLs from search results - NEVER guess URLs
- NEVER mention competitors by name
- NO em-dashes (—), NO "Here's how", "Key points:", or robotic phrases

FRESH DATA:
- Today is {current_date}
- Use current year data. Say "2025 report" not "recent report"

VOICE:
- Match the company's tone and voice persona exactly

CONTENT QUALITY:
- Be direct - no filler like "In today's rapidly evolving..."
- Vary section lengths (some long 500+ words, some shorter)
- Include 2+ of: decision frameworks, concrete scenarios, common mistakes, strong opinions
- Cite stats naturally inline: "According to [Source]'s report..." not boring lists

FORMATTING:
- HTML: <p>, <ul>, <li>, <ol>, <strong>
- Lists are encouraged - use them for any set of 3+ related points'''


def get_system_instruction() -> str:
    """Get system instruction with current date injected."""
    template = _load_prompt("system_instruction.txt", _FALLBACK_SYSTEM)
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        return template.format(current_date=current_date)
    except KeyError as e:
        logger.error(f"System instruction template has unknown placeholder: {e}")
        # Fall back to template with manual date substitution
        return _FALLBACK_SYSTEM.format(current_date=current_date)


_FALLBACK_USER_PROMPT = '''Write a comprehensive, engaging blog article.

TOPIC: {keyword}

COMPANY CONTEXT:
{company_context}

LOCALIZATION:
- Language: {language}
- Country/Region: {country}

PARAMETERS:
- Word count: {word_count}
- Sections: 4-6 content sections
- PAA: 4 People Also Ask questions with answers
- FAQ: 5-6 FAQ questions with answers
- Takeaways: 3 key takeaways

{custom_instructions_section}

Return valid JSON with: Headline, Teaser, Direct_Answer, Intro, Meta_Title, Meta_Description,
section_01_title, section_01_content, ... (up to section_09), key_takeaway_01-03,
paa_01_question, paa_01_answer, ... (4 PAAs), faq_01_question, faq_01_answer, ... (up to 6 FAQs),
Sources (list of {{title, url}}), Search_Queries.
'''


def get_user_prompt() -> str:
    """Get user prompt template."""
    prompt = _load_prompt("user_prompt.txt", _FALLBACK_USER_PROMPT)
    if not prompt or not prompt.strip():
        logger.warning("Empty user_prompt.txt, using fallback")
        return _FALLBACK_USER_PROMPT
    return prompt


# =============================================================================
# Article Generation
# =============================================================================

async def write_article(
    keyword: str,
    company_context: Dict[str, Any],
    word_count: int = 2000,
    language: str = "en",
    country: str = "United States",
    batch_instructions: Optional[str] = None,
    keyword_instructions: Optional[str] = None,
    api_key: Optional[str] = None,
) -> ArticleOutput:
    """
    Generate a complete blog article using Gemini.

    Uses shared GeminiClient for consistency.

    Args:
        keyword: Primary SEO keyword
        company_context: Company info dict (from Stage 1)
        word_count: Target word count
        language: Article language code (e.g., "en", "de", "es")
        country: Target country/region for localization (e.g., "United States", "Germany")
        batch_instructions: Batch-level instructions (applies to all articles)
        keyword_instructions: Keyword-level instructions (adds to batch instructions)
        api_key: Gemini API key (falls back to env var)

    Returns:
        ArticleOutput with all fields populated

    Raises:
        ValueError: If no API key
        Exception: If Gemini call fails
    """
    logger.info(f"Writing article for: {keyword} ({language}/{country})")

    try:
        # Use shared GeminiClient
        if GeminiClient is None:
            raise ImportError("shared.gemini_client not available")

        client = GeminiClient(api_key=api_key)

        # Load prompts
        system_instruction = get_system_instruction()
        user_prompt_template = get_user_prompt()

        # Build company context string
        company_str = _format_company_context(company_context)

        # Build custom instructions section (batch + keyword combined)
        custom_instructions_section = _build_custom_instructions(batch_instructions, keyword_instructions)

        # Build prompt with KeyError handling
        try:
            prompt = user_prompt_template.format(
                keyword=keyword,
                company_context=company_str,
                word_count=word_count,
                language=language,
                country=country,
                custom_instructions_section=custom_instructions_section,
            )
        except KeyError as e:
            logger.error(f"Prompt template missing placeholder: {e}. Using fallback.")
            prompt = _FALLBACK_USER_PROMPT.format(
                keyword=keyword,
                company_context=company_str,
                word_count=word_count,
                language=language,
                country=country,
                custom_instructions_section=custom_instructions_section,
            )

        # Call with URL Context + Google Search grounding + source extraction
        result = await client.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            use_url_context=True,
            use_google_search=True,
            json_output=True,
            extract_sources=True,  # Extract real URLs from grounding metadata
            temperature=0.3,
            max_tokens=16384,  # Reasonable limit for blog articles
        )

        # Always use grounding sources (real URLs from Google Search) instead of AI-generated ones
        # AI tends to hallucinate URLs that look real but return 404/403
        if "_grounding_sources" in result:
            grounding_sources = result.pop("_grounding_sources")
            if grounding_sources:
                ai_sources = result.get("Sources", [])
                result["Sources"] = grounding_sources
                logger.info(f"Using {len(grounding_sources)} grounding sources (replaced {len(ai_sources) if ai_sources else 0} AI-generated)")

        logger.info(f"Article generated: {result.get('Headline', 'Unknown')[:50]}...")

        return ArticleOutput(**result)

    except Exception as e:
        logger.error(f"Blog generation failed: {e}")
        raise


def _format_company_context(context: Dict[str, Any]) -> str:
    """Format company context dict into readable string."""
    # Warn about missing critical fields
    if not context.get('company_name'):
        logger.warning("Missing company_name in context - using 'Unknown'")
    if not context.get('industry'):
        logger.debug("Missing industry in context")
    if not context.get('target_audience'):
        logger.debug("Missing target_audience in context")

    lines = [
        f"Company: {context.get('company_name', 'Unknown')}",
        f"Industry: {context.get('industry', '')}",
        f"Target Audience: {context.get('target_audience', '')}",
        f"Tone: {context.get('tone', 'professional')}",
    ]

    # Add company description if available
    description = context.get('description', '')
    if description:
        lines.append(f"About: {description}")

    products = context.get('products', [])
    if products:
        if isinstance(products, list):
            lines.append(f"Products: {', '.join(str(p) for p in products)}")
        else:
            lines.append(f"Products: {products}")

    voice = context.get('voice_persona', {})
    if voice:
        voice_style = voice.get('voice_style', '')
        if voice_style:
            lines.append(f"Voice Style: {voice_style}")
        lang_style = voice.get('language_style', {})
        if lang_style:
            formality = lang_style.get('formality', '')
            perspective = lang_style.get('perspective', '')
            if formality:
                lines.append(f"Formality: {formality}")
            if perspective:
                lines.append(f"Perspective: {perspective}")

    # Add authors if available (for byline/credibility)
    authors = context.get('authors', [])
    if authors:
        author_names = []
        for author in authors:
            if isinstance(author, dict):
                name = author.get('name', '')
                title = author.get('title', '')
                if name:
                    author_names.append(f"{name} ({title})" if title else name)
            elif hasattr(author, 'name'):
                author_names.append(f"{author.name} ({author.title})" if author.title else author.name)
        if author_names:
            lines.append(f"Authors: {', '.join(author_names)}")

    return "\n".join(lines)


def _build_custom_instructions(
    batch_instructions: Optional[str],
    keyword_instructions: Optional[str],
) -> str:
    """
    Build combined custom instructions section.

    Batch instructions apply to all articles.
    Keyword instructions are added for specific articles.

    Args:
        batch_instructions: Batch-level instructions (e.g., "Target B2B SaaS companies")
        keyword_instructions: Keyword-level instructions (e.g., "Focus on Salesforce")

    Returns:
        Formatted instructions section, or empty string if none provided.
    """
    if not batch_instructions and not keyword_instructions:
        return ""

    lines = ["CUSTOM INSTRUCTIONS:"]

    if batch_instructions:
        lines.append(batch_instructions.strip())

    if keyword_instructions:
        if batch_instructions:
            lines.append("")
            lines.append(f"Additional for this article: {keyword_instructions.strip()}")
        else:
            lines.append(keyword_instructions.strip())

    return "\n".join(lines)


# =============================================================================
# BlogWriter Class (wrapper for compatibility)
# =============================================================================

class BlogWriter:
    """
    Wrapper class for write_article function.

    Provides class-based interface for compatibility with stage_2.py.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("No Gemini API key. Set GEMINI_API_KEY environment variable.")
        logger.info("BlogWriter initialized (using shared GeminiClient)")

    async def write_article(
        self,
        keyword: str,
        company_context: Dict[str, Any],
        word_count: int = 2000,
        language: str = "en",
        country: str = "United States",
        batch_instructions: Optional[str] = None,
        keyword_instructions: Optional[str] = None,
    ) -> ArticleOutput:
        """Generate article using write_article function."""
        return await write_article(
            keyword=keyword,
            company_context=company_context,
            word_count=word_count,
            language=language,
            country=country,
            batch_instructions=batch_instructions,
            keyword_instructions=keyword_instructions,
            api_key=self.api_key,
        )


# =============================================================================
# CLI for standalone testing
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python blog_writer.py <keyword> [company_url]")
        sys.exit(1)

    # Check for API key first
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: No API key. Set GEMINI_API_KEY environment variable.")
        sys.exit(1)

    keyword = sys.argv[1]
    company_url = sys.argv[2] if len(sys.argv) > 2 else "https://example.com"

    # Minimal company context
    company = {
        "company_name": company_url.replace("https://", "").replace("http://", "").split("/")[0],
        "company_url": company_url,
        "industry": "",
        "tone": "professional",
    }

    async def main():
        try:
            article = await write_article(keyword, company, word_count=1000)
            print(f"\nHeadline: {article.Headline}")
            print(f"Sections: {article.count_sections()}")
            print(f"FAQs: {article.count_faqs()}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    asyncio.run(main())
