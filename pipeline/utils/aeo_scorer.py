"""AEO (Agentic Search Optimization) scoring utility."""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple

from ..models.output_schema import ArticleOutput

logger = logging.getLogger(__name__)


class AEOScorer:
    """
    Score content for AEO (Agentic Search Optimization).
    
    AEO optimizes content for AI search engines like Google AI Overviews,
    ChatGPT, Perplexity, etc.
    """

    def __init__(self):
        """Initialize AEO scorer."""
        self.max_score = 100.0

    def _detect_language(self, content: str, primary_keyword: str) -> str:
        """
        Simple language detection based on common words and primary keyword.

        Args:
            content: Article content to analyze
            primary_keyword: Primary keyword (can indicate language)

        Returns:
            Language code: 'en', 'de', 'fr', etc. (defaults to 'en')
        """
        content_lower = content.lower()

        # Common German words (high frequency)
        german_indicators = ['und', 'der', 'die', 'das', 'ist', 'sie', 'für', 'mit', 'auf', 'werden', 'kann', 'eine', 'einem', 'eines', 'können', 'sollte']
        german_count = sum(1 for word in german_indicators if f' {word} ' in f' {content_lower} ')

        # Common English words (high frequency)
        english_indicators = ['the', 'and', 'for', 'with', 'that', 'this', 'from', 'can', 'will', 'are', 'have', 'should', 'would']
        english_count = sum(1 for word in english_indicators if f' {word} ' in f' {content_lower} ')

        # Check primary keyword for non-ASCII characters (indicates non-English)
        has_german_chars = any(char in primary_keyword.lower() for char in ['ä', 'ö', 'ü', 'ß'])

        # Decision logic
        if has_german_chars or german_count > english_count * 1.5:
            return 'de'
        elif english_count > german_count:
            return 'en'
        else:
            # Default to English if unclear
            return 'en'

    def score_article(
        self,
        output: ArticleOutput,
        primary_keyword: str,
        input_data: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
    ) -> float:
        """
        Calculate AEO optimization score for an article.

        Args:
            output: Article output schema
            primary_keyword: Primary keyword/topic
            input_data: Optional input schema for E-E-A-T scoring
            language: Optional language code ('en', 'de', etc.). If not provided, will auto-detect.

        Returns:
            AEO score (0-100)
        """
        scores = {}
        details = {}

        # Detect language if not provided
        if not language:
            all_content = output.Intro + " " + self._get_all_section_content(output)
            language = self._detect_language(all_content, primary_keyword)
            logger.debug(f"Auto-detected language: {language}")

        # 1. Direct Answer (25 points)
        scores['direct_answer'], details['direct_answer'] = self._score_direct_answer(output, primary_keyword)

        # 2. Q&A Format (20 points)
        scores['qa_format'], details['qa_format'] = self._score_qa_format(output)

        # 3. Citation Clarity (15 points)
        scores['citation_clarity'], details['citation_clarity'] = self._score_citation_clarity(output)

        # 4. Natural Language (15 points) - language-aware
        scores['natural_language'], details['natural_language'] = self._score_natural_language(output, primary_keyword, language)

        # 5. Structured Data (10 points)
        scores['structured_data'], details['structured_data'] = self._score_structured_data(output)

        # 6. E-E-A-T (15 points)
        if input_data:
            scores['eat'], details['eat'] = self._score_eat(output, input_data)
        else:
            scores['eat'] = 0.0
            details['eat'] = ["No input data provided for E-E-A-T scoring"]

        # Total score
        total_score = sum(scores.values())

        # Store detailed breakdown for logging
        self._last_score_details = {
            'scores': scores,
            'details': details,
            'total': total_score
        }

        # Log detailed breakdown
        logger.info("=" * 70)
        logger.info("AEO SCORE BREAKDOWN")
        logger.info("=" * 70)
        logger.info(f"TOTAL SCORE: {total_score:.1f}/100")
        logger.info("")

        # Log each component with details
        for component, score in scores.items():
            max_score = self._get_max_score_for_component(component)
            percentage = (score / max_score * 100) if max_score > 0 else 0
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 60 else "❌"

            logger.info(f"{status} {component.replace('_', ' ').title()}: {score:.1f}/{max_score} ({percentage:.0f}%)")

            # Log details for this component
            component_details = details.get(component, [])
            for detail in component_details:
                logger.info(f"   {detail}")
            logger.info("")

        logger.info("=" * 70)

        return min(total_score, self.max_score)

    def _get_max_score_for_component(self, component: str) -> float:
        """Get maximum possible score for a component."""
        max_scores = {
            'direct_answer': 25.0,
            'qa_format': 20.0,
            'citation_clarity': 15.0,
            'natural_language': 15.0,
            'structured_data': 10.0,
            'eat': 15.0,
        }
        return max_scores.get(component, 0.0)

    def _score_direct_answer(
        self,
        output: ArticleOutput,
        primary_keyword: str,
    ) -> Tuple[float, List[str]]:
        """
        Score direct answer presence and quality (25 points).

        Checks:
        - Direct answer field exists (10 points)
        - Direct answer length 40-60 words (5 points)
        - Direct answer contains primary keyword (5 points)
        - Direct answer contains citation (academic OR natural) (5 points)

        Returns:
            Tuple of (score, details list)
        """
        score = 0.0
        details = []

        # Check if direct answer exists
        if output.Direct_Answer and output.Direct_Answer.strip():
            score += 10.0
            details.append("✅ Direct answer exists (+10)")

            direct_answer = output.Direct_Answer
            # Strip HTML for accurate word count (HTML tags shouldn't count as words)
            direct_answer_text = re.sub(r'<[^>]+>', '', direct_answer)
            direct_answer_lower = direct_answer_text.lower()

            # Check length (40-60 words ideal)
            word_count = len(direct_answer_text.split())
            if 40 <= word_count <= 60:
                score += 5.0
                details.append(f"✅ Ideal length: {word_count} words (+5)")
            elif 30 <= word_count < 40 or 60 < word_count <= 80:
                score += 2.5
                details.append(f"⚠️ Acceptable length: {word_count} words (+2.5, ideal: 40-60)")
            else:
                details.append(f"❌ Poor length: {word_count} words (+0, ideal: 40-60)")

            # Check if contains primary keyword
            # For long multi-word keywords (4+ words), be more flexible - check for core terms
            keyword_words = primary_keyword.lower().split()

            if primary_keyword.lower() in direct_answer_lower:
                # Exact match - always give full points
                score += 5.0
                details.append(f"✅ Contains keyword '{primary_keyword}' (+5)")
            elif len(keyword_words) >= 4:
                # For long phrases (4+ words), check if core terms appear
                # Core terms = first 2 words + last word (most semantically important)
                core_terms = keyword_words[:2] + [keyword_words[-1]]
                matches = sum(1 for term in core_terms if term in direct_answer_lower and len(term) > 2)  # Ignore short words like "is", "to"

                if matches >= 2:
                    # Partial credit for having core terms
                    score += 3.5
                    matched_terms = [term for term in core_terms if term in direct_answer_lower and len(term) > 2]
                    details.append(f"⚠️ Contains core terms {matched_terms} from '{primary_keyword}' (+3.5, partial credit)")
                else:
                    details.append(f"❌ Missing keyword '{primary_keyword}' and core terms (+0)")
            else:
                # For short keywords (1-3 words), require exact match
                details.append(f"❌ Missing keyword '{primary_keyword}' (+0)")

            # Check if contains citation (academic [1] OR natural language OR HTML citation tags)
            # NOTE: We check original Direct_Answer field (academic citations [N] are present here)
            # The HTML renderer strips [N] citations in final output, but AEO scorer runs before that
            has_academic_citation = re.search(r'\[\d+\]', direct_answer)  # Check original field

            # Check for HTML citation links (e.g., <a href="#source-1" class="citation">...)
            has_html_citation = re.search(r'<a[^>]*class=["\']citation["\'][^>]*>.*?</a>', direct_answer, re.IGNORECASE)

            has_natural_citation = any([
                # "According to X" patterns
                re.search(r'according to [A-Z]', direct_answer_text, re.IGNORECASE),

                # "X reports/states/notes/found" patterns (RELAXED - no "that" required)
                re.search(r'[A-Z][a-z]+ (?:reports?|states?|notes?|found|shows?|reveals?)', direct_answer_text),

                # "Research by/from X" patterns
                re.search(r'research (?:by|from) [A-Z]', direct_answer_text, re.IGNORECASE),

                # "X research" patterns (e.g., "Gartner research")
                re.search(r'[A-Z][a-z]+ research', direct_answer_text, re.IGNORECASE),

                # "Study by X" patterns
                re.search(r'study (?:by|from) [A-Z]', direct_answer_text, re.IGNORECASE),

                # "X's report/study/analysis" patterns
                re.search(r"[A-Z][a-z]+'s (?:report|study|analysis|research)", direct_answer_text),

                # "Data from X" patterns
                re.search(r'data from [A-Z]', direct_answer_text, re.IGNORECASE),
            ])

            if has_academic_citation or has_natural_citation or has_html_citation:
                score += 5.0
                citation_type = "academic [N]" if has_academic_citation else ("HTML citation tag" if has_html_citation else "natural language")
                details.append(f"✅ Contains citation ({citation_type}) (+5)")
            else:
                details.append("❌ Missing citation (+0)")
        else:
            details.append("❌ Direct answer field missing (+0)")
            # Fallback: check if intro starts with direct answer
            if output.Intro:
                intro_words = output.Intro.split()[:60]
                if len(intro_words) >= 30:
                    intro_text = " ".join(intro_words).lower()
                    if primary_keyword.lower() in intro_text:
                        score += 5.0  # Partial credit
                        details.append("⚠️ Partial credit: intro contains keyword (+5)")

        return min(score, 25.0), details

    def _score_qa_format(self, output: ArticleOutput) -> Tuple[float, List[str]]:
        """
        Score Q&A format presence (20 points).

        Checks:
        - FAQ section exists with 5-6 items (10 points)
        - PAA section exists with 3-4 items (5 points)
        - Question-format headers in content (5 points)

        Returns:
            Tuple of (score, details list)
        """
        score = 0.0
        details = []

        # FAQ section (target: 5-6 items)
        faq_count = output.get_active_faqs()
        if faq_count >= 5:
            score += 10.0
            details.append(f"✅ FAQ count: {faq_count} items (+10, target: 5+)")
        elif faq_count >= 3:
            score += 7.0  # Partial credit for 3-4 FAQ
            details.append(f"⚠️ FAQ count: {faq_count} items (+7, target: 5+)")
        elif faq_count > 0:
            score += 3.0
            details.append(f"❌ FAQ count: {faq_count} items (+3, target: 5+)")
        else:
            details.append("❌ No FAQs found (+0, target: 5+)")

        # PAA section (target: 3-4 items)
        paa_count = output.get_active_paas()
        if paa_count >= 3:
            score += 5.0
            details.append(f"✅ PAA count: {paa_count} items (+5, target: 3+)")
        elif paa_count >= 2:
            score += 3.0  # Partial credit for 2 PAA
            details.append(f"⚠️ PAA count: {paa_count} items (+3, target: 3+)")
        elif paa_count > 0:
            score += 1.0
            details.append(f"❌ PAA count: {paa_count} items (+1, target: 3+)")
        else:
            details.append("❌ No PAAs found (+0, target: 3+)")

        # Question-format headers in content (H2/H3 with questions)
        all_content = output.Intro + " " + self._get_all_section_content(output)
        # Check section titles for question format
        question_headers = 0
        sections = [
            output.section_01_title, output.section_02_title, output.section_03_title,
            output.section_04_title, output.section_05_title, output.section_06_title,
            output.section_07_title, output.section_08_title, output.section_09_title,
        ]
        for section_title in sections:
            if section_title:
                title_lower = section_title.lower()
                if any(q in title_lower for q in ["what is", "how does", "why does", "when should", "where can", "what are", "how can"]):
                    question_headers += 1

        if question_headers >= 2:
            score += 5.0
            details.append(f"✅ Question-format headers: {question_headers} found (+5, target: 2+)")
        elif question_headers >= 1:
            score += 2.5
            details.append(f"⚠️ Question-format headers: {question_headers} found (+2.5, target: 2+)")
        else:
            details.append("❌ No question-format headers found (+0, target: 2+)")

        return min(score, 20.0), details

    def _score_citation_clarity(self, output: ArticleOutput) -> Tuple[float, List[str]]:
        """
        Score citation clarity for AI extraction (15 points).

        Supports BOTH citation styles:
        - Academic: [1], [2], [3]
        - Natural language: "according to IBM", "Gartner reports", "research by McKinsey"

        Checks:
        - Citations present (academic or natural) (5 points)
        - Sources list exists and is populated (5 points)
        - Citations distributed per-paragraph (5 points)

        Returns:
            Tuple of (score, details list)
        """
        score = 0.0
        details = []

        all_content = output.Intro + " " + self._get_all_section_content(output)
        content_lower = all_content.lower()

        # Check ALL citation formats (academic, natural language, AND HTML)
        # 1. Academic: [1], [2], etc.
        # NOTE: We check original ArticleOutput fields (before HTML renderer strips [N] citations)
        # The HTML renderer strips [N] citations in final output, but AEO scorer runs before that
        academic_citations = re.findall(r'\[\d+\]', all_content)

        # 2. HTML citation links (e.g., <a href="#source-1" class="citation">...)
        # This is the PREFERRED format from the prompt
        html_citations = re.findall(r'<a[^>]*class=["\']citation["\'][^>]*>.*?</a>', all_content, re.IGNORECASE)

        # 3. Natural language citations (inline attribution)
        # Patterns should match common citation formats - RELAXED to accept more variations
        natural_citation_patterns = [
            # "according to X" patterns - allow any word
            r'according to \w+',

            # "per X" patterns (common in professional writing)
            r'per \w+ research',
            r'per \w+ report',
            r'per \w+ study',
            r'per \w+ data',

            # "X reports/states/notes" patterns - with capital letter
            r'[A-Z][a-z]+ reports?',
            r'[A-Z][a-z]+ reports? that',
            r'[A-Z][a-z]+ states?',
            r'[A-Z][a-z]+ states? that',
            r'[A-Z][a-z]+ notes?',
            r'[A-Z][a-z]+ notes? that',
            r'[A-Z][a-z]+ predicts?',
            r'[A-Z][a-z]+ estimates?',
            r'[A-Z][a-z]+ found',
            r'[A-Z][a-z]+ found that',
            r'[A-Z][a-z]+ shows?',
            r'[A-Z][a-z]+ shows? that',
            r'[A-Z][a-z]+ highlights?',

            # "research/study/report by X" patterns
            r'research by \w+',
            r'report by \w+',
            r'study by \w+',
            r'data from \w+',

            # "X's research/report" patterns
            r"\w+'s research",
            r"\w+'s report",
            r"\w+'s study",
        ]
        natural_citations = []
        for pattern in natural_citation_patterns:
            natural_citations.extend(re.findall(pattern, all_content, re.IGNORECASE))

        total_citations = len(academic_citations) + len(html_citations) + len(natural_citations)

        # Citation count scoring (graduated scale) (5 points)
        if total_citations >= 12:
            score += 5.0  # Excellent
            details.append(f"✅ Total citations: {total_citations} ({len(academic_citations)} academic, {len(html_citations)} HTML, {len(natural_citations)} natural) (+5, target: 12+)")
        elif total_citations >= 8:
            score += 4.0  # Good
            details.append(f"✅ Total citations: {total_citations} ({len(academic_citations)} academic, {len(html_citations)} HTML, {len(natural_citations)} natural) (+4, target: 12+)")
        elif total_citations >= 5:
            score += 3.0  # Acceptable
            details.append(f"⚠️ Total citations: {total_citations} ({len(academic_citations)} academic, {len(html_citations)} HTML, {len(natural_citations)} natural) (+3, target: 12+)")
        elif total_citations >= 3:
            score += 2.0  # Minimal
            details.append(f"❌ Total citations: {total_citations} ({len(academic_citations)} academic, {len(html_citations)} HTML, {len(natural_citations)} natural) (+2, target: 12+)")
        else:
            details.append(f"❌ Total citations: {total_citations} ({len(academic_citations)} academic, {len(html_citations)} HTML, {len(natural_citations)} natural) (+0, target: 12+)")

        # Unique source count scoring (graduated scale) (5 points)
        if output.Sources and output.Sources.strip():
            source_lines = [line.strip() for line in output.Sources.split('\n') if line.strip()]
            unique_sources = len(source_lines)

            if unique_sources >= 7:
                score += 5.0  # Excellent diversity
                details.append(f"✅ Unique sources: {unique_sources} (+5, target: 7+)")
            elif unique_sources >= 5:
                score += 4.0  # Good diversity
                details.append(f"✅ Unique sources: {unique_sources} (+4, target: 7+)")
            elif unique_sources >= 3:
                score += 3.0  # Acceptable diversity
                details.append(f"⚠️ Unique sources: {unique_sources} (+3, target: 7+)")
            else:
                details.append(f"❌ Unique sources: {unique_sources} (+0, target: 7+)")
        else:
            details.append("❌ No sources found (+0)")

        # Citation distribution per-paragraph (5 points)
        # Check both academic AND natural citations per paragraph
        # NOTE: We check original ArticleOutput fields (academic citations [N] are present here)
        paragraphs = re.findall(r'<p[^>]*>.*?</p>', all_content, re.DOTALL)
        if not paragraphs:
            # Fallback: split by double newlines or single newlines if content is plain text
            paragraphs = [p for p in all_content.split('\n\n') if p.strip()]
            if not paragraphs:
                # Last resort: split by periods followed by space (sentence boundaries)
                sentences = re.split(r'\.\s+', all_content)
                paragraphs = [s.strip() for s in sentences if len(s.strip()) > 50]  # Only meaningful sentences

        paragraphs_with_citations = 0
        for para in paragraphs:
            # Count academic citations
            para_academic = len(re.findall(r'\[\d+\]', para))

            # Count HTML citations
            para_html = len(re.findall(r'<a[^>]*class=["\']citation["\'][^>]*>.*?</a>', para, re.IGNORECASE))

            # Count natural citations
            para_natural = 0
            for pattern in natural_citation_patterns:
                para_natural += len(re.findall(pattern, para, re.IGNORECASE))

            # A paragraph is well-cited if it has 1+ citations (any style)
            if para_academic + para_html + para_natural >= 1:
                paragraphs_with_citations += 1

        # Paragraph distribution scoring (graduated scale) (5 points)
        if paragraphs:
            distribution_ratio = paragraphs_with_citations / len(paragraphs)

            if distribution_ratio >= 0.40:  # 40%+ cited
                score += 5.0  # Excellent
                details.append(f"✅ Citation distribution: {paragraphs_with_citations}/{len(paragraphs)} paragraphs ({distribution_ratio:.0%}) (+5, target: 40%+)")
            elif distribution_ratio >= 0.30:  # 30-39% cited
                score += 4.0  # Good
                details.append(f"✅ Citation distribution: {paragraphs_with_citations}/{len(paragraphs)} paragraphs ({distribution_ratio:.0%}) (+4, target: 40%+)")
            elif distribution_ratio >= 0.20:  # 20-29% cited
                score += 3.0  # Acceptable
                details.append(f"⚠️ Citation distribution: {paragraphs_with_citations}/{len(paragraphs)} paragraphs ({distribution_ratio:.0%}) (+3, target: 40%+)")
            elif distribution_ratio >= 0.10:  # 10-19% cited
                score += 2.0  # Low
                details.append(f"❌ Citation distribution: {paragraphs_with_citations}/{len(paragraphs)} paragraphs ({distribution_ratio:.0%}) (+2, target: 40%+)")
            else:
                details.append(f"❌ Citation distribution: {paragraphs_with_citations}/{len(paragraphs)} paragraphs ({distribution_ratio:.0%}) (+0, target: 40%+)")
        else:
            details.append("❌ No paragraphs found for distribution analysis (+0)")

        logger.debug(f"Citation scoring: {len(academic_citations)} academic, {len(html_citations)} HTML, {len(natural_citations)} natural, {paragraphs_with_citations}/{len(paragraphs) if paragraphs else 0} paragraphs cited")

        return min(score, 15.0), details

    def _score_natural_language(
        self,
        output: ArticleOutput,
        primary_keyword: str,
        language: str = "en",
    ) -> Tuple[float, List[str]]:
        """
        Score natural language usage (15 points).

        NOTE: Currently only supports English. Non-English articles will receive 0 points
        but with a clear explanation rather than false negatives.

        Checks:
        - Conversational phrases (6 points)
        - Direct statements (not vague) (5 points)
        - Natural question patterns (4 points)

        Args:
            output: Article output
            primary_keyword: Primary keyword
            language: Language code ('en', 'de', etc.)

        Returns:
            Tuple of (score, details list)
        """
        score = 0.0
        details = []

        # Skip scoring for non-English content (temporary until multi-language support is added)
        if language != "en":
            details.append(f"ℹ️ Natural language scoring skipped (language: {language.upper()}, currently only supports English)")
            details.append("   This is not a penalty - your content may have conversational phrases in the target language")
            details.append("   Future updates will add multi-language support for German, French, Spanish, etc.")
            logger.info(f"Natural language scoring skipped for language: {language}")
            return 0.0, details

        all_content = output.Intro + " " + self._get_all_section_content(output)
        content_lower = all_content.lower()

        # Conversational phrases (enhanced scoring)
        # NOTE: Excludes question patterns ("what is", "how does", etc.) - those are scored separately in question_patterns below
        # Extended conversational phrase list (matches injection list)
        conversational_phrases = [
            "how to",  # Keep "how to" (instructional, not a question pattern)
            "you can", "you'll", "you should", "let's", "here's", "this is",
            "we'll", "that's", "when you", "if you", "so you can", "which means",
            "it's", "there's", "here are", "let me", "you might", "you may",
        ]
        phrase_count = sum(1 for phrase in conversational_phrases if phrase in content_lower)
        if phrase_count >= 8:
            score += 6.0
            details.append(f"✅ Conversational phrases: {phrase_count} found (+6, target: 8+)")
        elif phrase_count >= 5:
            score += 4.0
            details.append(f"⚠️ Conversational phrases: {phrase_count} found (+4, target: 8+)")
        elif phrase_count >= 2:
            score += 2.0
            details.append(f"❌ Conversational phrases: {phrase_count} found (+2, target: 8+)")
        else:
            details.append(f"❌ Conversational phrases: {phrase_count} found (+0, target: 8+)")

        # Direct statements (not vague)
        vague_patterns = [
            r"might be",
            r"could be",
            r"possibly",
            r"perhaps",
            r"maybe",
        ]
        vague_count = sum(1 for pattern in vague_patterns if re.search(pattern, content_lower))

        # Direct statements (action verbs and definitive language)
        # REMOVED: "is", "are", "does" - too common, cause false positives
        # Focus on action verbs that indicate direct, confident statements
        direct_patterns = [
            r"\bprovides\b",
            r"\benables\b",
            r"\ballows\b",
            r"\bhelps\b",
            r"\bensures\b",
            r"\bguarantees\b",
            r"\bdelivers\b",
            r"\boffers\b",
            r"\bsupports\b",
            r"\bfacilitates\b",
            r"\bimplements\b",
            r"\bcreates\b",
            r"\bimproves\b",
            r"\boptimizes\b",
        ]
        direct_count = sum(1 for pattern in direct_patterns if re.search(pattern, content_lower))

        # Only score if we have significantly more direct statements than vague ones
        # Threshold increased since we removed common words
        if vague_count == 0 and direct_count >= 5:  # No vague language, several direct action verbs
            score += 5.0
            details.append(f"✅ Direct statements: {direct_count} direct, {vague_count} vague (+5)")
        elif direct_count > vague_count * 3 and direct_count >= 3:  # Much more direct than vague
            score += 5.0
            details.append(f"✅ Direct statements: {direct_count} direct, {vague_count} vague (+5)")
        elif direct_count > vague_count * 2 and direct_count >= 2:  # More direct than vague
            score += 3.0
            details.append(f"⚠️ Direct statements: {direct_count} direct, {vague_count} vague (+3)")
        elif direct_count > vague_count:  # Somewhat more direct
            score += 1.0
            details.append(f"❌ Direct statements: {direct_count} direct, {vague_count} vague (+1)")
        else:
            details.append(f"❌ Direct statements: {direct_count} direct, {vague_count} vague (+0, too vague)")

        # Natural question patterns (enhanced)
        # Use word boundaries to avoid false positives like "somewhat is" matching "what is"
        question_patterns = [
            r"\bwhat is\b",
            r"\bhow do\b",
            r"\bwhy does\b",
            r"\bwhen should\b",
            r"\bwhere can\b",
            r"\bhow can\b",
            r"\bwhat are\b",
        ]
        question_count = sum(1 for pattern in question_patterns if re.search(pattern, content_lower))
        if question_count >= 5:
            score += 4.0
            details.append(f"✅ Natural question patterns: {question_count} found (+4, target: 5+)")
        elif question_count >= 3:
            score += 3.0
            details.append(f"⚠️ Natural question patterns: {question_count} found (+3, target: 5+)")
        elif question_count >= 1:
            score += 1.5
            details.append(f"❌ Natural question patterns: {question_count} found (+1.5, target: 5+)")
        else:
            details.append("❌ No natural question patterns found (+0, target: 5+)")

        return min(score, 15.0), details

    def _score_structured_data(self, output: ArticleOutput) -> Tuple[float, List[str]]:
        """
        Score structured data presence (10 points).

        Checks:
        - Lists (ul/ol) present (5 points)
        - Headings structure (H2/H3) (5 points)

        Note: Section titles are stored in section_XX_title fields and count as H2 equivalents.

        Returns:
            Tuple of (score, details list)
        """
        score = 0.0
        details = []

        all_content = output.Intro + " " + self._get_all_section_content(output)

        # Lists
        list_count = all_content.count("<ul>") + all_content.count("<ol>")
        if list_count >= 3:
            score += 5.0
            details.append(f"✅ Lists found: {list_count} (+5, target: 3+)")
        elif list_count >= 1:
            score += 2.5
            details.append(f"⚠️ Lists found: {list_count} (+2.5, target: 3+)")
        else:
            details.append("❌ No lists found (+0, target: 3+)")

        # Headings structure - count both HTML tags AND section titles
        # Section titles are equivalent to H2 tags
        section_titles = [
            output.section_01_title, output.section_02_title, output.section_03_title,
            output.section_04_title, output.section_05_title, output.section_06_title,
            output.section_07_title, output.section_08_title, output.section_09_title,
        ]
        section_title_count = sum(1 for t in section_titles if t and t.strip())

        # Count explicit H2/H3 tags in content
        h2_in_content = all_content.count("<h2>")
        h3_in_content = all_content.count("<h3>")

        # Total H2 count = section titles + explicit H2 tags
        h2_count = section_title_count + h2_in_content
        h3_count = h3_in_content

        if h2_count >= 3 and (h3_count >= 2 or h2_count >= 5):
            score += 5.0
            details.append(f"✅ Headings structure: {h2_count} H2s, {h3_count} H3s (+5)")
        elif h2_count >= 2:
            score += 2.5
            details.append(f"⚠️ Headings structure: {h2_count} H2s, {h3_count} H3s (+2.5, target: 3+ H2s and 2+ H3s)")
        else:
            details.append(f"❌ Headings structure: {h2_count} H2s, {h3_count} H3s (+0, target: 3+ H2s and 2+ H3s)")

        return min(score, 10.0), details
    
    def _score_eat(self, output: ArticleOutput, input_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Score E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) (15 points).

        Checks:
        - Experience: Author bio mentions experience (4 points)
        - Expertise: Credentials/qualifications mentioned (4 points)
        - Authoritativeness: Author URL/social proof (4 points)
        - Trustworthiness: Source credibility (3 points)

        Returns:
            Tuple of (score, details list)
        """
        score = 0.0
        details = []

        # DEBUG: Log input_data structure
        logger.info(f"[E-A-T DEBUG] input_data keys: {list(input_data.keys())}")
        logger.info(f"[E-A-T DEBUG] input_data structure: {input_data}")

        # Extract author data - try root level first, then check nested company_info
        # This handles both flat structure and nested structure for backward compatibility
        author_bio = input_data.get('author_bio')
        author_url = input_data.get('author_url')
        author_name = input_data.get('author_name')

        logger.info(f"[E-A-T DEBUG] Root level - author_name: {author_name}, author_bio: {author_bio[:50] if author_bio else None}, author_url: {author_url}")

        # If not found at root level, check nested company_info structure
        if not author_bio or not author_url or not author_name:
            company_info = input_data.get('company_info', {})
            if isinstance(company_info, dict):
                author_bio = author_bio or company_info.get('author_bio')
                author_url = author_url or company_info.get('author_url')
                author_name = author_name or company_info.get('author_name')
                logger.info(f"[E-A-T DEBUG] company_info level - author_name: {author_name}, author_bio: {author_bio[:50] if author_bio else None}, author_url: {author_url}")

        # Experience: Author bio mentions experience
        if author_bio:
            experience_keywords = ["experience", "worked", "years", "expertise", "background"]
            if any(keyword in str(author_bio).lower() for keyword in experience_keywords):
                score += 4.0
                details.append("✅ Experience: Author bio mentions experience keywords (+4)")
            else:
                score += 2.0  # Partial credit if bio exists
                details.append("⚠️ Experience: Author bio exists but lacks experience keywords (+2)")
        else:
            details.append("❌ Experience: No author bio provided (+0)")

        # Expertise: Credentials/qualifications
        if author_bio:
            expertise_keywords = ["degree", "certified", "phd", "master", "bachelor", "qualification", "certification"]
            if any(keyword in str(author_bio).lower() for keyword in expertise_keywords):
                score += 4.0
                details.append("✅ Expertise: Credentials/qualifications found in bio (+4)")
            else:
                score += 1.0  # Partial credit
                details.append("⚠️ Expertise: Bio exists but lacks credentials (+1)")
        else:
            details.append("❌ Expertise: No author bio provided (+0)")

        # Authoritativeness: Author URL/social proof
        # (author_url and author_name already extracted above)
        if author_url:
            score += 4.0
            details.append("✅ Authoritativeness: Author URL provided (+4)")
        elif author_name:
            score += 2.0  # Partial credit if name exists
            details.append("⚠️ Authoritativeness: Author name provided but no URL (+2)")
        else:
            details.append("❌ Authoritativeness: No author URL or name (+0)")

        # Trustworthiness: Source credibility
        if output.Sources and output.Sources.strip():
            # Check if sources are from credible domains
            # Include both academic (.edu, .gov) AND tech industry sources (.com)
            credible_domains = [
                ".edu", ".gov", ".org",  # Academic/government
                "gartner.com", "forrester.com", "mckinsey.com", "ibm.com", "microsoft.com",  # Tech industry
                "nist.gov", "owasp.org", "sans.org",  # Security standards
                "wikipedia", "research", "study"
            ]
            source_lines = [line.strip() for line in output.Sources.split('\n') if line.strip()]
            credible_count = sum(
                1 for line in source_lines
                if any(domain in line.lower() for domain in credible_domains)
            )
            # Also give credit for multiple sources (even if not in credible list)
            if credible_count >= 2:
                score += 3.0
                details.append(f"✅ Trustworthiness: {credible_count} credible sources found (+3, target: 2+)")
            elif credible_count >= 1:
                score += 1.5
                details.append(f"⚠️ Trustworthiness: {credible_count} credible source found (+1.5, target: 2+)")
            elif len(source_lines) >= 5:
                score += 1.0  # Partial credit for multiple sources
                details.append(f"⚠️ Trustworthiness: {len(source_lines)} sources but not from credible domains (+1)")
            elif len(source_lines) >= 3:
                score += 0.5  # Minimal credit for some sources
                details.append(f"❌ Trustworthiness: {len(source_lines)} sources but not from credible domains (+0.5)")
            else:
                details.append(f"❌ Trustworthiness: Only {len(source_lines)} sources (+0, target: 5+)")
        else:
            details.append("❌ Trustworthiness: No sources provided (+0)")

        return min(score, 15.0), details
    
    def _get_all_section_content(self, output: ArticleOutput) -> str:
        """Get all section content as a single string."""
        sections = [
            output.section_01_content, output.section_02_content, output.section_03_content,
            output.section_04_content, output.section_05_content, output.section_06_content,
            output.section_07_content, output.section_08_content, output.section_09_content,
        ]
        return " ".join(s for s in sections if s)

