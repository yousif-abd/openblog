"""
Stage 0: Humanization Research Agents (Fast HTTP Version)

Collects real human content before article generation:
1. Google PAA (Ähnliche Fragen) — real questions users ask
2. Forum questions — authentic language from juraforum.de, gutefrage.net
3. Competitor headings — H2/H3 structure from top-ranking articles

All three sub-agents run in parallel using httpx (no browser needed).
Failures are non-fatal: if any scraper fails, the pipeline continues.

AI Calls: 0 (pure HTML parsing, no LLM calls)
"""

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Add project root for imports
_BASE_PATH = Path(__file__).parent.parent
if str(_BASE_PATH) not in sys.path:
    sys.path.insert(0, str(_BASE_PATH))

from stage0.stage0_models import Stage0Output, ForumQuestion, CompetitorPage

logger = logging.getLogger(__name__)

# Common headers to avoid bot detection
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
}


# =============================================================================
# Google PAA Scraper (HTTP)
# =============================================================================

async def scrape_google_paa(keyword: str, language: str = "de") -> List[str]:
    """
    Fetch Google SERP for the keyword and extract PAA questions from HTML.

    Args:
        keyword: Search keyword
        language: Language code (default: de)

    Returns:
        List of PAA question strings
    """
    if not HTTPX_AVAILABLE:
        logger.warning("httpx not available, skipping PAA scraping")
        return []

    query = quote_plus(keyword)
    url = f"https://www.google.de/search?q={query}&hl=de&gl=DE"

    try:
        async with httpx.AsyncClient(
            headers=_HEADERS,
            follow_redirects=True,
            timeout=15.0,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

        # Extract PAA questions from Google HTML
        questions = []

        # Pattern 1: data-q attribute contains question text
        pattern_data_q = re.findall(r'data-q="([^"]+)"', html)
        for q in pattern_data_q:
            q = q.strip()
            if q and len(q) > 10 and q not in questions:
                questions.append(q)

        # Pattern 2: aria-expanded spans in PAA accordion
        pattern_paa = re.findall(
            r'<div[^>]*jsname="[^"]*"[^>]*>\s*<span[^>]*>([^<]{15,120})\?</span>',
            html
        )
        for q in pattern_paa:
            q = q.strip() + "?"
            if q not in questions:
                questions.append(q)

        # Pattern 3: Question-like text near PAA section header
        paa_section = re.search(
            r'(Ähnliche Fragen|Nutzer fragen auch|People also ask)(.*?)'
            r'(Weitere Ergebnisse|Ähnliche Suchanfragen|$)',
            html, re.DOTALL | re.IGNORECASE
        )
        if paa_section:
            section_html = paa_section.group(2)
            q_patterns = re.findall(r'>([^<]{15,150}\?)\s*<', section_html)
            for q in q_patterns:
                q = q.strip()
                if q and q not in questions:
                    questions.append(q)

        logger.info(f"PAA: Extracted {len(questions)} questions from Google SERP")
        return questions[:8]

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning("PAA: Google rate-limited (429), skipping")
        else:
            logger.warning(f"PAA: HTTP error {e.response.status_code}")
        return []
    except Exception as e:
        logger.warning(f"PAA scraping failed (non-fatal): {type(e).__name__}: {e}")
        return []


# =============================================================================
# Forum Question Scraper (HTTP)
# =============================================================================

async def scrape_forum_questions(
    keyword: str,
    sites: Optional[List[str]] = None,
) -> List[ForumQuestion]:
    """
    Search Google for forum threads and extract titles from SERP HTML.

    Args:
        keyword: Search keyword
        sites: Forum domains to search (default: juraforum.de, gutefrage.net)

    Returns:
        List of ForumQuestion objects with real user questions
    """
    if not HTTPX_AVAILABLE:
        logger.warning("httpx not available, skipping forum scraping")
        return []

    if sites is None:
        sites = ["juraforum.de", "gutefrage.net"]

    all_questions: List[ForumQuestion] = []

    for site in sites:
        query = quote_plus(f"site:{site} {keyword}")
        url = f"https://www.google.de/search?q={query}&hl=de&gl=DE&num=5"

        try:
            async with httpx.AsyncClient(
                headers=_HEADERS,
                follow_redirects=True,
                timeout=15.0,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

            # Extract search result titles and URLs
            results = re.findall(
                r'<a[^>]+href="(/url\?q=([^"&]+)|([^"]+))"[^>]*>\s*<h3[^>]*>([^<]+)</h3>',
                html
            )

            for match in results:
                raw_url = match[1] or match[2]
                title = match[3].strip()

                if site not in raw_url:
                    continue

                if title and len(title) > 10:
                    all_questions.append(ForumQuestion(
                        source=site,
                        question=title,
                        context="",
                        url=raw_url,
                    ))

            # Fallback: extract <h3> texts if standard pattern finds nothing
            if not any(q.source == site for q in all_questions):
                h3_texts = re.findall(r'<h3[^>]*>([^<]+)</h3>', html)
                for t in h3_texts[:5]:
                    t = t.strip()
                    if t and len(t) > 10:
                        all_questions.append(ForumQuestion(
                            source=site,
                            question=t,
                            context="",
                            url=f"https://www.{site}",
                        ))

            site_count = len([q for q in all_questions if q.source == site])
            logger.info(f"Forum: {site_count} questions from {site}")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"Forum: Google rate-limited for {site}, skipping")
            else:
                logger.warning(f"Forum: HTTP error {e.response.status_code} for {site}")
        except Exception as e:
            logger.warning(
                f"Forum scraping failed for {site} (non-fatal): {type(e).__name__}: {e}"
            )

    return all_questions


# =============================================================================
# Competitor Heading Scraper (HTTP)
# =============================================================================

async def scrape_competitor_headings(
    keyword: str,
    language: str = "de",
    num_results: int = 3,
) -> List[CompetitorPage]:
    """
    Search Google, fetch top organic result pages, extract H2/H3 headings.

    Args:
        keyword: Search keyword
        language: Language code
        num_results: Number of competitor pages to analyze

    Returns:
        List of CompetitorPage objects with heading structures
    """
    if not HTTPX_AVAILABLE:
        logger.warning("httpx not available, skipping competitor scraping")
        return []

    query = quote_plus(keyword)
    serp_url = f"https://www.google.de/search?q={query}&hl=de&gl=DE&num={num_results + 2}"

    try:
        async with httpx.AsyncClient(
            headers=_HEADERS,
            follow_redirects=True,
            timeout=15.0,
        ) as client:
            serp_response = await client.get(serp_url)
            serp_response.raise_for_status()
            serp_html = serp_response.text

        # Extract organic result URLs from Google redirect links
        url_matches = re.findall(r'/url\?q=(https?://[^&"]+)', serp_html)

        organic_urls = []
        seen_domains = set()
        for u in url_matches:
            if "google." in u or "youtube.com" in u:
                continue
            domain_match = re.match(r'https?://([^/]+)', u)
            if domain_match:
                domain = domain_match.group(1)
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    organic_urls.append(u)
            if len(organic_urls) >= num_results:
                break

        if not organic_urls:
            logger.info("Competitor: No organic URLs found in SERP")
            return []

        # Fetch each page and extract H2/H3 headings
        competitors = []

        async with httpx.AsyncClient(
            headers=_HEADERS,
            follow_redirects=True,
            timeout=10.0,
        ) as client:
            for page_url in organic_urls:
                try:
                    resp = await client.get(page_url)
                    resp.raise_for_status()
                    page_html = resp.text

                    title_match = re.search(
                        r'<title[^>]*>([^<]+)</title>', page_html, re.IGNORECASE
                    )
                    page_title = title_match.group(1).strip() if title_match else ""

                    headings = []
                    h2_matches = re.findall(
                        r'<h2[^>]*>([^<]+)</h2>', page_html, re.IGNORECASE
                    )
                    for h in h2_matches:
                        h = h.strip()
                        if h and 3 < len(h) < 200:
                            headings.append(f"H2: {h}")

                    h3_matches = re.findall(
                        r'<h3[^>]*>([^<]+)</h3>', page_html, re.IGNORECASE
                    )
                    for h in h3_matches:
                        h = h.strip()
                        if h and 3 < len(h) < 200:
                            headings.append(f"H3: {h}")

                    if headings:
                        competitors.append(CompetitorPage(
                            url=page_url,
                            title=page_title,
                            headings=headings[:15],
                        ))
                        logger.info(
                            f"Competitor: {len(headings)} headings from "
                            f"{page_url[:60]}..."
                        )

                except Exception as e:
                    logger.debug(f"Competitor: Failed to fetch {page_url[:60]}: {e}")
                    continue

        logger.info(f"Competitor: Scraped headings from {len(competitors)} pages")
        return competitors

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning("Competitor: Google rate-limited (429), skipping")
        else:
            logger.warning(f"Competitor: HTTP error {e.response.status_code}")
        return []
    except Exception as e:
        logger.warning(
            f"Competitor scraping failed (non-fatal): {type(e).__name__}: {e}"
        )
        return []


# =============================================================================
# Gemini Fallback (Google Search Grounding)
# =============================================================================

async def _gemini_humanization_fallback(keyword: str, language: str = "de") -> dict:
    """
    Use Gemini with Google Search grounding to find real PAA questions
    and forum discussions when HTML scraping fails.

    Returns:
        Dict with "paa" (list of strings) and "forum_questions" (list of strings)
    """
    from shared.gemini_client import GeminiClient

    client = GeminiClient()

    prompt = f"""Du bist ein SEO-Researcher. Suche im Internet nach dem Thema "{keyword}" auf dem deutschen Markt.

Finde und gib mir zurück:

1. **PAA-Fragen (Ähnliche Fragen)**: 4-8 echte Fragen, die Nutzer zu diesem Thema bei Google stellen.
   Diese müssen authentische Fragen sein, wie sie in der Google-Suche unter "Ähnliche Fragen" erscheinen.

2. **Forum-Fragen**: 3-5 echte Fragen von Nutzern aus deutschen Rechtsforen oder Ratgeberforen
   (z.B. juraforum.de, gutefrage.net, finanztip.de). Diese sollen die echte Sprache und Sorgen
   der Menschen widerspiegeln.

Antworte NUR im folgenden JSON-Format, ohne Erklärungen:
{{
  "paa": ["Frage 1?", "Frage 2?", ...],
  "forum_questions": ["Frage 1?", "Frage 2?", ...]
}}"""

    result = await client.generate(
        prompt=prompt,
        use_google_search=True,
        json_output=True,
        temperature=0.3,
        max_tokens=2048,
    )

    if not result:
        return {"paa": [], "forum_questions": []}

    # result may already be a dict (json_output=True) or a string
    if isinstance(result, dict):
        data = result
    else:
        import json
        try:
            data = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Gemini fallback returned non-JSON, trying to extract questions")
            questions = re.findall(r'"([^"]{15,150}\?)"', str(result))
            half = len(questions) // 2
            return {
                "paa": questions[:half] or questions[:4],
                "forum_questions": questions[half:] or [],
            }

    return {
        "paa": data.get("paa", [])[:8],
        "forum_questions": data.get("forum_questions", [])[:5],
    }


# =============================================================================
# Stage 0 Orchestrator
# =============================================================================

def _simplify_keyword(keyword: str) -> str:
    """
    Simplify a long article title into a better Google search query.

    Examples:
        "Berliner Testament: Vorteile, Risiken und Alternativen" → "Berliner Testament"
        "Erbrecht: 3 häufige Fehler" → "Erbrecht häufige Fehler"
        "Nach mir die Sintflut: Gefahren der gesetzlichen Erbfolge" → "Gefahren gesetzliche Erbfolge"
    """
    # If keyword has a colon, combine the topic (before) with key terms from after
    if ":" in keyword:
        parts = keyword.split(":", 1)
        before = parts[0].strip()
        after = parts[1].strip()
        # Always keep the part before the colon (the main topic)
        # If before is short (1 word), combine with first 2-3 meaningful words from after
        if len(before.split()) >= 2:
            simplified = before
        else:
            # Take topic + first meaningful words from subtitle
            after_words = list(w for w in after.split() if len(w) > 2 and not w.endswith("?"))[:2]
            simplified = before + " " + " ".join(after_words) if after_words else before
    else:
        simplified = keyword

    # Remove numbering patterns like "3 häufige" → "häufige"
    simplified = re.sub(r'^\d+\s+', '', simplified)
    # Remove trailing year references
    simplified = re.sub(r'\s+\d{4}$', '', simplified)

    return simplified.strip()


async def run_stage_0(keyword: str, language: str = "de") -> Stage0Output:
    """
    Run all three Stage 0 sub-agents in parallel using httpx.

    Each agent is independent — failures in one don't affect the others.
    Results are collected and returned as Stage0Output.

    Args:
        keyword: Primary article keyword
        language: Target language code

    Returns:
        Stage0Output with PAA questions, forum questions, and competitor headings
    """
    logger.info(f"Stage 0: Humanization Research for '{keyword}' (httpx mode)")

    if not HTTPX_AVAILABLE:
        logger.warning("httpx not installed. Stage 0 returning empty results.")
        return Stage0Output(errors=["httpx not installed"])

    # Simplify keyword for better Google results
    search_keyword = _simplify_keyword(keyword)
    if search_keyword != keyword:
        logger.info(f"  Simplified search keyword: '{keyword}' → '{search_keyword}'")

    errors = []

    # Run all three in parallel, using simplified keyword for search
    results = await asyncio.gather(
        scrape_google_paa(search_keyword, language),
        scrape_forum_questions(search_keyword),
        scrape_competitor_headings(search_keyword, language),
        return_exceptions=True,
    )

    paa = results[0] if not isinstance(results[0], BaseException) else []
    if isinstance(results[0], BaseException):
        errors.append(f"PAA scraper: {results[0]}")

    forums = results[1] if not isinstance(results[1], BaseException) else []
    if isinstance(results[1], BaseException):
        errors.append(f"Forum scraper: {results[1]}")

    competitors = results[2] if not isinstance(results[2], BaseException) else []
    if isinstance(results[2], BaseException):
        errors.append(f"Competitor scraper: {results[2]}")

    # If scraping returned nothing, use Gemini with Google Search grounding
    total_scraped = len(paa) + len(forums) + len(competitors)
    if total_scraped == 0:
        logger.info("  Scraping returned 0 results, falling back to Gemini Search grounding...")
        try:
            gemini_result = await _gemini_humanization_fallback(keyword, language)
            paa = gemini_result.get("paa", [])
            forums_raw = gemini_result.get("forum_questions", [])
            forums = [
                ForumQuestion(question=q, source="gemini-search", url="")
                for q in forums_raw
            ]
            logger.info(f"  Gemini fallback: {len(paa)} PAA, {len(forums)} forum Qs")
        except Exception as e:
            logger.warning(f"  Gemini fallback failed: {type(e).__name__}: {e}")
            errors.append(f"Gemini fallback: {e}")

    output = Stage0Output(
        paa_questions=paa,
        forum_questions=forums,
        competitor_headings=competitors,
        errors=errors,
    )

    logger.info(
        f"Stage 0 complete: {len(output.paa_questions)} PAA, "
        f"{len(output.forum_questions)} forum Qs, "
        f"{len(output.competitor_headings)} competitors"
    )

    return output
