"""
Beck-Online Resource Extractor

Reuses the existing browser_agent.py to extract legal resources from Beck-Online
and stores them in the SQLite database.

This module wraps the existing research_via_beck_online() function and adds:
- Persistent storage in SQLite
- Per-keyword extraction (vs. per-batch in the pipeline)
- Content plan integration
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from shared.database import OpenBlogDB

logger = logging.getLogger(__name__)

# Import browser agent from stage1
try:
    _stage1_path = _PROJECT_ROOT / "stage1"
    if str(_stage1_path) not in sys.path:
        sys.path.insert(0, str(_stage1_path))

    from browser_agent import research_via_beck_online
    from legal_researcher import conduct_legal_research

    BECK_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Beck-Online browser agent not available: {e}")
    BECK_AVAILABLE = False


async def extract_for_keyword(
    keyword: str,
    rechtsgebiet: Optional[str] = None,
    use_mock: bool = False,
    db: Optional[OpenBlogDB] = None,
) -> Dict:
    """
    Extract Beck-Online resources for a single keyword and store in DB.

    Args:
        keyword: Article title/keyword
        rechtsgebiet: German legal area (auto-detected if None)
        use_mock: Use mock data instead of live Beck-Online
        db: Database instance (creates new one if None)

    Returns:
        Dict with keyword, rechtsgebiet, resources_count, resources, error
    """
    if db is None:
        db = OpenBlogDB()

    result = {
        "keyword": keyword,
        "rechtsgebiet": rechtsgebiet or "",
        "resources_count": 0,
        "resources": [],
        "error": None,
    }

    # Check if we already have resources for this keyword
    existing = db.get_beck_resources(keyword)
    if existing:
        logger.info(f"Found {len(existing)} existing resources for '{keyword}', skipping extraction")
        result["resources"] = existing
        result["resources_count"] = len(existing)
        result["rechtsgebiet"] = existing[0].get("rechtsgebiet", "")
        return result

    try:
        if use_mock:
            # Use mock data via legal_researcher
            from legal_researcher import conduct_legal_research

            legal_context = await conduct_legal_research(
                keywords=[keyword],
                rechtsgebiet=rechtsgebiet or "Arbeitsrecht",
                use_mock=True,
            )
        else:
            if not BECK_AVAILABLE:
                raise ImportError(
                    "Beck-Online browser agent not available. "
                    "Install: pip install browser-use playwright && playwright install chromium"
                )

            # Live Beck-Online extraction
            legal_context = await research_via_beck_online(
                keywords=[keyword],
                rechtsgebiet=rechtsgebiet or "Arbeitsrecht",
            )

        # Extract court decisions from LegalContext
        decisions = []
        if hasattr(legal_context, "court_decisions"):
            decisions = [d.model_dump() for d in legal_context.court_decisions]
        elif isinstance(legal_context, dict):
            raw = legal_context.get("court_decisions", [])
            decisions = [d.model_dump() if hasattr(d, "model_dump") else d for d in raw]

        # Get rechtsgebiet from result
        if hasattr(legal_context, "rechtsgebiet"):
            result["rechtsgebiet"] = legal_context.rechtsgebiet
        elif isinstance(legal_context, dict):
            result["rechtsgebiet"] = legal_context.get("rechtsgebiet", rechtsgebiet or "")

        # Store in database
        if decisions:
            db.store_beck_resources(keyword, decisions)
            result["resources"] = decisions
            result["resources_count"] = len(decisions)
            logger.info(
                f"Extracted and stored {len(decisions)} resources for '{keyword}' "
                f"(rechtsgebiet: {result['rechtsgebiet']})"
            )
        else:
            logger.warning(f"No resources found for '{keyword}'")

    except Exception as e:
        logger.error(f"Extraction failed for '{keyword}': {type(e).__name__}: {e}")
        result["error"] = str(e)

    return result


async def extract_for_keywords(
    keywords: List[str],
    rechtsgebiet: Optional[str] = None,
    use_mock: bool = False,
) -> Dict:
    """
    Extract Beck-Online resources for multiple keywords sequentially.

    Sequential to avoid overloading Beck-Online with concurrent browser sessions.

    Args:
        keywords: List of article titles/keywords
        rechtsgebiet: German legal area (applied to all)
        use_mock: Use mock data

    Returns:
        BeckExtractionOutput-compatible dict
    """
    db = OpenBlogDB()
    results = []
    total_resources = 0
    errors = []

    for i, keyword in enumerate(keywords):
        logger.info(f"Extracting resources for ({i+1}/{len(keywords)}): {keyword}")
        result = await extract_for_keyword(
            keyword=keyword,
            rechtsgebiet=rechtsgebiet,
            use_mock=use_mock,
            db=db,
        )
        results.append(result)
        total_resources += result["resources_count"]
        if result["error"]:
            errors.append(f"{keyword}: {result['error']}")

        # Rate limit: wait between keywords to avoid triggering Beck-Online captcha
        if i < len(keywords) - 1 and not use_mock:
            import asyncio
            delay = 120  # 2 minutes between extractions
            logger.info(f"Rate limiting: waiting {delay}s before next keyword...")
            await asyncio.sleep(delay)

    return {
        "results": results,
        "total_resources": total_resources,
        "total_keywords": len(keywords),
        "errors": errors,
    }


async def extract_from_content_plan(
    rechtsgebiet: Optional[str] = None,
    use_mock: bool = False,
) -> Dict:
    """
    Extract Beck-Online resources for all planned articles in content_plan table.

    Only processes entries with status='planned' that don't already have resources.
    """
    db = OpenBlogDB()
    # Try both English and German status names
    plan_entries = db.get_content_plan(status="planned")
    if not plan_entries:
        plan_entries = db.get_content_plan(status="Geplant")
    if not plan_entries:
        # Fall back to all entries if no status filter matches
        plan_entries = db.get_content_plan()

    if not plan_entries:
        logger.info("No articles found in content plan")
        return {"results": [], "total_resources": 0, "total_keywords": 0, "errors": []}

    keywords = []
    for entry in plan_entries:
        kw = entry.get("keyword") or entry.get("title", "")
        if kw:
            keywords.append(kw)

    logger.info(f"Found {len(keywords)} planned articles to extract resources for")
    return await extract_for_keywords(keywords, rechtsgebiet=rechtsgebiet, use_mock=use_mock)
