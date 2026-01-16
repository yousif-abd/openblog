"""
Legal Claim Verification Logic

Extracts legal claims from article content and matches them against
provided court decisions from Stage 1 research.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.gemini_client import GeminiClient
from shared.prompt_loader import load_prompt
from stage2_5.stage2_5_models import LegalClaim

logger = logging.getLogger(__name__)


async def verify_legal_claims(
    article: Dict[str, Any],
    legal_context: Optional[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[LegalClaim], int]:
    """
    Extract legal claims from article and verify against LegalContext.

    Process:
    1. Extract all legal claims from content sections using Gemini
    2. Match claims to court decisions in LegalContext
    3. Flag unsupported claims in article.legal_issues
    4. Update article.legal_verification_status

    Args:
        article: ArticleOutput dict from Stage 2
        legal_context: LegalContext dict from Stage 1 (or None)

    Returns:
        Tuple of (modified_article, legal_claims_list, ai_calls)
        - modified_article has legal_verification_status updated
        - legal_claims_list contains all extracted claims with verification results
        - ai_calls is 1 if verification ran, 0 if skipped

    Example:
        >>> article, claims, ai_calls = await verify_legal_claims(
        ...     article={"Headline": "...", "section_01_content": "..."},
        ...     legal_context={"court_decisions": [...], "rechtsgebiet": "Arbeitsrecht"}
        ... )
        >>> article["legal_verification_status"]
        'verified'
        >>> len([c for c in claims if not c.supported])
        0
    """
    # Skip verification if no legal context
    if not legal_context:
        logger.info("No legal context provided - skipping verification")
        article["legal_verification_status"] = "skipped"
        return article, [], 0

    logger.info("Starting legal claim verification...")

    # Extract article content for verification
    content = _extract_article_content(article)

    # Format court decisions for prompt
    court_decisions = legal_context.get("court_decisions", [])
    decisions_summary = _format_decisions_for_verification(court_decisions)

    # Build verification prompt
    prompt_template = load_prompt("stage2_5", "legal_verification")
    prompt = prompt_template.format(
        content=content,
        court_decisions=decisions_summary
    )

    # Define verification schema
    verification_schema = {
        "type": "object",
        "properties": {
            "legal_claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim_text": {"type": "string"},
                        "field": {"type": "string"},
                        "cited_source": {"type": "string"},
                        "supported": {"type": "boolean"},
                        "matching_decision": {"type": "string"},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"]}
                    },
                    "required": ["claim_text", "field", "supported"]
                }
            }
        },
        "required": ["legal_claims"]
    }

    # Call Gemini with schema (no grounding needed - pure analysis)
    try:
        gemini_client = GeminiClient()
        result = await gemini_client.generate_with_schema(
            prompt=prompt,
            response_schema=verification_schema,
            temperature=0.2  # Low temperature for consistent verification
        )

        # Parse claims
        claims_data = result.get("legal_claims", [])
        claims = [LegalClaim(**claim) for claim in claims_data]

        logger.info(f"Extracted {len(claims)} legal claims")

        # Analyze results
        unsupported = [c for c in claims if not c.supported]
        supported = [c for c in claims if c.supported]

        logger.info(f"  Supported: {len(supported)}")
        logger.info(f"  Unsupported: {len(unsupported)}")

        # Update article metadata
        article["legal_issues"] = [c.claim_text for c in unsupported]
        article["legal_verification_status"] = "verified" if not unsupported else "issues_found"

        # Update rechtliche_grundlagen with matched decisions
        matched_decisions = [c.matching_decision for c in claims if c.matching_decision]
        if matched_decisions:
            article["rechtliche_grundlagen"] = list(set(matched_decisions))

        logger.info(f"Verification complete: status={article['legal_verification_status']}")

        return article, claims, 1  # 1 AI call

    except Exception as e:
        logger.error(f"Legal verification failed: {e}")
        article["legal_verification_status"] = "error"
        article["legal_issues"] = [f"Verification failed: {str(e)}"]
        return article, [], 0


def _extract_article_content(article: Dict[str, Any]) -> str:
    """
    Extract all text content from article for verification.

    Args:
        article: ArticleOutput dict

    Returns:
        Combined text from all content fields
    """
    content_fields = [
        "Headline", "Teaser", "Direct_Answer", "Intro",
        "section_01_title", "section_01_content",
        "section_02_title", "section_02_content",
        "section_03_title", "section_03_content",
        "section_04_title", "section_04_content",
        "section_05_title", "section_05_content",
        "section_06_title", "section_06_content",
        "section_07_title", "section_07_content",
    ]

    parts = []
    for field in content_fields:
        value = article.get(field, "")
        if value and value.strip():
            parts.append(f"[{field}]\n{value}\n")

    return "\n".join(parts)


def _format_decisions_for_verification(court_decisions: List[Dict[str, Any]]) -> str:
    """
    Format court decisions for verification prompt.

    Args:
        court_decisions: List of CourtDecision dicts

    Returns:
        Formatted string with all decisions for verification prompt
    """
    if not court_decisions:
        return "Keine Gerichtsentscheidungen verfügbar."

    parts = []
    for i, decision in enumerate(court_decisions, 1):
        # Extract fields with defaults
        gericht = decision.get("gericht", "Unbekannt")
        aktenzeichen = decision.get("aktenzeichen", "")
        datum = decision.get("datum", "")
        leitsatz = decision.get("leitsatz", "")
        normen = decision.get("relevante_normen", [])
        rechtsgebiet = decision.get("rechtsgebiet", "")

        # Format date to German format (DD.MM.YYYY)
        if datum and len(datum) == 10:  # ISO format YYYY-MM-DD
            try:
                year, month, day = datum.split("-")
                datum = f"{day}.{month}.{year}"
            except:
                pass  # Keep original if parsing fails

        normen_str = ", ".join(normen) if normen else "keine Normen angegeben"

        parts.append(
            f"Entscheidung {i}:\n"
            f"  Gericht: {gericht}\n"
            f"  Aktenzeichen: {aktenzeichen}\n"
            f"  Datum: {datum}\n"
            f"  Leitsatz: {leitsatz}\n"
            f"  Relevante Normen: {normen_str}\n"
            f"  Rechtsgebiet: {rechtsgebiet}"
        )

    return "\n\n".join(parts)
