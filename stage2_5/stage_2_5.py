"""
Stage 2.5: Legal Verification

Validates legal claims in generated articles against provided court decisions.
This stage runs after Stage 2 (blog generation) and before Stage 3 (quality check).

Micro-API Interface:
- Input: article (from Stage 2), legal_context (from Stage 1)
- Output: article with legal_verification_status and legal_issues populated
- AI Calls: 1 (Gemini with schema for claim extraction and verification)

Entry Points:
- run(input_dict) -> output_dict (async)
- run_sync(input_dict) -> output_dict (sync wrapper)
- run_from_json(input_json) -> output_json (JSON I/O)

Example Usage:
    >>> import asyncio
    >>> input_dict = {
    ...     "article": {...},  # ArticleOutput dict from Stage 2
    ...     "legal_context": {...}  # LegalContext dict from Stage 1
    ... }
    >>> output_dict = asyncio.run(run(input_dict))
    >>> print(output_dict["claims_extracted"])
    12
    >>> print(output_dict["claims_unsupported"])
    0
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stage2_5.stage2_5_models import Stage25Input, Stage25Output
from stage2_5.legal_verifier import verify_legal_claims

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stage 2.5 Main Orchestrator: Legal Verification

    Validates legal claims in the article against provided court decisions.

    Args:
        input_dict: Dictionary with:
            - article: ArticleOutput dict from Stage 2
            - legal_context: LegalContext dict from Stage 1 (optional)

    Returns:
        Stage25Output dict with:
            - article: Article with legal_verification_status updated
            - claims_extracted: Total number of claims found
            - claims_supported: Number of supported claims
            - claims_unsupported: Number of unsupported claims
            - legal_claims: Detailed list of all claims
            - ai_calls: Number of AI calls (1 or 0)
            - verification_skipped: True if no legal context

    Raises:
        ValidationError: If input_dict doesn't match Stage25Input schema
        Exception: If verification fails critically

    Example:
        >>> input_dict = {
        ...     "article": {"Headline": "...", "section_01_content": "..."},
        ...     "legal_context": {"court_decisions": [...], "rechtsgebiet": "Arbeitsrecht"}
        ... }
        >>> output = await run(input_dict)
        >>> output["claims_extracted"]
        12
        >>> output["article"]["legal_verification_status"]
        'verified'
    """
    logger.info("=" * 80)
    logger.info("STAGE 2.5: LEGAL VERIFICATION")
    logger.info("=" * 80)

    # Validate input
    try:
        stage_input = Stage25Input(**input_dict)
    except Exception as e:
        logger.error(f"Input validation failed: {e}")
        raise

    # Extract inputs
    article_dict = stage_input.article.copy()
    legal_context = stage_input.legal_context

    # Log mode
    if not legal_context:
        logger.info("Mode: SKIP (no legal context provided)")
    else:
        rechtsgebiet = legal_context.get("rechtsgebiet", "unknown")
        num_decisions = len(legal_context.get("court_decisions", []))
        logger.info(f"Mode: VERIFY (rechtsgebiet={rechtsgebiet}, decisions={num_decisions})")

    # Verify legal claims
    modified_article, claims, ai_calls = await verify_legal_claims(
        article=article_dict,
        legal_context=legal_context
    )

    # Count results
    claims_supported = len([c for c in claims if c.supported])
    claims_unsupported = len([c for c in claims if not c.supported])

    # Build output
    output = Stage25Output(
        article=modified_article,
        claims_extracted=len(claims),
        claims_supported=claims_supported,
        claims_unsupported=claims_unsupported,
        legal_claims=claims,
        ai_calls=ai_calls,
        verification_skipped=(legal_context is None)
    )

    # Log summary
    logger.info("-" * 80)
    logger.info("STAGE 2.5 COMPLETE")
    logger.info(f"  Claims Extracted: {len(claims)}")
    logger.info(f"  Claims Supported: {claims_supported}")
    logger.info(f"  Claims Unsupported: {claims_unsupported}")
    logger.info(f"  Verification Status: {modified_article.get('legal_verification_status', 'unknown')}")
    logger.info(f"  AI Calls: {ai_calls}")
    logger.info("=" * 80)

    return output.model_dump()


def run_sync(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous wrapper for run().

    Args:
        input_dict: Same as run()

    Returns:
        Same as run()
    """
    return asyncio.run(run(input_dict))


def run_from_json(input_json: str) -> str:
    """
    JSON string input/output wrapper.

    Args:
        input_json: JSON string with article and legal_context

    Returns:
        JSON string with Stage25Output

    Example:
        >>> input_json = '{"article": {...}, "legal_context": {...}}'
        >>> output_json = run_from_json(input_json)
        >>> output = json.loads(output_json)
        >>> output["claims_extracted"]
        12
    """
    input_dict = json.loads(input_json)
    output_dict = run_sync(input_dict)
    return json.dumps(output_dict, ensure_ascii=False, indent=2)


# CLI entry point for standalone testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stage 2.5: Legal Verification")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input JSON file (with article and legal_context)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to output JSON file (default: print to stdout)"
    )

    args = parser.parse_args()

    # Load input
    with open(args.input, "r", encoding="utf-8") as f:
        input_json = f.read()

    # Run verification
    output_json = run_from_json(input_json)

    # Save or print output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Verification complete. Output saved to: {args.output}")
    else:
        print(output_json)
