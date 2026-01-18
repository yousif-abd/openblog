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
from typing import Optional, Dict, Any, List

# Add parent to path for shared imports
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from article_schema import ArticleOutput

try:
    from shared.gemini_client import GeminiClient
except ImportError:
    GeminiClient = None

# Legal article models for decision-centric generation
try:
    from stage2.legal_article_models import (
        ArticleOutline,
        SectionOutline,
        GeneratedSection,
        calculate_section_allocation,
    )
except ImportError:
    # Fallback for direct execution
    from legal_article_models import (
        ArticleOutline,
        SectionOutline,
        GeneratedSection,
        calculate_section_allocation,
    )

logger = logging.getLogger(__name__)

# Build field name mapping from lowercase/snake_case to ArticleOutput field names
_FIELD_NAME_MAPPING = {}
for field_name in ArticleOutput.model_fields.keys():
    # Map lowercase version to correct casing
    _FIELD_NAME_MAPPING[field_name.lower()] = field_name
    # Also map snake_case version (e.g., direct_answer -> Direct_Answer)
    snake_case = field_name.lower()
    _FIELD_NAME_MAPPING[snake_case] = field_name
    # Map version without underscores (e.g., directanswer -> Direct_Answer)
    _FIELD_NAME_MAPPING[snake_case.replace('_', '')] = field_name

# Prompts directory
PROMPTS_DIR = Path(__file__).parent / "prompts"


# =============================================================================
# Field Name Normalization
# =============================================================================

def _normalize_field_names(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Gemini API response field names to match ArticleOutput schema.

    Gemini may return lowercase field names (headline, teaser, etc.)
    but ArticleOutput expects capitalized names (Headline, Teaser, etc.).

    Args:
        result: Raw dictionary from Gemini API

    Returns:
        Dictionary with normalized field names matching ArticleOutput
    """
    normalized = {}

    for key, value in result.items():
        # Check if we have a mapping for this key
        normalized_key = _FIELD_NAME_MAPPING.get(key.lower(), key)

        # If the normalized key differs from original, log it for debugging
        if normalized_key != key:
            logger.debug(f"Normalized field name: {key} -> {normalized_key}")

        normalized[normalized_key] = value

    return normalized


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
    legal_context: Optional[Dict[str, Any]] = None,
    use_decision_centric: bool = True,
) -> ArticleOutput:
    """
    Generate a complete blog article using Gemini.

    Uses shared GeminiClient for consistency.
    Supports legal mode for German law firm content.

    Args:
        keyword: Primary SEO keyword
        company_context: Company info dict (from Stage 1)
        word_count: Target word count
        language: Article language code (e.g., "en", "de", "es")
        country: Target country/region for localization (e.g., "United States", "Germany")
        batch_instructions: Batch-level instructions (applies to all articles)
        keyword_instructions: Keyword-level instructions (adds to batch instructions)
        api_key: Gemini API key (falls back to env var)
        legal_context: Optional LegalContext dict from Stage 1 (enables legal mode)
        use_decision_centric: Use two-phase decision-centric approach for legal articles (default True)

    Returns:
        ArticleOutput with all fields populated (including legal fields if legal_context provided)

    Raises:
        ValueError: If no API key
        Exception: If Gemini call fails
    """
    logger.info(f"Writing article for: {keyword} ({language}/{country})")

    # Use decision-centric approach for legal articles with court decisions
    if use_decision_centric and legal_context and legal_context.get("court_decisions"):
        logger.info("Using decision-centric two-phase generation for legal article")
        article, _ = await write_legal_article_decision_centric(
            keyword=keyword,
            company_context=company_context,
            legal_context=legal_context,
            word_count=word_count,
            api_key=api_key,
        )
        return article

    # Log Beck-Online data usage
    _log_legal_context_usage(legal_context)

    try:
        # Use shared GeminiClient
        if GeminiClient is None:
            raise ImportError("shared.gemini_client not available")

        client = GeminiClient(api_key=api_key)

        # Detect legal mode
        is_legal_mode = legal_context is not None
        if is_legal_mode:
            logger.info(f"Legal mode enabled: rechtsgebiet={legal_context.get('rechtsgebiet', 'Unknown')}")

        # Load prompts (legal-specific or standard)
        if is_legal_mode:
            # For legal mode, format system instruction with legal context
            system_instruction = _format_legal_system_instruction(legal_context)
            user_prompt_template = _get_legal_user_prompt()
        else:
            system_instruction = get_system_instruction()
            user_prompt_template = get_user_prompt()

        # Build company context string
        company_str = _format_company_context(company_context)

        # Build custom instructions section (batch + keyword combined)
        custom_instructions_section = _build_custom_instructions(batch_instructions, keyword_instructions)

        # Build prompt with KeyError handling
        try:
            if is_legal_mode:
                prompt = _build_legal_prompt(
                    user_prompt_template,
                    keyword,
                    legal_context,
                    company_str,
                    word_count,
                    language,
                    country,
                )
            else:
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
        # Note: Cannot use generate_with_schema() because ArticleOutput has additionalProperties
        # which Gemini API doesn't support. Instead, rely on detailed prompt instructions.
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

        # Normalize field names (Gemini may return lowercase, but ArticleOutput expects capitalized)
        result = _normalize_field_names(result)

        # Always use grounding sources (real URLs from Google Search) instead of AI-generated ones
        # AI tends to hallucinate URLs that look real but return 404/403
        if "_grounding_sources" in result:
            grounding_sources = result.pop("_grounding_sources")
            if grounding_sources:
                ai_sources = result.get("Sources", [])
                result["Sources"] = grounding_sources
                logger.info(f"Using {len(grounding_sources)} grounding sources (replaced {len(ai_sources) if ai_sources else 0} AI-generated)")

        logger.info(f"Article generated: {result.get('Headline', 'Unknown')[:50]}...")

        # Populate legal fields if in legal mode
        if is_legal_mode and legal_context:
            if "rechtsgebiet" not in result or not result["rechtsgebiet"]:
                result["rechtsgebiet"] = legal_context.get("rechtsgebiet")
            if "stand_der_rechtsprechung" not in result or not result["stand_der_rechtsprechung"]:
                result["stand_der_rechtsprechung"] = legal_context.get("stand_der_rechtsprechung")
            if "legal_disclaimer" not in result or not result["legal_disclaimer"]:
                result["legal_disclaimer"] = legal_context.get("disclaimer_template", "")
            logger.info(f"Legal fields populated: rechtsgebiet={result.get('rechtsgebiet')}")

        return ArticleOutput(**result)

    except Exception as e:
        logger.error(f"Blog generation failed: {e}")
        raise


def _format_company_context(context: Dict[str, Any]) -> str:
    """
    Format company context dict into readable string for Gemini prompt.

    Includes full voice persona, pain points, value propositions, and competitors
    to guide content generation aligned with brand voice.
    """
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
            lines.append(f"Products/Services: {', '.join(str(p) for p in products)}")
        else:
            lines.append(f"Products/Services: {products}")

    # Add pain points - helps content address real customer problems
    pain_points = context.get('pain_points', [])
    if pain_points:
        if isinstance(pain_points, list):
            lines.append(f"Customer Pain Points: {'; '.join(str(p) for p in pain_points)}")
        else:
            lines.append(f"Customer Pain Points: {pain_points}")

    # Add value propositions - helps frame solutions and CTAs
    value_props = context.get('value_propositions', [])
    if value_props:
        if isinstance(value_props, list):
            lines.append(f"Value Propositions: {'; '.join(str(v) for v in value_props)}")
        else:
            lines.append(f"Value Propositions: {value_props}")

    # Add competitors to AVOID mentioning
    competitors = context.get('competitors', [])
    if competitors:
        if isinstance(competitors, list):
            lines.append(f"COMPETITORS (NEVER mention these): {', '.join(str(c) for c in competitors)}")
        else:
            lines.append(f"COMPETITORS (NEVER mention these): {competitors}")

    # Add use cases if available
    use_cases = context.get('use_cases', [])
    if use_cases:
        if isinstance(use_cases, list):
            lines.append(f"Common Use Cases: {'; '.join(str(u) for u in use_cases)}")
        else:
            lines.append(f"Common Use Cases: {use_cases}")

    # Full voice persona section
    voice = context.get('voice_persona', {})
    if voice:
        lines.append("")
        lines.append("=== VOICE & WRITING STYLE ===")

        # ICP profile - who we're writing for
        icp = voice.get('icp_profile', '')
        if icp:
            lines.append(f"Ideal Reader: {icp}")

        voice_style = voice.get('voice_style', '')
        if voice_style:
            lines.append(f"Voice Style: {voice_style}")

        # Language style details
        lang_style = voice.get('language_style', {})
        if lang_style:
            style_parts = []
            if lang_style.get('formality'):
                style_parts.append(f"Formality: {lang_style['formality']}")
            if lang_style.get('complexity'):
                style_parts.append(f"Complexity: {lang_style['complexity']}")
            if lang_style.get('perspective'):
                style_parts.append(f"Perspective: {lang_style['perspective']}")
            if lang_style.get('sentence_length'):
                style_parts.append(f"Sentences: {lang_style['sentence_length']}")
            if style_parts:
                lines.append(f"Language Style: {', '.join(style_parts)}")

        # DO list - behaviors that resonate
        do_list = voice.get('do_list', [])
        if do_list:
            lines.append(f"DO: {'; '.join(str(d) for d in do_list[:5])}")

        # DON'T list - anti-patterns to avoid
        dont_list = voice.get('dont_list', [])
        if dont_list:
            lines.append(f"DON'T: {'; '.join(str(d) for d in dont_list[:5])}")

        # Banned words - critical for avoiding AI-sounding phrases
        banned = voice.get('banned_words', [])
        if banned:
            lines.append(f"BANNED WORDS (never use): {', '.join(str(b) for b in banned[:10])}")

        # Technical terms to use correctly
        tech_terms = voice.get('technical_terms', [])
        if tech_terms:
            lines.append(f"Technical Terms (use correctly): {', '.join(str(t) for t in tech_terms[:8])}")

        # Power words that resonate
        power_words = voice.get('power_words', [])
        if power_words:
            lines.append(f"Power Words: {', '.join(str(p) for p in power_words[:8])}")

        # Example phrases for tone reference
        examples = voice.get('example_phrases', [])
        if examples:
            lines.append(f"Example Phrases: \"{'\"; \"'.join(str(e) for e in examples[:3])}\"")

        # CTA phrases
        cta_phrases = voice.get('cta_phrases', [])
        if cta_phrases:
            lines.append(f"CTA Style: {'; '.join(str(c) for c in cta_phrases[:3])}")

        # Headline patterns
        headline_patterns = voice.get('headline_patterns', [])
        if headline_patterns:
            lines.append(f"Headline Patterns: {'; '.join(str(h) for h in headline_patterns[:3])}")

        # Content structure hints
        structure = voice.get('content_structure_pattern', '')
        if structure:
            lines.append(f"Preferred Structure: {structure}")

        # Formatting preferences
        format_hints = []
        if voice.get('uses_questions'):
            format_hints.append("Use rhetorical questions")
        if voice.get('uses_lists'):
            format_hints.append("Use bullet/numbered lists")
        if voice.get('uses_statistics'):
            format_hints.append("Include data/statistics")
        if voice.get('first_person_usage'):
            format_hints.append(f"First person: {voice['first_person_usage']}")
        if format_hints:
            lines.append(f"Formatting: {', '.join(format_hints)}")

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
# Legal Mode Functions
# =============================================================================

def _format_legal_system_instruction(legal_context: Dict[str, Any]) -> str:
    """Format legal-specific system instruction with legal context."""
    template = _load_prompt("system_instruction_legal.txt", "")
    if not template:
        logger.error("Legal system instruction not found, using standard")
        return get_system_instruction()

    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rechtsgebiet = legal_context.get("rechtsgebiet", "Arbeitsrecht")
    court_decisions = legal_context.get("court_decisions", [])
    decisions_summary = _format_court_decisions(court_decisions)

    try:
        return template.format(
            current_date=current_date,
            rechtsgebiet=rechtsgebiet,
            court_decisions_summary=decisions_summary,
        )
    except KeyError as e:
        logger.error(f"Legal system instruction template has unknown placeholder: {e}")
        # Fallback with manual replacement
        result = template
        result = result.replace("{current_date}", current_date)
        result = result.replace("{rechtsgebiet}", rechtsgebiet)
        result = result.replace("{court_decisions_summary}", decisions_summary)
        return result


def _get_legal_user_prompt() -> str:
    """Get legal-specific user prompt template."""
    prompt = _load_prompt("user_prompt_legal.txt", "")
    if not prompt or not prompt.strip():
        logger.error("Legal user prompt not found, using standard")
        return get_user_prompt()
    return prompt


def _build_legal_prompt(
    template: str,
    keyword: str,
    legal_context: Dict[str, Any],
    company_str: str,
    word_count: int,
    language: str,
    country: str,
) -> str:
    """
    Build prompt for legal article generation.

    Args:
        template: Legal user prompt template
        keyword: Article keyword
        legal_context: LegalContext dict from Stage 1
        company_str: Formatted company context
        word_count: Target word count
        language: Article language
        country: Target country

    Returns:
        Formatted prompt string
    """
    # Format court decisions for prompt injection
    court_decisions = legal_context.get("court_decisions", [])
    decisions_summary = _format_court_decisions(court_decisions)

    # Extract rechtsgebiet
    rechtsgebiet = legal_context.get("rechtsgebiet", "Arbeitsrecht")

    # Extract disclaimer
    disclaimer_template = legal_context.get("disclaimer_template", "")

    # Extract voice persona from company context
    voice_persona = "Professionell und verständlich"

    # Extract target audience
    target_audience = "Mandanten und rechtlich Interessierte"

    # Build prompt
    try:
        return template.format(
            keyword=keyword,
            rechtsgebiet=rechtsgebiet,
            word_count=word_count,
            target_audience=target_audience,
            court_decisions_summary=decisions_summary,
            disclaimer_template=disclaimer_template,
            company_name=company_str.split("\n")[0].replace("Company: ", "") if company_str else "Braun & Kollegen",
            company_description="Rechtsanwaltskanzlei",
            voice_persona=voice_persona,
        )
    except KeyError as e:
        logger.error(f"Legal prompt template missing placeholder: {e}")
        # Fallback with minimal substitution
        result = template
        result = result.replace("{keyword}", keyword)
        result = result.replace("{rechtsgebiet}", rechtsgebiet)
        result = result.replace("{word_count}", str(word_count))
        result = result.replace("{court_decisions_summary}", decisions_summary)
        result = result.replace("{disclaimer_template}", disclaimer_template)
        return result


def _format_court_decisions(court_decisions: list) -> str:
    """
    Format court decisions for prompt injection.

    Args:
        court_decisions: List of CourtDecision dicts

    Returns:
        Formatted string with all decisions
    """
    if not court_decisions:
        return "Keine Gerichtsentscheidungen bereitgestellt."

    parts = []
    for i, decision in enumerate(court_decisions, 1):
        normen = ", ".join(decision.get("relevante_normen", [])) if decision.get("relevante_normen") else "keine Normen angegeben"

        # Format datum from ISO to German format
        datum = decision.get("datum", "")
        if datum and len(datum) == 10:  # ISO format YYYY-MM-DD
            try:
                parts_date = datum.split("-")
                datum_german = f"{parts_date[2]}.{parts_date[1]}.{parts_date[0]}"
            except:
                datum_german = datum
        else:
            datum_german = datum

        parts.append(
            f"{i}. {decision.get('gericht', 'Unbekannt')}, Urt. v. {datum_german} – {decision.get('aktenzeichen', 'N/A')}\n"
            f"   Leitsatz: {decision.get('leitsatz', 'N/A')}\n"
            f"   Relevante Normen: {normen}\n"
            f"   URL: {decision.get('url', 'N/A')}"
        )

    return "\n\n".join(parts)


def _log_legal_context_usage(legal_context: Optional[dict]) -> None:
    """
    Log which Beck-Online court decisions are being used in article generation.

    Args:
        legal_context: Legal context with court_decisions list
    """
    import logging
    logger = logging.getLogger(__name__)

    if not legal_context:
        return

    court_decisions = legal_context.get("court_decisions", [])

    if court_decisions:
        logger.info("=" * 80)
        logger.info("BECK-ONLINE DATA USED IN ARTICLE GENERATION")
        logger.info("=" * 80)
        logger.info(f"  Injecting {len(court_decisions)} court decision(s) into article prompt:")
        for i, decision in enumerate(court_decisions, 1):
            aktenzeichen = decision.get("aktenzeichen", "Unknown")
            gericht = decision.get("gericht", "Unknown")
            datum = decision.get("datum", "Unknown")
            leitsatz = decision.get("leitsatz", "")
            logger.info(f"    {i}. {gericht} {aktenzeichen} ({datum})")
            if leitsatz:
                logger.info(f"       Leitsatz: {leitsatz[:80]}...")
        logger.info("=" * 80)
    else:
        logger.info("Beck-Online: No court decisions available for article generation")


# =============================================================================
# Decision-Centric Legal Article Generation (Two-Phase)
# =============================================================================

async def write_legal_article_decision_centric(
    keyword: str,
    company_context: Dict[str, Any],
    legal_context: Dict[str, Any],
    word_count: int = 2000,
    api_key: Optional[str] = None,
) -> tuple[ArticleOutput, int]:
    """
    Generate a legal article using decision-centric two-phase approach.

    Phase 1: Generate structured outline mapping sections to court decisions
    Phase 2: Generate each section with type-specific constraints

    This approach ensures:
    - Every provided court decision is cited in exactly one section
    - No unsupported legal claims (verified by section type)
    - Reduced Stage 2.5 verification burden

    Args:
        keyword: Primary SEO keyword
        company_context: Company info dict
        legal_context: LegalContext dict with court_decisions
        word_count: Target word count
        api_key: Gemini API key

    Returns:
        Tuple of (ArticleOutput, ai_calls_count)
    """
    logger.info(f"Starting decision-centric generation for: {keyword}")

    client = GeminiClient(api_key=api_key)
    ai_calls = 0

    # Extract court decisions
    court_decisions = legal_context.get("court_decisions", [])
    rechtsgebiet = legal_context.get("rechtsgebiet", "Arbeitsrecht")

    if not court_decisions:
        logger.warning("No court decisions provided - falling back to standard legal generation")
        # Fall back to standard approach
        article = await write_article(
            keyword=keyword,
            company_context=company_context,
            word_count=word_count,
            legal_context=legal_context,
            api_key=api_key,
        )
        return article, 1

    logger.info(f"Decision-centric mode: {len(court_decisions)} court decisions available")

    # ==========================================================================
    # PHASE 1: Generate Structured Outline
    # ==========================================================================

    logger.info("Phase 1: Generating structured outline...")

    outline = await _generate_legal_outline(
        client=client,
        keyword=keyword,
        rechtsgebiet=rechtsgebiet,
        court_decisions=court_decisions,
    )
    ai_calls += 1

    logger.info(f"Outline generated: {len(outline.target_sections)} sections")
    for section in outline.target_sections:
        logger.info(f"  - {section.section_id}: {section.section_type} "
                   f"({section.anchored_decision_aktenzeichen or 'no anchor'})")

    # ==========================================================================
    # PHASE 2: Generate Section Content
    # ==========================================================================

    logger.info("Phase 2: Generating section content...")

    sections_content = {}
    decisions_by_az = {d.get("aktenzeichen"): d for d in court_decisions}

    for section in outline.target_sections:
        logger.info(f"  Generating {section.section_id} ({section.section_type})...")

        if section.section_type == "decision_anchor":
            decision = decisions_by_az.get(section.anchored_decision_aktenzeichen)
            if not decision:
                logger.warning(f"Decision {section.anchored_decision_aktenzeichen} not found, using first available")
                decision = court_decisions[0]

            content = await _generate_decision_anchor_section(
                client=client,
                section=section,
                decision=decision,
            )
        elif section.section_type == "context":
            content = await _generate_context_section(
                client=client,
                section=section,
            )
        else:  # practical_advice
            content = await _generate_practical_section(
                client=client,
                section=section,
            )

        sections_content[section.section_id] = {
            "title": section.title,
            "content": content,
            "type": section.section_type,
        }
        ai_calls += 1

    # ==========================================================================
    # PHASE 3: Generate Supporting Content (FAQs, Intro, Meta)
    # ==========================================================================

    logger.info("Phase 3: Generating supporting content...")

    supporting = await _generate_supporting_content(
        client=client,
        keyword=keyword,
        rechtsgebiet=rechtsgebiet,
        outline=outline,
        court_decisions=court_decisions,
        legal_context=legal_context,
    )
    ai_calls += 1

    # ==========================================================================
    # ASSEMBLE FINAL ARTICLE
    # ==========================================================================

    logger.info("Assembling final article...")

    article_dict = _assemble_article(
        outline=outline,
        sections_content=sections_content,
        supporting=supporting,
        legal_context=legal_context,
        court_decisions=court_decisions,
    )

    # Normalize field names
    article_dict = _normalize_field_names(article_dict)

    logger.info(f"Decision-centric generation complete: {ai_calls} AI calls")

    return ArticleOutput(**article_dict), ai_calls


async def _generate_legal_outline(
    client: GeminiClient,
    keyword: str,
    rechtsgebiet: str,
    court_decisions: List[Dict[str, Any]],
) -> ArticleOutline:
    """
    Phase 1: Generate structured outline mapping sections to decisions.

    Args:
        client: GeminiClient instance
        keyword: Article keyword
        rechtsgebiet: Legal area
        court_decisions: List of court decision dicts

    Returns:
        ArticleOutline with section assignments
    """
    # Format court decisions for prompt
    decisions_summary = _format_court_decisions(court_decisions)

    # Load outline prompt
    prompt_template = _load_prompt("legal_outline.txt", "")
    if not prompt_template:
        raise ValueError("legal_outline.txt prompt not found")

    prompt = prompt_template.format(
        keyword=keyword,
        rechtsgebiet=rechtsgebiet,
        court_decisions_summary=decisions_summary,
    )

    # Define schema for outline
    outline_schema = {
        "type": "object",
        "properties": {
            "headline": {"type": "string"},
            "teaser": {"type": "string"},
            "direct_answer": {"type": "string"},
            "intro_brief": {"type": "string"},
            "target_sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "section_id": {"type": "string"},
                        "title": {"type": "string"},
                        "section_type": {"type": "string", "enum": ["decision_anchor", "context", "practical_advice"]},
                        "anchored_decision_aktenzeichen": {"type": "string"},
                        "content_brief": {"type": "string"},
                        "relevant_statutes": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["section_id", "title", "section_type", "content_brief"]
                }
            },
            "faq_topics": {"type": "array", "items": {"type": "string"}},
            "key_takeaway_topics": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["headline", "teaser", "direct_answer", "intro_brief", "target_sections"]
    }

    result = await client.generate_with_schema(
        prompt=prompt,
        response_schema=outline_schema,
        temperature=0.3,
    )

    return ArticleOutline(**result)


async def _generate_decision_anchor_section(
    client: GeminiClient,
    section: SectionOutline,
    decision: Dict[str, Any],
) -> str:
    """
    Generate a section anchored to a specific court decision.

    The section MUST cite and explain the assigned decision.

    Args:
        client: GeminiClient instance
        section: Section outline with assignment
        decision: Court decision dict to anchor

    Returns:
        HTML content for the section
    """
    prompt_template = _load_prompt("legal_section_decision_anchor.txt", "")
    if not prompt_template:
        raise ValueError("legal_section_decision_anchor.txt prompt not found")

    # Format decision date to German
    datum = decision.get("datum", "")
    if datum and len(datum) == 10:
        try:
            parts = datum.split("-")
            datum_german = f"{parts[2]}.{parts[1]}.{parts[0]}"
        except:
            datum_german = datum
    else:
        datum_german = datum

    normen = ", ".join(decision.get("relevante_normen", [])) or "keine Normen"

    prompt = prompt_template.format(
        section_title=section.title,
        content_brief=section.content_brief,
        relevant_statutes=", ".join(section.relevant_statutes) or "keine",
        decision_gericht=decision.get("gericht", "Unbekannt"),
        decision_aktenzeichen=decision.get("aktenzeichen", ""),
        decision_datum=datum_german,
        decision_leitsatz=decision.get("leitsatz", ""),
        decision_normen=normen,
    )

    result = await client.generate(
        prompt=prompt,
        use_url_context=False,
        use_google_search=False,
        json_output=False,
        temperature=0.3,
        max_tokens=2048,
    )

    return result.strip()


async def _generate_context_section(
    client: GeminiClient,
    section: SectionOutline,
) -> str:
    """
    Generate a context section with statutory references only.

    NO legal claims requiring court decisions allowed.

    Args:
        client: GeminiClient instance
        section: Section outline

    Returns:
        HTML content for the section
    """
    prompt_template = _load_prompt("legal_section_context.txt", "")
    if not prompt_template:
        raise ValueError("legal_section_context.txt prompt not found")

    prompt = prompt_template.format(
        section_title=section.title,
        content_brief=section.content_brief,
        relevant_statutes=", ".join(section.relevant_statutes) or "keine",
    )

    result = await client.generate(
        prompt=prompt,
        use_url_context=False,
        use_google_search=False,
        json_output=False,
        temperature=0.3,
        max_tokens=2048,
    )

    return result.strip()


async def _generate_practical_section(
    client: GeminiClient,
    section: SectionOutline,
) -> str:
    """
    Generate a practical advice section with no legal claims.

    Tips and recommendations only.

    Args:
        client: GeminiClient instance
        section: Section outline

    Returns:
        HTML content for the section
    """
    prompt_template = _load_prompt("legal_section_practical.txt", "")
    if not prompt_template:
        raise ValueError("legal_section_practical.txt prompt not found")

    prompt = prompt_template.format(
        section_title=section.title,
        content_brief=section.content_brief,
    )

    result = await client.generate(
        prompt=prompt,
        use_url_context=False,
        use_google_search=False,
        json_output=False,
        temperature=0.4,  # Slightly higher for practical tips
        max_tokens=2048,
    )

    return result.strip()


async def _generate_supporting_content(
    client: GeminiClient,
    keyword: str,
    rechtsgebiet: str,
    outline: ArticleOutline,
    court_decisions: List[Dict[str, Any]],
    legal_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate supporting content: intro, FAQs, meta tags, key takeaways.

    Args:
        client: GeminiClient instance
        keyword: Article keyword
        rechtsgebiet: Legal area
        outline: Generated article outline
        court_decisions: Court decisions for citations
        legal_context: Full legal context

    Returns:
        Dict with intro, faqs, meta, takeaways
    """
    # Format decisions for prompt
    decisions_summary = _format_court_decisions(court_decisions)
    disclaimer = legal_context.get("disclaimer_template", "")

    prompt = f"""Erstellen Sie unterstützende Inhalte für einen deutschen Rechtsartikel.

KEYWORD: {keyword}
RECHTSGEBIET: {rechtsgebiet}

ARTIKEL-HEADLINE: {outline.headline}
ARTIKEL-TEASER: {outline.teaser}
DIREKTE ANTWORT: {outline.direct_answer}

INTRO-KURZBESCHREIBUNG: {outline.intro_brief}

FAQ-THEMEN: {', '.join(outline.faq_topics)}
KEY-TAKEAWAY-THEMEN: {', '.join(outline.key_takeaway_topics)}

VERFÜGBARE GERICHTSENTSCHEIDUNGEN (für Zitate in FAQs):
{decisions_summary}

AUFGABE:
Erstellen Sie die folgenden Felder als JSON:

1. Intro (80-120 Wörter, HTML mit <p>-Tags)
2. Meta_Title (max 55 Zeichen, SEO-optimiert)
3. Meta_Description (max 160 Zeichen, mit CTA)
4. 4 FAQs (faq_01_question, faq_01_answer, etc.) - HTML in Antworten
5. 3 Key Takeaways (key_takeaway_01, key_takeaway_02, key_takeaway_03)
6. 4 PAA (People Also Ask) - paa_01_question, paa_01_answer, etc.
7. TLDR (2-3 Sätze Zusammenfassung)

WICHTIG:
- FAQs können Gerichtsentscheidungen zitieren (im korrekten Format)
- Key Takeaways sollten die wichtigsten Punkte zusammenfassen
- Meta-Felder SEO-optimiert mit Keyword
- Alle Texte auf Deutsch

Geben Sie NUR das JSON zurück.
"""

    schema = {
        "type": "object",
        "properties": {
            "Intro": {"type": "string"},
            "Meta_Title": {"type": "string"},
            "Meta_Description": {"type": "string"},
            "faq_01_question": {"type": "string"},
            "faq_01_answer": {"type": "string"},
            "faq_02_question": {"type": "string"},
            "faq_02_answer": {"type": "string"},
            "faq_03_question": {"type": "string"},
            "faq_03_answer": {"type": "string"},
            "faq_04_question": {"type": "string"},
            "faq_04_answer": {"type": "string"},
            "paa_01_question": {"type": "string"},
            "paa_01_answer": {"type": "string"},
            "paa_02_question": {"type": "string"},
            "paa_02_answer": {"type": "string"},
            "paa_03_question": {"type": "string"},
            "paa_03_answer": {"type": "string"},
            "paa_04_question": {"type": "string"},
            "paa_04_answer": {"type": "string"},
            "key_takeaway_01": {"type": "string"},
            "key_takeaway_02": {"type": "string"},
            "key_takeaway_03": {"type": "string"},
            "TLDR": {"type": "string"},
        },
        "required": ["Intro", "Meta_Title", "Meta_Description"]
    }

    result = await client.generate_with_schema(
        prompt=prompt,
        response_schema=schema,
        temperature=0.3,
    )

    return result


def _assemble_article(
    outline: ArticleOutline,
    sections_content: Dict[str, Dict[str, Any]],
    supporting: Dict[str, Any],
    legal_context: Dict[str, Any],
    court_decisions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Assemble the final ArticleOutput dict from all generated components.

    Args:
        outline: Generated outline
        sections_content: Dict of section_id -> {title, content, type}
        supporting: Supporting content (intro, faqs, meta, etc.)
        legal_context: Legal context for metadata
        court_decisions: Court decisions for rechtliche_grundlagen

    Returns:
        Complete ArticleOutput dict
    """
    article = {
        "Headline": outline.headline,
        "Teaser": outline.teaser,
        "Direct_Answer": outline.direct_answer,
        "Intro": supporting.get("Intro", ""),
        "Meta_Title": supporting.get("Meta_Title", ""),
        "Meta_Description": supporting.get("Meta_Description", ""),
        "TLDR": supporting.get("TLDR", ""),
    }

    # Add sections
    for i, section in enumerate(outline.target_sections, 1):
        section_id = f"section_{i:02d}"
        content_data = sections_content.get(section.section_id, {})

        article[f"section_{i:02d}_title"] = content_data.get("title", section.title)
        article[f"section_{i:02d}_content"] = content_data.get("content", "")

        # Store section type as metadata for Stage 2.5 verification
        article[f"_section_{i:02d}_type"] = content_data.get("type", "unknown")

    # Add FAQs
    for i in range(1, 5):
        article[f"faq_{i:02d}_question"] = supporting.get(f"faq_{i:02d}_question", "")
        article[f"faq_{i:02d}_answer"] = supporting.get(f"faq_{i:02d}_answer", "")

    # Add PAAs
    for i in range(1, 5):
        article[f"paa_{i:02d}_question"] = supporting.get(f"paa_{i:02d}_question", "")
        article[f"paa_{i:02d}_answer"] = supporting.get(f"paa_{i:02d}_answer", "")

    # Add key takeaways
    article["key_takeaway_01"] = supporting.get("key_takeaway_01", "")
    article["key_takeaway_02"] = supporting.get("key_takeaway_02", "")
    article["key_takeaway_03"] = supporting.get("key_takeaway_03", "")

    # Add legal metadata
    article["rechtsgebiet"] = legal_context.get("rechtsgebiet", "")
    article["stand_der_rechtsprechung"] = legal_context.get("stand_der_rechtsprechung", "")
    article["legal_disclaimer"] = legal_context.get("disclaimer_template", "")

    # Build rechtliche_grundlagen from court decisions
    rechtliche_grundlagen = []
    for decision in court_decisions:
        datum = decision.get("datum", "")
        if datum and len(datum) == 10:
            try:
                parts = datum.split("-")
                datum_german = f"{parts[2]}.{parts[1]}.{parts[0]}"
            except:
                datum_german = datum
        else:
            datum_german = datum

        citation = f"{decision.get('gericht', 'Unbekannt')}, Urt. v. {datum_german} – {decision.get('aktenzeichen', '')}"
        rechtliche_grundlagen.append(citation)

    article["rechtliche_grundlagen"] = rechtliche_grundlagen

    # Build sources from court decisions
    sources = []
    for decision in court_decisions:
        sources.append({
            "title": f"{decision.get('gericht', '')} {decision.get('aktenzeichen', '')}",
            "url": decision.get("url", ""),
        })
    article["Sources"] = sources

    # Initialize empty fields
    article["Subtitle"] = ""
    article["Search_Queries"] = f"Recherche: {outline.headline}"

    # Store section types mapping for Stage 2.5
    section_types = {}
    for i, section in enumerate(outline.target_sections, 1):
        section_types[f"section_{i:02d}"] = section.section_type
    article["section_types_metadata"] = section_types

    return article


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
        legal_context: Optional[Dict[str, Any]] = None,
        use_decision_centric: bool = True,
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
            legal_context=legal_context,
            use_decision_centric=use_decision_centric,
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
