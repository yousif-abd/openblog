"""
Legal research orchestrator for Stage 1.

Coordinates legal research via two modes:
1. Mock mode: Uses mock_legal_data.py (for development/testing)
2. Beck-Online mode: Uses browser_agent.py + beck-online.beck.de (when credentials available)

Called by stage_1.py when enable_legal_research=True.
"""

import logging
import sys
from pathlib import Path
from typing import List

# Add stage1 to path for imports
stage1_path = Path(__file__).parent
if str(stage1_path) not in sys.path:
    sys.path.insert(0, str(stage1_path))

from legal_models import LegalContext
from mock_legal_data import generate_mock_legal_context

logger = logging.getLogger(__name__)


async def conduct_legal_research(
    keywords: List[str],
    rechtsgebiet: str = "Arbeitsrecht",
    use_mock: bool = True
) -> LegalContext:
    """
    Conduct legal research for batch of keywords.

    Orchestrates between mock data and real Beck-Online research based on mode.

    Args:
        keywords: List of article keywords (may be strings or dicts)
        rechtsgebiet: German legal area (Arbeitsrecht, Mietrecht, etc.)
        use_mock: If True, use mock data; if False, use Beck-Online browser agent

    Returns:
        LegalContext with court decisions, disclaimer, and metadata

    Raises:
        Exception: If Beck-Online mode fails and cannot fall back to mock data

    Example:
        >>> context = await conduct_legal_research(
        ...     keywords=["Kündigung", "Kündigungsschutz"],
        ...     rechtsgebiet="Arbeitsrecht",
        ...     use_mock=True
        ... )
        >>> len(context.court_decisions)
        4
    """
    logger.info(f"Starting legal research: rechtsgebiet={rechtsgebiet}, keywords={keywords}, use_mock={use_mock}")

    if use_mock:
        logger.info("Using mock legal data (development mode)")
        context = await generate_mock_legal_context(
            keywords=keywords,
            rechtsgebiet=rechtsgebiet
        )
    else:
        logger.info("Using Beck-Online browser agent (production mode)")
        try:
            from browser_agent import research_via_beck_online
            context = await research_via_beck_online(
                keywords=keywords,
                rechtsgebiet=rechtsgebiet
            )
        except ImportError as e:
            logger.error(f"Beck-Online scraper not available: {e}")
            logger.warning("Falling back to mock data")
            context = await generate_mock_legal_context(
                keywords=keywords,
                rechtsgebiet=rechtsgebiet
            )
        except Exception as e:
            logger.error(f"Beck-Online scraping failed: {e}")
            logger.warning("Falling back to mock data")
            context = await generate_mock_legal_context(
                keywords=keywords,
                rechtsgebiet=rechtsgebiet
            )

    # Enhanced logging: Beck-Online Research Summary
    logger.info("=" * 80)
    logger.info("BECK-ONLINE RESEARCH SUMMARY")
    logger.info("=" * 80)
    logger.info(f"  Rechtsgebiet: {context.rechtsgebiet}")
    logger.info(f"  Court Decisions Found: {len(context.court_decisions)}")
    if context.court_decisions:
        for i, decision in enumerate(context.court_decisions, 1):
            logger.info(f"    {i}. {decision.gericht} {decision.aktenzeichen} ({decision.datum})")
            if decision.leitsatz:
                logger.info(f"       Leitsatz: {decision.leitsatz[:80]}...")
    else:
        logger.info("    (No court decisions available)")
    logger.info(f"  Research Date: {context.stand_der_rechtsprechung}")
    logger.info(f"  Keywords Researched: {', '.join(context.keywords_researched)}")
    logger.info("=" * 80)

    return context


def format_decisions_for_prompt(legal_context: LegalContext) -> str:
    """
    Format court decisions for prompt injection in Stage 2.

    Args:
        legal_context: LegalContext from Stage 1 research

    Returns:
        Formatted string with all decisions for article generation

    Example:
        >>> formatted = format_decisions_for_prompt(context)
        >>> print(formatted)
        BAG, Urt. v. 12.05.2024 – 6 AZR 148/22
        Leitsatz: Die Kündigung eines Arbeitsverhältnisses...
        Relevante Normen: § 623 BGB
        ...
    """
    return legal_context.get_decisions_summary()


def format_decisions_for_verification(court_decisions: List) -> str:
    """
    Format court decisions for Stage 2.5 verification prompt.

    Args:
        court_decisions: List of CourtDecision objects

    Returns:
        Formatted string optimized for verification prompt

    Example:
        >>> formatted = format_decisions_for_verification(context.court_decisions)
    """
    parts = []
    for i, decision in enumerate(court_decisions, 1):
        normen = ", ".join(decision.relevante_normen) if decision.relevante_normen else "keine Normen angegeben"
        parts.append(
            f"Entscheidung {i}:\n"
            f"  Gericht: {decision.gericht}\n"
            f"  Aktenzeichen: {decision.aktenzeichen}\n"
            f"  Datum: {decision.datum}\n"
            f"  Leitsatz: {decision.leitsatz}\n"
            f"  Normen: {normen}\n"
            f"  Rechtsgebiet: {decision.rechtsgebiet}"
        )
    return "\n\n".join(parts)
