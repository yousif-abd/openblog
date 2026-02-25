"""
Stage 0: Humanization Research Agents

Uses browser-use to scrape real human content before article generation:
1. Google PAA (Ähnliche Fragen) — real questions users ask
2. Forum questions — authentic language from juraforum.de, gutefrage.net
3. Competitor headings — H2/H3 structure from top-ranking articles

All three sub-agents run in parallel. Failures are non-fatal:
if any scraper fails, the pipeline continues with whatever data was collected.

AI Calls: 0-3 (one per browser-use agent, only if browser-use is available)
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

# Add project root for imports
_BASE_PATH = Path(__file__).parent.parent
if str(_BASE_PATH) not in sys.path:
    sys.path.insert(0, str(_BASE_PATH))

from stage0.stage0_models import Stage0Output, ForumQuestion, CompetitorPage

logger = logging.getLogger(__name__)

# Check browser-use availability
try:
    from browser_use.agent.service import Agent
    from browser_use.browser import BrowserSession, BrowserProfile
    from browser_use.llm.google.chat import ChatGoogle
    BROWSER_USE_AVAILABLE = True
except ImportError as e:
    BROWSER_USE_AVAILABLE = False
    logger.warning(f"browser-use not available for Stage 0: {e}")


# =============================================================================
# Google PAA Scraper
# =============================================================================

PAA_TASK_TEMPLATE = """
TASK: Extract "People Also Ask" questions from Google search results.

Step 1: Go to https://www.google.de/search?q={query}&hl=de
Step 2: If a cookie consent popup appears, click "Alle akzeptieren"
Step 3: Look for the "Ähnliche Fragen" or "Nutzer fragten auch" section on the page
Step 4: If found, click on each question to expand it (this reveals additional questions)
Step 5: Extract ALL question text strings you can see in this section (aim for 4-8 questions)
Step 6: Call done with all questions in this format:

PAA_SUCCESS
Question 1: [exact question text]
Question 2: [exact question text]
Question 3: [exact question text]
...

If no PAA section exists, call done with: NO_PAA_FOUND

CRITICAL:
- Only extract the QUESTION text, not the answers
- Do NOT click on any ads or sponsored content
- Do NOT navigate away from the search results page
- Extract the questions EXACTLY as written (in German)
"""


async def scrape_google_paa(keyword: str, language: str = "de") -> List[str]:
    """
    Search Google.de for keyword, extract the 'Ähnliche Fragen' (PAA) box.
    
    Args:
        keyword: Search keyword
        language: Language code (default: de)
        
    Returns:
        List of PAA question strings
    """
    if not BROWSER_USE_AVAILABLE:
        logger.warning("browser-use not available, skipping PAA scraping")
        return []

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.warning("GEMINI_API_KEY not set, skipping PAA scraping")
        return []

    llm = ChatGoogle(
        model="gemini-3.1-pro",
        api_key=gemini_api_key,
        temperature=0.1,
    )

    browser_profile = BrowserProfile(headless=True)
    browser_session = BrowserSession(browser_profile=browser_profile)

    try:
        await browser_session.start()

        query = quote_plus(keyword)
        task = PAA_TASK_TEMPLATE.format(query=query)

        agent = Agent(
            task=task,
            llm=llm,
            browser_session=browser_session,
            use_vision=False,
            max_failures=3,
            max_actions_per_step=15,
        )

        result = await agent.run()
        content = result.extracted_content() or []
        output = "\n".join(str(item) for item in content if item)

        if "NO_PAA_FOUND" in output:
            logger.info("No PAA section found on Google for this keyword")
            return []

        # Parse questions from output
        questions = []
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("Question") and ":" in line:
                q = line.split(":", 1)[1].strip()
                if q and len(q) > 5:
                    questions.append(q)

        logger.info(f"Scraped {len(questions)} PAA questions from Google")
        return questions

    except Exception as e:
        logger.warning(f"PAA scraping failed (non-fatal): {e}")
        return []
    finally:
        await browser_session.stop()


# =============================================================================
# Forum Question Scraper
# =============================================================================

FORUM_TASK_TEMPLATE = """
TASK: Find real user questions about a legal topic from German forums.

Step 1: Go to https://www.google.de/search?q=site:{site}+{query}&hl=de
Step 2: If a cookie consent popup appears, click "Alle akzeptieren"
Step 3: Look at the search results — these are forum threads from {site}
Step 4: For each of the top 5 results:
   - Note the thread TITLE (this is the user's question)
   - Click on the result
   - Copy the FIRST 200 characters of the original post (the question body)
   - Go BACK to search results
Step 5: Call done with all questions in this format:

FORUM_SUCCESS
Thread 1:
Title: [thread title]
Context: [first 200 chars of original post]
URL: [thread URL]

Thread 2:
Title: [thread title]
Context: [first 200 chars of original post]
URL: [thread URL]
...

If no results found, call done with: NO_FORUM_RESULTS

CRITICAL:
- Extract at least 3 threads, up to 5
- Copy the exact question text — do NOT paraphrase
- Do NOT click on ads
- The Context should be the ORIGINAL POSTER's text, not a reply
"""


async def scrape_forum_questions(
    keyword: str,
    sites: Optional[List[str]] = None,
) -> List[ForumQuestion]:
    """
    Search German legal forums for real user questions about the keyword.
    
    Args:
        keyword: Search keyword
        sites: Forum domains to search (default: juraforum.de, gutefrage.net)
        
    Returns:
        List of ForumQuestion objects with real user questions
    """
    if not BROWSER_USE_AVAILABLE:
        logger.warning("browser-use not available, skipping forum scraping")
        return []

    if sites is None:
        sites = ["juraforum.de", "gutefrage.net"]

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.warning("GEMINI_API_KEY not set, skipping forum scraping")
        return []

    all_questions = []

    for site in sites:
        llm = ChatGoogle(
            model="gemini-3.1-pro",
            api_key=gemini_api_key,
            temperature=0.1,
        )

        browser_profile = BrowserProfile(headless=True)
        browser_session = BrowserSession(browser_profile=browser_profile)

        try:
            await browser_session.start()

            query = quote_plus(keyword)
            task = FORUM_TASK_TEMPLATE.format(site=site, query=query)

            agent = Agent(
                task=task,
                llm=llm,
                browser_session=browser_session,
                use_vision=False,
                max_failures=3,
                max_actions_per_step=20,
            )

            result = await agent.run()
            content = result.extracted_content() or []
            output = "\n".join(str(item) for item in content if item)

            if "NO_FORUM_RESULTS" in output:
                logger.info(f"No forum results found on {site}")
                continue

            # Parse forum questions from output
            import re
            thread_blocks = re.split(r"Thread \d+:", output)
            for block in thread_blocks:
                if "Title:" not in block:
                    continue
                title_match = re.search(r"Title:\s*(.+)", block)
                context_match = re.search(r"Context:\s*(.+)", block)
                url_match = re.search(r"URL:\s*(.+)", block)

                if title_match:
                    q = ForumQuestion(
                        source=site,
                        question=title_match.group(1).strip(),
                        context=context_match.group(1).strip() if context_match else "",
                        url=url_match.group(1).strip() if url_match else "",
                    )
                    all_questions.append(q)

            logger.info(f"Scraped {len(all_questions)} questions from {site}")

        except Exception as e:
            logger.warning(f"Forum scraping failed for {site} (non-fatal): {e}")
        finally:
            await browser_session.stop()

    return all_questions


# =============================================================================
# Competitor Heading Scraper
# =============================================================================

COMPETITOR_TASK_TEMPLATE = """
TASK: Extract H2 and H3 headings from top Google search results.

Step 1: Go to https://www.google.de/search?q={query}&hl=de
Step 2: If a cookie consent popup appears, click "Alle akzeptieren"
Step 3: Look at the organic (non-ad) search results. Skip anything marked "Gesponsert" or "Anzeige".
Step 4: For each of the top 3 organic results:
   - Note the page TITLE and URL
   - Click on the result
   - Extract ALL <h2> and <h3> headings from the page content
   - Go BACK to search results
   - Click the NEXT organic result
Step 5: Call done with all headings in this format:

COMPETITOR_SUCCESS

Page 1:
URL: [page URL]
Title: [page title]
H2: [first h2 heading]
H2: [second h2 heading]
H3: [first h3 heading]
...

Page 2:
URL: [page URL]
Title: [page title]
H2: [heading]
...

Page 3:
URL: [page URL]
Title: [page title]
H2: [heading]
...

CRITICAL:
- Skip ads and sponsored results
- Extract headings EXACTLY as they appear on the page
- Only extract H2 and H3 level headings (not H1, H4, etc.)
- Go back to search results after each page
- Do NOT extract headings from navigation, footer, or sidebar — only from the main article content
"""


async def scrape_competitor_headings(
    keyword: str,
    language: str = "de",
    num_results: int = 3,
) -> List[CompetitorPage]:
    """
    Search Google.de, visit top organic results, extract H2/H3 headings.
    
    Args:
        keyword: Search keyword
        language: Language code
        num_results: Number of competitor pages to analyze
        
    Returns:
        List of CompetitorPage objects with heading structures
    """
    if not BROWSER_USE_AVAILABLE:
        logger.warning("browser-use not available, skipping competitor scraping")
        return []

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.warning("GEMINI_API_KEY not set, skipping competitor scraping")
        return []

    llm = ChatGoogle(
        model="gemini-3.1-pro",
        api_key=gemini_api_key,
        temperature=0.1,
    )

    browser_profile = BrowserProfile(headless=True)
    browser_session = BrowserSession(browser_profile=browser_profile)

    try:
        await browser_session.start()

        query = quote_plus(keyword)
        task = COMPETITOR_TASK_TEMPLATE.format(query=query)

        agent = Agent(
            task=task,
            llm=llm,
            browser_session=browser_session,
            use_vision=False,
            max_failures=3,
            max_actions_per_step=25,
        )

        result = await agent.run()
        content = result.extracted_content() or []
        output = "\n".join(str(item) for item in content if item)

        # Parse competitor pages from output
        import re
        competitors = []
        page_blocks = re.split(r"Page \d+:", output)

        for block in page_blocks:
            if "URL:" not in block:
                continue

            url_match = re.search(r"URL:\s*(.+)", block)
            title_match = re.search(r"Title:\s*(.+)", block)

            headings = []
            for line in block.split("\n"):
                line = line.strip()
                if line.startswith("H2:") or line.startswith("H3:"):
                    headings.append(line)

            if url_match and headings:
                competitors.append(CompetitorPage(
                    url=url_match.group(1).strip(),
                    title=title_match.group(1).strip() if title_match else "",
                    headings=headings,
                ))

        logger.info(f"Scraped headings from {len(competitors)} competitor pages")
        return competitors

    except Exception as e:
        logger.warning(f"Competitor scraping failed (non-fatal): {e}")
        return []
    finally:
        await browser_session.stop()


# =============================================================================
# Stage 0 Orchestrator
# =============================================================================

async def run_stage_0(keyword: str, language: str = "de") -> Stage0Output:
    """
    Run all three Stage 0 sub-agents in parallel.
    
    Each agent is independent — failures in one don't affect the others.
    Results are collected and returned as Stage0Output for use in Stage 2.
    
    Args:
        keyword: Primary article keyword
        language: Target language code
        
    Returns:
        Stage0Output with PAA questions, forum questions, and competitor headings
    """
    logger.info(f"Stage 0: Humanization Research for '{keyword}'")

    if not BROWSER_USE_AVAILABLE:
        logger.warning("browser-use not installed. Stage 0 returning empty results.")
        return Stage0Output(errors=["browser-use not installed"])

    errors = []

    # Run all three in parallel
    paa_task = scrape_google_paa(keyword, language)
    forum_task = scrape_forum_questions(keyword)
    competitor_task = scrape_competitor_headings(keyword, language)

    results = await asyncio.gather(
        paa_task, forum_task, competitor_task,
        return_exceptions=True,
    )

    paa = results[0] if not isinstance(results[0], Exception) else []
    if isinstance(results[0], Exception):
        errors.append(f"PAA scraper: {results[0]}")

    forums = results[1] if not isinstance(results[1], Exception) else []
    if isinstance(results[1], Exception):
        errors.append(f"Forum scraper: {results[1]}")

    competitors = results[2] if not isinstance(results[2], Exception) else []
    if isinstance(results[2], Exception):
        errors.append(f"Competitor scraper: {results[2]}")

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
