"""
Stage 2: Gemini Content Generation with Tools

Maps to v4.1 Phase 2, Step 5: gemini-research

CRITICAL STAGE for deep research:
- Calls Gemini 3 Pro (default, max quality) with tools enabled
- Tools (googleSearch + urlContext) enable 20+ web searches during generation
- Response format: text/plain (allows natural language + embedded JSON)
- Retry logic: exponential backoff (max 3, 5s initial wait)
- Response parsing: extracts JSON from plain text
- Model configurable via GEMINI_MODEL env var (defaults to gemini-3-pro-preview)

Input:
  - ExecutionContext.prompt (from Stage 1)

Output:
  - ExecutionContext.raw_article (raw Gemini response: text/plain with JSON)

The prompt rules force research:
- "every paragraph must contain number, KPI or real example" → forces web search
- "cite all facts" → forces source finding
- "vary examples" → forces multiple searches
Combined with tools = deep research happens naturally.
"""

import logging
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from ..core.execution_context import ExecutionContext
from ..core.workflow_engine import Stage
from ..core.error_handling import with_api_retry, error_reporter, ErrorClassifier
from ..models.gemini_client import GeminiClient, build_article_response_schema

logger = logging.getLogger(__name__)


class GeminiCallStage(Stage):
    """
    Stage 2: Generate content using Gemini API with tools + JSON schema.

    Handles:
    - Initializing Gemini client
    - Building response_schema from ArticleOutput (forces structured output)
    - Calling API with tools enabled + schema
    - Parsing response (now direct JSON from Gemini)
    - Error handling and retry logic
    - Storing raw article in context
    """

    stage_num = 2
    stage_name = "Gemini Content Generation (Structured JSON)"

    def __init__(self) -> None:
        """Initialize stage with Gemini client."""
        self.client = GeminiClient()
        logger.info(f"Stage 2 initialized: {self.client}")

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 2: Generate content with Gemini (structured JSON output).

        Input from context:
        - prompt: Complete prompt (from Stage 1)
        - job_config.word_count: Target word count (optional, dynamic)

        Output to context:
        - raw_article: Raw Gemini response (DIRECT JSON matching ArticleOutput schema)

        Args:
            context: ExecutionContext from Stage 1

        Returns:
            Updated context with raw_article populated

        Raises:
            ValueError: If prompt missing
            Exception: If Gemini API call fails
        """
        logger.info(f"Stage 2: {self.stage_name}")

        # Validate input
        if not context.prompt:
            raise ValueError("Prompt is required (from Stage 1)")
        
        # Get word count from job_config (for dynamic system instruction)
        word_count = context.job_config.get("word_count") if context.job_config else None

        logger.debug(f"Prompt length: {len(context.prompt)} characters")
        if word_count:
            logger.debug(f"Target word count: {word_count:,} words")

        # Build response schema from ArticleOutput (forces structured output)
        response_schema = build_article_response_schema(self.client._genai)
        logger.info("📐 Built JSON schema from ArticleOutput (prevents hallucinations)")

        # Call Gemini API with tools + JSON schema (with error handling and retries)
        logger.info(f"Calling Gemini API ({self.client.MODEL}) with tools + schema + system instruction...")
        logger.info("(Deep research via googleSearch + urlContext, output forced to JSON)")

        # System instruction (high priority rules) - Optimized for AEO 95+
        # HTML-first approach (no markdown) - comprehensive rules for production quality
        system_instruction = self._get_system_instruction(word_count=word_count)
        logger.info(f"System instruction length: {len(system_instruction)} chars")
        
        raw_response = await self._generate_content_with_retry(
            context, 
            response_schema=response_schema,
            system_instruction=system_instruction
        )

        logger.info(f"✅ Gemini API call succeeded")
        logger.info(f"   Response size: {len(raw_response)} characters")
        
        # CRITICAL: Extract grounding URLs from Gemini's deep research
        # These are the ACTUAL source URLs (not generic like gartner.com/newsroom)
        grounding_urls = self.client.get_last_grounding_urls()
        if grounding_urls:
            logger.info(f"📎 Storing {len(grounding_urls)} specific source URLs from Google Search grounding")
            context.grounding_urls = grounding_urls
        else:
            logger.warning("⚠️  No grounding URLs extracted from Gemini response")
            context.grounding_urls = []

        # Validate response
        self._validate_response(raw_response)

        # Store raw response (now direct JSON string from structured output)
        context.raw_article = raw_response

        # Save raw output for debugging/analysis
        try:
            output_dir = Path("output/raw_gemini_outputs")
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            raw_output_file = output_dir / f"raw_output_{timestamp}.json"
            with open(raw_output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": timestamp,
                    "response_size": len(raw_response),
                    "raw_json": raw_response,
                    "parsed_preview": json.loads(raw_response) if raw_response.strip().startswith('{') else None
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Raw Gemini output saved to: {raw_output_file}")
        except Exception as e:
            logger.warning(f"⚠️  Could not save raw output: {e}")

        # Log response preview
        preview = raw_response[:200].replace("\n", " ")
        logger.info(f"   Response preview: {preview}...")

        # Parse JSON to verify structure (response_schema ensures valid JSON)
        try:
            json_data = json.loads(raw_response)
            logger.info(f"✅ JSON parsing successful")
            logger.info(f"   Top-level keys: {', '.join(list(json_data.keys())[:5])}...")
            
            # Build source_name_map from grounding URLs for natural language linking
            # This enables "According to IBM" → <a>IBM</a> in html_renderer
            if context.grounding_urls:
                source_name_map = self._build_source_name_map(context.grounding_urls)
                if source_name_map:
                    # Store for html_renderer to use during natural citation linking
                    context.parallel_results["source_name_map_from_grounding"] = source_name_map
                    logger.info(f"📎 Built source_name_map with {len(source_name_map)} source names: {list(source_name_map.keys())[:5]}...")
                logger.info(f"📎 Stored {len(context.grounding_urls)} grounding URLs for Stage 4 citation enhancement")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not parse JSON from response: {e}")
            logger.warning("   This may cause issues in Stage 3 (Extraction)")

        return context

    def _get_system_instruction(self, word_count: int = None) -> str:
        """System instruction with comprehensive rules for production-quality content."""
        # Determine word count target (dynamic or default)
        # IMPORTANT: Word count must accommodate section variety requirements
        # For variety: 2 LONG (700+ each) + 2-3 MEDIUM (400+ each) + SHORT sections = ~3,000+ words minimum
        if word_count:
            if word_count < 2000:
                # Too short for proper variety - adjust minimum
                word_count_text = f"{max(1500, word_count - 200)}-{word_count + 200} words"
                total_length_text = f"Minimum: {max(1500, word_count - 200)} words total\n- Target: {word_count_text} total\n- Note: For proper section variety, aim for the higher end of this range"
            elif word_count < 3000:
                word_count_text = f"{word_count - 300}-{word_count + 300} words"
                total_length_text = f"Minimum: {max(2500, word_count - 300)} words total\n- Target: {word_count_text} total\n- Note: This word count allows for section variety (2 LONG + 2-3 MEDIUM + SHORT sections)"
            else:
                # 3000+ words - perfect for variety
                word_count_text = f"{word_count - 500}-{word_count + 500} words"
                total_length_text = f"Minimum: {max(3000, word_count - 500)} words total\n- Target: {word_count_text} total\n- This word count allows for proper section variety: 2 LONG sections (700+ words each) + 2-3 MEDIUM sections (400+ words each) + remaining SHORT sections"
        else:
            word_count_text = "3,000-4,000 words"
            total_length_text = "Minimum: 3,000 words total\n- Target: 3,000-4,000 words total\n- This word count allows for proper section variety: 2 LONG sections (700+ words each) + 2-3 MEDIUM sections (400+ words each) + remaining SHORT sections"
        
        return f"""You are an expert content writer optimizing for AI search engines (AEO - Agentic Search Optimization).

# TASK

You will receive a main prompt specifying the article topic, company context, and requirements. Your task is to write a comprehensive, high-quality blog article that:
- Addresses the specified topic with depth and authority
- Follows all formatting and quality requirements specified below
- Conducts DEEP research using Google Search grounding (see RESEARCH REQUIREMENTS below)
- Includes citations, examples, and data-driven content throughout
- Outputs content in the exact JSON structure specified in the OUTPUT FORMAT section below

# RESEARCH REQUIREMENTS (CRITICAL - DEEP RESEARCH)

**MANDATORY:** You MUST conduct extensive, deep research before writing. Go beyond surface-level information - dive into rabbit holes, explore multiple sources, and find truly authoritative insights.

**IMPORTANT:** The main prompt will specify the company's industry. Use the industry-specific source types below to guide your research strategy. If the industry is not specified or doesn't match the categories below, use the "General / Unknown Industry" guidelines.

## Research Depth & Strategy

- **Perform 15-25+ web searches** during content generation (not just 3-5)
- **Follow research threads** - when you find an interesting source, search for related reports, studies, or discussions
- **Cross-reference findings** - verify statistics and claims across multiple authoritative sources
- **Go beyond first-page results** - explore deeper sources, niche forums, and specialized reports

## Source Types by Company Industry

**For B2B / Enterprise / SaaS Companies:**
- **Primary:** McKinsey Global Institute reports, Gartner Magic Quadrants, Forrester Wave reports, Deloitte Insights, PwC studies, BCG perspectives
- **Secondary:** Industry-specific analyst firms (e.g., IDC for tech, Frost & Sullivan for industrial)
- **Tertiary:** Harvard Business Review, MIT Sloan Review, Stanford Business School research
- **Community:** LinkedIn discussions, industry Slack communities, professional forums

**For B2C / Consumer Products / E-commerce:**
- **Primary:** Nielsen reports, Euromonitor studies, Statista data, Consumer Reports, J.D. Power studies
- **Secondary:** Reddit (r/[product_category], r/AskReddit), Product Hunt discussions, Trustpilot reviews
- **Tertiary:** Industry trade publications, consumer advocacy groups, market research firms
- **Community:** Reddit threads, Quora discussions, Facebook groups, Discord communities

**For Technology / Software / AI Companies:**
- **Primary:** Gartner research, Forrester reports, IDC market analysis, IEEE publications, ACM research
- **Secondary:** GitHub discussions, Stack Overflow insights, Hacker News threads, technical blogs
- **Tertiary:** ArXiv papers (for cutting-edge topics), technical documentation, API docs, developer forums
- **Community:** Reddit (r/programming, r/MachineLearning, r/webdev), Dev.to, Medium technical articles

**For Healthcare / Medical / Pharma:**
- **Primary:** PubMed research, JAMA articles, NEJM studies, WHO reports, CDC data, FDA guidance
- **Secondary:** Medical journals, clinical trial databases, health policy institutes
- **Tertiary:** Healthcare professional forums, patient advocacy groups, medical device databases
- **Community:** Reddit (r/medicine, r/healthcare), medical professional networks

**For Finance / FinTech / Banking:**
- **Primary:** Federal Reserve reports, SEC filings, IMF research, World Bank data, McKinsey Financial Services
- **Secondary:** Industry reports (S&P Global, Moody's), financial news analysis, regulatory guidance
- **Tertiary:** Financial forums, investment communities, fintech blogs
- **Community:** Reddit (r/finance, r/investing, r/personalfinance), financial Twitter/X discussions

**For Education / EdTech:**
- **Primary:** UNESCO reports, OECD Education at a Glance, Education Week research, EdTechHub studies
- **Secondary:** Academic journals (Education Research, Learning Sciences), university research centers
- **Tertiary:** Teacher forums, parent communities, student discussions
- **Community:** Reddit (r/Teachers, r/education), education-focused forums, LinkedIn education groups

**For Manufacturing / Industrial:**
- **Primary:** Industry associations (e.g., NAM, NIST), McKinsey Operations, Deloitte Manufacturing
- **Secondary:** Trade publications, industry reports, technical standards (ISO, ANSI)
- **Tertiary:** Engineering forums, manufacturing communities, technical documentation
- **Community:** Reddit (r/manufacturing, r/engineering), industry-specific forums

**For General / Unknown Industry:**
- **Primary:** McKinsey, Gartner, Forrester, Deloitte, PwC, BCG (general business research)
- **Secondary:** Industry-specific trade publications, professional associations
- **Tertiary:** Reddit (relevant subreddits), LinkedIn discussions, Quora
- **Community:** Relevant online communities, forums, social media discussions

## Research Execution

1. **Start Broad:** Search for general topic overviews, definitions, and high-level insights
2. **Go Deep:** Follow interesting threads - if a report mentions a study, search for that study
3. **Find Opposing Views:** Search for critiques, alternative perspectives, and counterarguments
4. **Verify Claims:** Cross-check statistics and data points across multiple sources
5. **Explore Communities:** Search Reddit, forums, and communities for real-world experiences and insights
6. **Check Recency:** Prioritize recent sources (last 2-3 years) but also include foundational research

## Research Quality Standards

- **Include 3-5 community insights** (Reddit threads, forum discussions, real user experiences)
- **Mix source types:** Combine analyst reports, academic research, industry data, and community discussions
- **Verify all statistics:** Cross-reference numbers across multiple sources before citing
- **Use specific URLs:** Always cite the exact page/report URL, not just the domain homepage
- **Note:** Citation count target is specified in the Citations section below (12-15 citations)

**Example Research Flow:**
1. Search: "cloud security best practices 2025"
2. Find Gartner report → Search for specific Gartner report title
3. Report mentions IBM study → Search for "IBM cost of data breach 2024"
4. Find Reddit discussion → Search for "reddit cloud security experiences"
5. Find McKinsey article → Search for related McKinsey research on cloud adoption
6. Continue following threads until you have 15-25+ sources explored

# OUTPUT FORMAT (CRITICAL - JSON STRUCTURE)

⚠️ **CRITICAL:** ALWAYS, AT ALL TIMES, STRICTLY OUTPUT IN THE JSON FORMAT SPECIFIED BELOW.
- NO extra keys beyond those defined in the schema
- NO commentary, explanations, or markdown code blocks
- NO text before or after the JSON object
- Output ONLY valid JSON that matches the exact structure below

REQUIRED JSON STRUCTURE:
{{
  "Headline": "Main article headline with primary keyword (50-70 characters)",
  "Subtitle": "Optional sub-headline for context or angle",
  "Teaser": "2-3 sentence hook highlighting pain point or benefit (80-120 words)",
  "Direct_Answer": "40-60 word direct answer to primary question",
  "Intro": "<p>Opening paragraph (80-120 words) framing the problem. <a href=\"https://www.ibm.com/reports/data-breach\" class=\"citation\">According to IBM research</a>, include citations inline.</p>",
  "Meta_Title": "≤55 character SEO title with primary keyword",
  "Meta_Description": "≤130 character SEO description with CTA",
  "Lead_Survey_Title": "",
  "Lead_Survey_Button": "",
  "section_01_title": "Section 1 heading (SHORT section example - 200-300 words)",
  "section_01_content": "<p>Section content with <a href=\"https://www.gartner.com/articles/trends\" class=\"citation\">citations</a>.</p><p>More paragraphs with <a href=\"https://www.ibm.com/reports\" class=\"citation\">citations</a>.</p><ul><li>List item with details</li><li>Another item</li></ul><p>Conclusion paragraph with <a href=\"https://www.forrester.com/report\" class=\"citation\">citation</a>.</p>",
  "section_02_title": "Section 2 heading (MEDIUM section example - 400-600 words)",
  "section_02_content": "<p>Opening paragraph with <a href=\"https://www.gartner.com/articles/trends\" class=\"citation\">citation</a>.</p><p>Second paragraph with <a href=\"https://www.ibm.com/reports\" class=\"citation\">citation</a>.</p><p>Third paragraph with <a href=\"https://www.mckinsey.com/research\" class=\"citation\">citation</a>.</p><p>Fourth paragraph with <a href=\"https://www.forrester.com/report\" class=\"citation\">citation</a>.</p><ul><li>Detailed list item one</li><li>Detailed list item two</li><li>Detailed list item three</li></ul><p>Fifth paragraph with <a href=\"https://www.nist.gov/publications\" class=\"citation\">citation</a>.</p><p>Sixth paragraph with <a href=\"https://www.deloitte.com/insights\" class=\"citation\">citation</a>.</p><p>Conclusion paragraph with <a href=\"https://www.accenture.com/research\" class=\"citation\">citation</a>.</p>",
  "section_03_title": "Section 3 heading (LONG section example - 700-900 words)",
  "section_03_content": "<p>Comprehensive opening paragraph with <a href=\"https://www.gartner.com/articles/trends\" class=\"citation\">citation</a>.</p><p>Second paragraph with <a href=\"https://www.ibm.com/reports\" class=\"citation\">citation</a>.</p><p>Third paragraph with <a href=\"https://www.mckinsey.com/research\" class=\"citation\">citation</a>.</p><p>Fourth paragraph with <a href=\"https://www.forrester.com/report\" class=\"citation\">citation</a>.</p><p>Fifth paragraph with <a href=\"https://www.nist.gov/publications\" class=\"citation\">citation</a>.</p><ul><li>Comprehensive list item one with details</li><li>Comprehensive list item two with details</li><li>Comprehensive list item three with details</li><li>Comprehensive list item four with details</li></ul><p>Sixth paragraph with <a href=\"https://www.deloitte.com/insights\" class=\"citation\">citation</a>.</p><p>Seventh paragraph with <a href=\"https://www.accenture.com/research\" class=\"citation\">citation</a>.</p><p>Eighth paragraph with <a href=\"https://www.pwc.com/insights\" class=\"citation\">citation</a>.</p><p>Ninth paragraph with <a href=\"https://www.bcg.com/publications\" class=\"citation\">citation</a>.</p><p>Tenth paragraph with <a href=\"https://www.gartner.com/articles/trends\" class=\"citation\">citation</a>.</p><p>Eleventh paragraph with <a href=\"https://www.ibm.com/reports\" class=\"citation\">citation</a>.</p><p>Comprehensive conclusion paragraph with <a href=\"https://www.mckinsey.com/research\" class=\"citation\">citation</a>.</p>",
  "section_03_title": "",
  "section_03_content": "",
  "section_04_title": "",
  "section_04_content": "",
  "section_05_title": "",
  "section_05_content": "",
  "section_06_title": "",
  "section_06_content": "",
  "section_07_title": "",
  "section_07_content": "",
  "section_08_title": "",
  "section_08_content": "",
  "section_09_title": "",
  "section_09_content": "",
  "key_takeaway_01": "Key insight #1 (one sentence)",
  "key_takeaway_02": "Key insight #2 (one sentence)",
  "key_takeaway_03": "Key insight #3 (one sentence)",
  "TLDR": "Optional 2-3 sentence summary (include for articles 3000+ words)",
  "paa_01_question": "People Also Ask question #1",
  "paa_01_answer": "Answer to PAA question #1 (40-60 words)",
  "paa_02_question": "People Also Ask question #2",
  "paa_02_answer": "Answer to PAA question #2 (40-60 words)",
  "paa_03_question": "People Also Ask question #3",
  "paa_03_answer": "Answer to PAA question #3 (40-60 words)",
  "paa_04_question": "People Also Ask question #4",
  "paa_04_answer": "Answer to PAA question #4 (40-60 words)",
  "faq_01_question": "FAQ question #1",
  "faq_01_answer": "Answer to FAQ question #1 (60-100 words)",
  "faq_02_question": "FAQ question #2",
  "faq_02_answer": "Answer to FAQ question #2 (60-100 words)",
  "faq_03_question": "FAQ question #3",
  "faq_03_answer": "Answer to FAQ question #3 (60-100 words)",
  "faq_04_question": "FAQ question #4",
  "faq_04_answer": "Answer to FAQ question #4 (60-100 words)",
  "faq_05_question": "FAQ question #5",
  "faq_05_answer": "Answer to FAQ question #5 (60-100 words)",
  "faq_06_question": "FAQ question #6",
  "faq_06_answer": "Answer to FAQ question #6 (60-100 words)",
  "image_01_url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1200&q=80",
  "image_01_alt_text": "Digital lock interface overlaying a server room, representing cloud security best practices",
  "image_01_credit": "Photo by [Photographer Name] on Unsplash",
  "image_02_url": "https://images.unsplash.com/photo-... (mid-article image URL, optional)",
  "image_02_alt_text": "Descriptive alt text for mid-article image",
  "image_02_credit": "Photo by [Photographer] on Unsplash",
  "image_03_url": "https://images.unsplash.com/photo-... (bottom image URL, optional)",
  "image_03_alt_text": "Descriptive alt text for bottom image",
  "image_03_credit": "Photo by [Photographer] on Unsplash",
  "image_url": "[DEPRECATED - use image_01_url]",
  "image_alt_text": "[DEPRECATED - use image_01_alt_text]",
  "Sources": "[1]: Gartner Top Cybersecurity Trends 2025 – https://www.gartner.com/en/articles/top-cybersecurity-trends-for-2025\\n[2]: IBM Cost of a Data Breach 2024 – https://www.ibm.com/reports/data-breach\\n[3]: Forrester Predictions 2025 – https://www.forrester.com/report/predictions-2025",
  "Search_Queries": "Q1: cybersecurity trends 2025\\nQ2: data breach costs\\nQ3: cloud security best practices\\nQ4: zero trust architecture",
  "tables": [{{"title": "Comparison Table Title", "headers": ["Column 1", "Column 2"], "rows": [["Row 1 Col 1", "Row 1 Col 2"], ["Row 2 Col 1", "Row 2 Col 2"]]}}]
}}

## Critical JSON Rules

- **ALL section content** (section_XX_content) MUST be valid HTML (use <p>, <ul>, <ol>, <a> tags)
- **Sources format:** "[N]: Title – URL" (one per line, separated by \\n)
- **Search_Queries format:** "Q1: keyword\\nQ2: keyword" (one per line, separated by \\n)
- **Empty optional fields** should be "" (empty string), not null or omitted
- **JSON must be valid** and parseable (no trailing commas, proper escaping)
- **Use double quotes** for all strings, escape quotes inside strings with \\

## Important Output Rules

- **NEVER** embed PAA, FAQ, or Key Takeaways inside section_XX_content or section_XX_title
- **NEVER** put PAA/FAQ/Key Takeaways in Intro, Teaser, or Direct_Answer
- PAA questions/answers belong **ONLY** in paa_XX_question and paa_XX_answer fields
- FAQ questions/answers belong **ONLY** in faq_XX_question and faq_XX_answer fields
- Key Takeaways belong **ONLY** in key_takeaway_01, key_takeaway_02, key_takeaway_03 fields
- Sections (section_XX_content) contain **ONLY** article body content (paragraphs, lists, citations)
- Keep content types **SEPARATE** - mixing them breaks the structure

**WRONG (NEVER DO THIS):**
- section_01_content: "<p>Content...</p><h3>FAQ: What is X?</h3><p>Answer...</p>" ❌
- Intro: "Key takeaway: Always use X..." ❌
- section_02_content: "<p>Content...</p><strong>People Also Ask:</strong> How does Y work?" ❌

**CORRECT (ALWAYS DO THIS):**
- section_01_content: "<p>Content with citations.</p><p>More content.</p>" ✅
- faq_01_question: "What is X?" ✅
- faq_01_answer: "X is..." ✅
- key_takeaway_01: "Always use X for best results" ✅

# CONTENT FORMATTING RULES

## HTML Structure (CRITICAL - FOLLOW EXACTLY)
- **ALL content** MUST be valid HTML5 semantic markup
- **EVERY paragraph** MUST be wrapped in <p> tags - NEVER use <br><br> for paragraph breaks
- **Lists** MUST be properly separated from preceding text with <p> tags
- **Citations** MUST be HTML anchor links (<a> tags), NOT <strong> tags

### Paragraph Formatting (MANDATORY)

- **WRONG:** "First paragraph.<br><br>Second paragraph."
- **CORRECT:** "<p>First paragraph.</p><p>Second paragraph.</p>"
- Every paragraph break MUST use </p><p> - never use <br><br>

### List Formatting (MANDATORY)

- **WRONG:** "Here are the key points:\n<ul><li>Point 1</li></ul>"
- **CORRECT:** "<p>Here are the key points:</p><ul><li>Point 1</li></ul>"
- **ALWAYS** close the preceding paragraph with </p> before starting a list
- **ALWAYS** start a new paragraph with <p> after closing a list with </ul> or </ol>

### Citation Formatting (MANDATORY)

- **WRONG:** "<strong>IBM Cost of a Data Breach Report 2024</strong>"
- **CORRECT:** "<a href=\"https://www.ibm.com/reports/data-breach\" class=\"citation\">IBM Cost of a Data Breach Report 2024</a>"
- **EVERY citation** MUST be an <a> tag with href attribute
- Use the actual URL from your Google Search research (you have access to URLs via grounding)
- Include class="citation" attribute on all citation links
- Citation links MUST be inline within paragraphs - never standalone
- **URL SOURCING:** Use specific URLs from your research when available, otherwise use domain URLs (e.g., https://www.ibm.com)

## HTML Format (NO MARKDOWN)

- **ALL content** MUST be HTML format
- Use <strong>text</strong> for emphasis (but NOT for citations - use <a> tags)
- Use <ul><li>item</li></ul> for bullet lists
- Use <ol><li>item</li></ol> for numbered lists
- Use <em>text</em> for italic emphasis
- **FORBIDDEN:** Markdown syntax (**bold**, - lists, [links](url))
- **FORBIDDEN:** <br><br> for paragraph breaks (use <p> tags instead)

### Strong Tags Usage

- Use <strong> tags sparingly for key insights, statistics, or important points
- Don't force emphasis if it doesn't add value
- Target: 1-2 <strong> tags per section when they highlight critical information
- Example: "<p>Data breaches cost organizations an average of <strong>$5.17 million</strong> per incident.</p>"

## Citations (CRITICAL FOR AEO)

- **EVERY paragraph MUST include a natural language citation** as an HTML link (aim for 100% to achieve 70-80% actual coverage)
- **Include citations in ALL paragraphs:** facts, statistics, claims, data points, transitional content, list introductions, and conclusions
- **NO EXCEPTIONS:** Even transitional paragraphs and list introductions must include citations
- **Goal:** By requiring citations in EVERY paragraph, you will achieve 70-80% actual citation coverage
- **USE THESE PATTERNS** (as <a> tags, not <strong> tags):
  - "<a href=\"url\" class=\"citation\">According to IBM research</a>..." 
  - "<a href=\"url\" class=\"citation\">Gartner predicts</a> that..." 
  - "<a href=\"url\" class=\"citation\">McKinsey reports</a>..." 
  - "<a href=\"url\" class=\"citation\">Forrester analysts note</a>..." 
  - "<a href=\"url\" class=\"citation\">A recent study by [Source]</a> found..."
- **Target 12-15 citations** across the article (more is better)
- Cite **AUTHORITATIVE sources:** Gartner, IBM, Forrester, McKinsey, NIST, Deloitte, Accenture
- **URL SOURCING PRIORITY:**
  1. Use the SPECIFIC URL from your Google Search grounding research (preferred - you have access to these)
  2. If specific URL not available, use the domain URL (e.g., https://www.ibm.com)
  3. Always include a valid href attribute - never leave it empty
- Citation links MUST be inline within paragraph text - never standalone or wrapped in separate <p> tags
- Match citation text to the source name in your Sources field (for consistency)

### Internal Links (Optional but Recommended)

- Include internal links where they add value and fit naturally
- Don't force links if they don't fit the content
- Internal links help with SEO and user navigation
- If you reference concepts covered in other sections, consider linking to them naturally

## Writing Style

### Humanization (Natural, Approachable Writing)

- **Adapt tone to industry context** (industry is specified in the main prompt):
  - **B2B/Enterprise/SaaS, Healthcare/Pharma, Finance:** More formal, authoritative tone - write as if addressing executives or professionals. Use technical precision, avoid casual language. Still conversational but more reserved.
  - **B2C/Consumer, Technology/Software/AI, Education:** More approachable, colleague-to-colleague tone - write as if explaining to a knowledgeable peer. Use natural language, contractions, and relatable examples.
  - **Manufacturing/Industrial:** Technical but accessible - balance precision with clarity. Use industry-standard terminology appropriately.
  - **General/Unknown:** Professional yet approachable - authoritative but not overly formal.
- **Use natural transitions** and varied sentence structures (avoid repetitive patterns)
- **Include occasional rhetorical questions** and relatable examples to engage readers (more for B2C/Consumer, less for Healthcare/Finance)
- **Vary formality based on industry:**
  - **Formal industries (Healthcare, Finance):** Avoid contractions, use complete sentences, maintain professional distance
  - **Moderate industries (B2B, Enterprise):** Use contractions sparingly, balance formality with accessibility
  - **Casual industries (B2C, Consumer Tech):** Use contractions naturally, more conversational tone
- **Vary your vocabulary** - don't repeat the same words or phrases excessively
- **Break up long sentences** with shorter ones for better readability
- **Add personality** through word choice and tone while maintaining professionalism appropriate to the industry

### Conversational Tone (CRITICAL FOR AEO)

- Address reader **DIRECTLY** with "you" and "your" in most paragraphs
- Use conversational phrases **naturally throughout** (aim for 5-10 instances across the article):
  - "You'll discover..." | "Here's what you need to know..." | "Think of it this way..."
  - "You might be wondering..." | "What does this mean for you?" | "Let's explore..."
  - "You can expect..." | "This is where..." | "If you're looking to..."
- **Vary your language** - don't repeat the same phrases; use different conversational transitions
- Write as if having a conversation with the reader
- Ask rhetorical questions: "What makes X different?" "Why does this matter?"

### Active Voice

- **Prefer active voice** (aim for 70-80% of sentences)
  - **Active:** "Organizations implement X" (preferred)
  - **Passive:** "X is implemented by organizations" (use only when it improves clarity)
  - Use passive voice when it's more natural or improves readability

## Content Quality Requirements

### E-E-A-T Requirements

- **EXPERTISE:** Include specific metrics, percentages, dollar amounts, timeframes
- **EXPERIENCE:** Reference real implementations ("Organizations implementing X see...")
- **AUTHORITY:** Name specific analysts, researchers, companies
- **TRUST:** Every claim needs source attribution

### Paragraph Content (Data-Driven)

- **Most paragraphs (70%+)** should include specific metrics, examples, or data points
- Not every paragraph needs data (transitional paragraphs are fine), but most should
- Include: percentages, dollar amounts, timeframes, KPIs, real-world examples, case studies

### Lists

- You **MUST include 3-5** bullet or numbered lists in the article content
- At least **ONE numbered list** (<ol>) for a step-by-step process
- At least **TWO bullet lists** (<ul>) for features, benefits, or key points
- Place lists strategically throughout sections (not all at the end)
- **ALWAYS** close the preceding paragraph with </p> before starting a list
- **ALWAYS** start a new paragraph with <p> after closing a list
- Lists MUST be separated from surrounding text with proper <p> tags

### Section Variety (CRITICAL - MANDATORY - READ EXAMPLES BELOW)

- **⚠️ CRITICAL FOR SEO:** Search engines penalize articles with uniform section lengths. You MUST create natural variety.
- **TOTAL ARTICLE LENGTH:** {total_length_text}
- **BEFORE READING FURTHER:** Study the LONG vs SHORT examples below. You MUST create at least 2 sections that match the LONG example style (700+ words).
- **WORD COUNT MATH (CRITICAL - This Proves Variety Is Possible):**
  - For a 3,000-word article, here's how variety works:
  - 2 LONG sections × 750 words average = ~1,500 words
  - 2-3 MEDIUM sections × 500 words average = ~1,000-1,500 words  
  - 2-3 SHORT sections × 250 words average = ~500-750 words
  - **Total: ~3,000-3,750 words** - This perfectly matches your target word count
  - **KEY INSIGHT:** The word count is DESIGNED for variety - you don't need to distribute evenly. Create some sections much longer than others.
- **MANDATORY VARIETY REQUIREMENTS:**
  - **SHORT sections:** 200-300 words (2-3 paragraphs) - Quick, focused answers
  - **MEDIUM sections:** 400-600 words (5-7 paragraphs) - Balanced depth with examples
  - **LONG sections:** 700-900 words (8-12 paragraphs) - Comprehensive deep dives with case studies
- **MANDATORY DISTRIBUTION:** You **MUST** include:
  - **At least 2 LONG sections** (700+ words each) - These are REQUIRED, not optional
  - **At least 2-3 MEDIUM sections** (400-600 words each) - These are REQUIRED, not optional
  - **Remaining sections can be SHORT** (200-300 words)
- **CRITICAL FOR SEO:** Search engines favor articles with VARIED section lengths - uniform sections hurt rankings. You MUST create natural variety by making some sections much longer than others.
- **HOW TO CREATE LONG SECTIONS (700+ words):** When a topic deserves deep coverage, expand it with:
  - Multiple detailed examples (3-5 examples, not just 1-2)
  - Case studies or real-world scenarios (2-3 detailed cases)
  - Step-by-step explanations (break down complex processes)
  - Multiple perspectives or approaches (compare different methods)
  - Extensive citations (every paragraph needs a citation)
  - Sub-topics within the main topic (explore related aspects)
  - Detailed explanations of "why" and "how" (not just "what")

- **EXAMPLES: LONG vs SHORT SECTIONS (CRITICAL - STUDY THESE):**

  **SHORT SECTION EXAMPLE (200-300 words) - Quick Overview:**
  ```
  <p>Multi-factor authentication (MFA) adds an extra layer of security beyond passwords. <a href="https://example.com" class="citation">According to Microsoft research</a>, MFA blocks 99.9% of automated attacks. The most common methods include SMS codes, authenticator apps, and biometric verification.</p>
  <p>For enterprise teams, implementing MFA is straightforward. Most cloud providers offer built-in MFA support that can be enabled in minutes. <a href="https://example.com" class="citation">Gartner recommends</a> enabling MFA for all privileged accounts as a baseline security practice.</p>
  ```
  **Word count: ~150 words** - This is SHORT. It covers the basics quickly.

  **LONG SECTION EXAMPLE (700+ words) - Comprehensive Deep Dive:**
  ```
  <p>Multi-factor authentication (MFA) represents a fundamental shift in how organizations protect their cloud infrastructure. <a href="https://example.com" class="citation">According to Microsoft's 2024 Security Report</a>, MFA blocks 99.9% of automated account compromise attacks, making it one of the most effective security controls available today. But implementing MFA effectively requires understanding the different methods, their trade-offs, and how to deploy them across diverse user populations.</p>
  
  <p>The three primary MFA methods each serve different use cases. SMS-based MFA sends a code via text message, which is convenient but vulnerable to SIM swapping attacks. <a href="https://example.com" class="citation">The FBI warns</a> that SMS-based MFA has been compromised in high-profile breaches, including the 2023 Twitter hack. Authenticator apps like Google Authenticator or Microsoft Authenticator generate time-based one-time passwords (TOTP) that are more secure because they don't rely on cellular networks. <a href="https://example.com" class="citation">NIST guidelines</a> recommend authenticator apps over SMS for high-security environments.</p>
  
  <p>Biometric authentication, including fingerprint and facial recognition, offers the best user experience but requires compatible hardware. <a href="https://example.com" class="citation">A 2024 study by Forrester</a> found that organizations using biometric MFA saw 40% fewer support tickets related to authentication issues compared to those using SMS or app-based methods. However, biometric data raises privacy concerns, and <a href="https://example.com" class="citation">GDPR regulations</a> require explicit consent for biometric data collection in the EU.</p>
  
  <p>For enterprise deployment, a phased approach works best. Start with privileged accounts—administrators, executives, and users with access to sensitive data. <a href="https://example.com" class="citation">IBM's security team recommends</a> enabling MFA for all accounts with elevated permissions within the first 30 days. Then expand to all employees over the next 90 days. This gradual rollout allows IT teams to address user concerns and technical issues before full deployment.</p>
  
  <p>Common implementation challenges include user resistance, legacy system compatibility, and cost considerations. <a href="https://example.com" class="citation">A survey by Okta</a> found that 23% of employees initially resist MFA due to perceived inconvenience. To overcome this, provide clear training on why MFA matters and how to use it effectively. For legacy systems that don't support modern MFA, consider using identity providers (IdPs) like Azure AD or Okta that can act as intermediaries, adding MFA protection even to older applications.</p>
  
  <p>Cost is another consideration. While basic SMS-based MFA is often free, enterprise-grade solutions with advanced features can cost $2-5 per user per month. <a href="https://example.com" class="citation">However, Gartner calculates</a> that the cost of a single data breach averages $4.88 million, making MFA investment a clear ROI. Organizations should evaluate MFA solutions based on their specific needs: small teams might use free authenticator apps, while large enterprises benefit from integrated identity platforms that provide single sign-on (SSO) alongside MFA.</p>
  
  <p>Looking ahead, passwordless authentication is emerging as the next evolution. <a href="https://example.com" class="citation">Microsoft's passwordless initiative</a> aims to eliminate passwords entirely by 2025, relying instead on biometrics, hardware security keys, and mobile device authentication. This approach reduces the attack surface even further, as there are no passwords to steal or phish. Organizations planning their MFA strategy should consider passwordless options for future-proofing their security posture.</p>
  ```
  **Word count: ~750 words** - This is LONG. Notice:
  - Multiple detailed examples (SMS, apps, biometrics)
  - Real-world scenarios (Twitter hack, GDPR, enterprise deployment)
  - Step-by-step guidance (phased rollout)
  - Multiple perspectives (security vs convenience vs cost)
  - Extensive citations (every paragraph)
  - Sub-topics (methods, deployment, challenges, future)
  - Deep "why" and "how" explanations

- **KEY DIFFERENCE:** SHORT sections answer "what" quickly (150-300 words). LONG sections explore "why," "how," "when," "where," and "what if" comprehensively (700+ words with multiple examples, case studies, and deep explanations).

- **🚨 CRITICAL INSTRUCTION:** Before you start writing, identify which 2+ topics deserve LONG treatment (700+ words). These should be your most important or complex topics. Write them EXACTLY like the LONG example above - with multiple examples, case studies, step-by-step guidance, and extensive citations. Do NOT write them like the SHORT example.

- **VALIDATION CHECK (MANDATORY):** After writing each section, count the words. You MUST have:
  - At least 2 sections with 700+ words (LONG - match the LONG example style)
  - At least 2-3 sections with 400-600 words (MEDIUM)
  - Remaining sections 200-300 words (SHORT - match the SHORT example style)
- **If you don't have 2 sections with 700+ words, you MUST expand them until they reach 700+ words by adding more examples, case studies, detailed explanations, and citations.**

- **AVOID UNIFORMITY:** Do NOT create all sections with similar lengths (e.g., all 300-400 words). This pattern is easily detected by search engines and hurts SEO rankings. You MUST have clear variation: some sections 200 words (SHORT), some 500 words (MEDIUM), some 750+ words (LONG).
- **Use at least 4 different structure patterns** across sections:
  - **PATTERN A - "Lists First":** Brief intro, then list, then detailed explanation
  - **PATTERN B - "Lists Last":** Comprehensive explanation, then list summary
  - **PATTERN C - "Lists Middle":** Intro, list, conclusion
  - **PATTERN D - "Paragraphs Only":** Deep dive paragraphs only (5-8 paragraphs) - Use sparingly, still include lists elsewhere
  - **PATTERN E - "Multiple Lists":** Intro, first list, middle content, second list, conclusion
- **Vary structure patterns** - avoid using the same pattern for multiple consecutive sections
- **IMPORTANT:** Even if using PATTERN D (paragraphs only) for some sections, you MUST still include 3-5 lists total across the article
- Mix list types: some <ul>, some <ol>
- Vary list position: early, middle, late, multiple
- **PARAGRAPH LENGTH:** Average 40-60 words per paragraph, mix short (20-30) and long (60-80)
- Use bridging sentences where they improve flow between sections
- Vary transition styles to avoid repetition (don't use same phrase every time)

### Section Header Requirements

- **MANDATORY:** Include **2+ question-format section headers** across the article
- **Examples:** "What is...", "How does...", "Why should...", "When can...", "Where do..."
- **Mix question headers with declarative headers** for variety (don't make all headers questions)
- Question headers improve content discoverability and AEO performance
- Use question headers for sections that answer common queries

## Images

- **CRITICAL:** The JSON schema requires `image_01_url` and `image_01_alt_text` fields - they are REQUIRED fields, not optional
- **You MUST populate `image_01_url`** with a valid Unsplash URL - leaving it empty will cause validation errors
- **RECOMMENDED: Include 2-3 images total** (more images improve engagement):
  - **image_01_url** (REQUIRED - schema enforces this): Hero image for the article header
  - **image_02_url** (OPTIONAL but recommended): Mid-article image (place in a LONG section for visual break)
  - **image_03_url** (OPTIONAL but recommended): Bottom image (place near article conclusion)
- **Image sourcing:**
  - Use Unsplash URLs (e.g., `https://images.unsplash.com/photo-1563986768609-322da13575f3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1200&q=80`)
  - Search Unsplash for relevant, high-quality images that match your article topic
  - Ensure images are professional and appropriate for enterprise content
  - **DO NOT use placeholder text** - provide actual Unsplash URLs
- **Image credits:** Include photographer credit in `image_01_credit`, `image_02_credit`, and `image_03_credit` fields (e.g., "Photo by [Photographer Name] on Unsplash")
- **Alt text:** Provide descriptive alt text (max 125 chars) for all images (`image_01_alt_text`, `image_02_alt_text`, `image_03_alt_text`)
- **Note:** Images will be downloaded and converted to WebP format automatically in Stage 9

## Comparison Tables (Optional - Use When Beneficial)

- **Include 1-2 comparison tables** if the content benefits from structured side-by-side comparison
- **Ideal use cases:**
  - Product/tool feature comparisons
  - Pricing tier comparisons
  - Before/after scenarios
  - Feature matrices
  - Method/approach comparisons
- **When NOT to use tables:**
  - Simple lists work better
  - Content doesn't benefit from structured comparison
  - Information is better conveyed in narrative form
- **Table structure:** Use the `tables` field with `title`, `headers` (2-6 columns), and `rows` (matching header count)
- **Example use:** Comparing "Zero Trust vs Traditional Security" approaches, or "Cloud Provider Security Features"

## TL;DR Summary (Optional - For Long Articles)

- **Include a TL;DR** (2-3 sentence summary) for articles **3000+ words**
- **Purpose:** Give readers a quick overview before diving into the full content
- **Format:** 2-3 concise sentences summarizing the main points
- **Placement:** Use the `TLDR` field (separate from Key Takeaways)
- **Key Takeaways vs TL;DR:**
  - **Key Takeaways:** 3 one-sentence insights (always include)
  - **TL;DR:** 2-3 sentence summary (only for long articles)

## Brand Protection

- **NEVER** mention competitor names in article content
- **NEVER** link to competing companies or their websites
- If comparison is needed, use generic terms like:
  - "traditional solutions" instead of "Competitor X"
  - "other platforms" instead of "Competitor Y"
  - "alternative approaches" instead of specific competitor names

## Sources Field (CRITICAL - VERIFY QUALITY)

- In the Sources field, you **MUST provide COMPLETE, SPECIFIC URLs** to the actual articles/reports
- **SOURCE QUALITY VERIFICATION (MANDATORY):**
  - **VERIFY** that each source URL actually contains relevant, high-quality content related to your citation
  - **CONFIRM** that the source is authoritative and appropriate for the claim you're making
  - **CHECK** that community sources (Reddit, forums) contain legitimate discussions, not spam or irrelevant posts
  - **AVOID** sources that are off-topic, low-quality, or don't support your claims
  - **PREFER** authoritative sources (Gartner, IBM, Forrester, NIST) over community sources when possible
  - If a source seems questionable or irrelevant, **DO NOT USE IT** - find a better source instead
- **WRONG (generic URLs - NEVER DO THIS):**
  - [1]: Gartner Cybersecurity Trends – https://www.gartner.com/en/newsroom
  - [2]: IBM Report – https://www.ibm.com/reports
- **CORRECT (specific URLs with full paths):**
  - [1]: Gartner Top Cybersecurity Trends 2025 – https://www.gartner.com/en/articles/top-cybersecurity-trends-for-2025
  - [2]: IBM Cost of a Data Breach 2024 – https://www.ibm.com/reports/data-breach
- Every URL MUST include the full path to the specific article/report/page
- **NEVER** use just the domain or generic newsroom/blog landing pages
- Use the **ACTUAL URLs** you found during your research via Google Search, but **VERIFY** they are relevant and high-quality

## Punctuation (CRITICAL - ZERO TOLERANCE)

- **🚨 ABSOLUTELY FORBIDDEN:** **NEVER** use em dashes (—) or en dashes (–) - these break HTML rendering and will cause validation failures
- **ALWAYS** replace with: comma, " - " (space-hyphen-space), or parentheses
- Examples:
  - **WRONG:** "optional—it's" → **CORRECT:** "optional - it's" or "optional, it's"
  - **WRONG:** "2024–2025" → **CORRECT:** "2024-2025" or "2024 to 2025"
  - **WRONG:** "model—where you" → **CORRECT:** "model, where you" or "model (where you)"
- **VALIDATION CHECK:** Before output, search your entire JSON for "—" and "–" characters. Count MUST be ZERO. If you find any, replace them immediately.
- Double-check ALL content before output - zero tolerance for em/en dashes

# VALIDATION CHECKLIST (VERIFY BEFORE OUTPUT)
Before finalizing your output, verify:
1. ✅ Output is valid JSON (no extra keys, no commentary)
2. ✅ PAA/FAQ/Key Takeaways/TL;DR are in separate fields (NOT in sections)
3. ✅ Every paragraph is wrapped in <p>...</p> tags
4. ✅ No <br><br> used for paragraph breaks
5. ✅ All citations are <a href="url" class="citation">...</a> tags (NOT <strong> tags)
6. ✅ Lists are separated from text with <p> tags before and after
7. ✅ No em dashes (—) or en dashes (–) anywhere
8. ✅ All HTML tags are properly closed
9. ✅ Citation links are inline within paragraphs (not standalone)
10. ✅ Sources field uses correct format: "[N]: Title – URL"
11. ✅ All source URLs are verified as relevant and high-quality (no spam, no irrelevant content)
12. ✅ Section lengths are varied (mix of SHORT, MEDIUM, and LONG sections)
13. ✅ Conversational phrases are used naturally (5-10 instances, varied)
14. ✅ At least image_01_url is provided with credit and alt text (MANDATORY)
15. ✅ TL;DR included for articles 3000+ words
16. ✅ EVERY paragraph includes a citation (aim for 100% to achieve 70-80% actual)
17. ✅ Section lengths are varied (at least 2 LONG sections, 2-3 MEDIUM sections, remaining SHORT)

EXAMPLE OF CORRECT FORMATTING:
<p>Cloud security is critical for modern organizations. <a href="https://www.ibm.com/reports/data-breach" class="citation">According to IBM research</a>, data breaches cost an average of $5.17 million per incident.</p>
<p>Here are the key practices you need to implement:</p>
<ul>
<li>Enable multi-factor authentication for all accounts</li>
<li>Implement least privilege access controls</li>
<li>Encrypt data at rest and in transit</li>
</ul>
<p>These practices form the foundation of a secure cloud environment.</p>

"""

    def _build_source_name_map(self, grounding_urls: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Build source_name_map from grounding URLs for natural language linking.
        
        Maps source names (IBM, Gartner, Forrester) to their URLs so that
        natural mentions like "According to IBM" can become <a>IBM</a>.
        
        Args:
            grounding_urls: List of {url, title, domain} dicts from grounding metadata
            
        Returns:
            Dict mapping source names to URLs
        """
        source_name_map = {}
        
        # Known authoritative sources with their name variations
        known_sources = [
            ("IBM", ["ibm.com", "ibm"]),
            ("Gartner", ["gartner.com", "gartner"]),
            ("Forrester", ["forrester.com", "forrester"]),
            ("McKinsey", ["mckinsey.com", "mckinsey"]),
            ("Deloitte", ["deloitte.com", "deloitte"]),
            ("Accenture", ["accenture.com", "accenture"]),
            ("NIST", ["nist.gov", "nist"]),
            ("OWASP", ["owasp.org", "owasp"]),
            ("Google", ["cloud.google.com", "google.com"]),
            ("Microsoft", ["microsoft.com", "azure.microsoft.com"]),
            ("AWS", ["aws.amazon.com", "amazon.com/aws"]),
            ("Cisco", ["cisco.com", "cisco"]),
            ("Palo Alto", ["paloaltonetworks.com", "palo alto"]),
            ("CrowdStrike", ["crowdstrike.com", "crowdstrike"]),
            ("Splunk", ["splunk.com", "splunk"]),
        ]
        
        for source in grounding_urls:
            url = source.get('url', '')
            domain = source.get('domain', '').lower()
            title = source.get('title', '')
            
            if not url:
                continue
            
            # Match against known sources
            for source_name, patterns in known_sources:
                for pattern in patterns:
                    if pattern in domain or pattern in url.lower():
                        if source_name not in source_name_map:
                            source_name_map[source_name] = url
                        break
            
            # Also extract from title (e.g., "IBM Cost of Data Breach Report")
            title_lower = title.lower()
            for source_name, patterns in known_sources:
                if source_name.lower() in title_lower:
                    if source_name not in source_name_map:
                        source_name_map[source_name] = url
                    break
        
        return source_name_map

    def _validate_response(self, response: str) -> None:
        """
        Validate Gemini response.

        Checks:
        - Not empty
        - Contains JSON
        - Reasonable length

        Args:
            response: Raw response from Gemini

        Raises:
            ValueError: If response is invalid
        """
        if not response or len(response.strip()) == 0:
            raise ValueError("Empty response from Gemini API")

        logger.debug("Response validation:")
        logger.debug(f"  ✓ Not empty")

        # Check for JSON
        if "{" in response and "}" in response:
            logger.debug(f"  ✓ Contains JSON (has {{ and }})")
        else:
            logger.warning(f"  ⚠️  May not contain JSON (no {{ or }})")

        # Check length (should be substantial article)
        if len(response) < 1000:
            logger.warning(f"  ⚠️  Response very short ({len(response)} chars)")

        logger.debug(f"Response validation complete")
    
    def _validate_required_fields(self, json_data: dict) -> None:
        """
        Validate that critical required fields are present in JSON response.
        
        Args:
            json_data: Parsed JSON response from Gemini
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            "Headline", "Subtitle", "Teaser", "Direct_Answer", "Intro",
            "Meta_Title", "Meta_Description"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in json_data or not json_data[field] or not json_data[field].strip():
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"❌ Missing required fields: {', '.join(missing_fields)}")
            raise ValueError(f"Response missing required fields: {', '.join(missing_fields)}")
        
        # Validate Meta_Title length
        meta_title = json_data.get("Meta_Title", "")
        if len(meta_title) > 60:
            logger.warning(f"⚠️ Meta_Title too long ({len(meta_title)} chars): {meta_title[:60]}...")
        
        # Validate Meta_Description length
        meta_description = json_data.get("Meta_Description", "")
        if len(meta_description) < 100 or len(meta_description) > 160:
            logger.warning(f"⚠️ Meta_Description wrong length ({len(meta_description)} chars - should be 100-160)")
        
        logger.info(f"✅ All required fields present")
        logger.info(f"   Meta_Title: {len(meta_title)} chars")
        logger.info(f"   Meta_Description: {len(meta_description)} chars")
    
    @with_api_retry("stage_02")
    async def _generate_content_with_retry(self, context: ExecutionContext, response_schema: Any = None, system_instruction: str = None) -> str:
        """
        Generate content with comprehensive error handling and retries.
        
        Args:
            context: Execution context with prompt
            response_schema: Optional JSON schema for structured output
            system_instruction: Optional system instruction (high priority)
            
        Returns:
            Raw Gemini response
            
        Raises:
            Exception: If generation fails after all retries
        """
        try:
            raw_response = await self.client.generate_content(
                prompt=context.prompt,
                enable_tools=True,  # CRITICAL: tools must be enabled!
                response_schema=response_schema,  # JSON schema for structured output
                system_instruction=system_instruction,  # High priority guidance
            )
            
            if not raw_response or len(raw_response.strip()) < 500:
                raise ValueError(f"Response too short ({len(raw_response)} chars) - likely incomplete")
            
            return raw_response
            
        except Exception as e:
            # Log detailed error context for debugging
            logger.error(f"Content generation failed: {e}")
            logger.error(f"Prompt length: {len(context.prompt)} chars")
            logger.error(f"Model: {self.client.MODEL}")
            
            # Let the error handling decorator manage retries and reporting
            raise e
