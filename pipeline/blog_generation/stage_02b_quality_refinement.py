"""
Stage 2b: Quality Refinement

🛡️ LAYER 2 (Detection + Best-Effort Fix)

This stage is part of a 3-layer production quality system:
- Layer 1: Prevention (main prompt rules)
- Layer 2: Detection + best-effort Gemini fix (this stage) [NON-BLOCKING]
- Layer 3: Guaranteed regex cleanup (html_renderer.py)

Detects quality issues:
1. Keyword over-optimization (too many mentions)
2. First paragraph too short
3. AI language markers (em dashes, robotic phrases)

Attempts Gemini-based surgical edits via RewriteEngine.
If Gemini fails, Layer 3 (regex) will catch remaining issues.

Runs AFTER Stage 3 (Extraction) but BEFORE Stage 4-9 (Parallel stages).
Only executes if quality issues are detected.
"""

import logging
import re
from typing import Dict, List, Any, Optional

from ..core import ExecutionContext, Stage
from ..models.output_schema import ArticleOutput
from ..rewrites import (
    RewriteEngine,
    RewriteInstruction,
    RewriteMode,
    targeted_rewrite
)

logger = logging.getLogger(__name__)


class QualityIssue:
    """
    Represents a detected quality issue.
    """
    def __init__(
        self,
        issue_type: str,
        severity: str,
        description: str,
        current_value: Any,
        target_value: Any,
        field: str
    ):
        self.issue_type = issue_type
        self.severity = severity  # "critical", "warning", "info"
        self.description = description
        self.current_value = current_value
        self.target_value = target_value
        self.field = field
    
    def __repr__(self):
        return f"QualityIssue({self.issue_type}, {self.severity}, field={self.field})"


class QualityRefinementStage(Stage):
    """
    Stage 2b: Quality Refinement (conditional).
    
    Detects and fixes quality issues in Gemini output:
    - Keyword over/under-optimization
    - Paragraph length issues
    - AI language markers
    
    Uses RewriteEngine for surgical edits.
    """
    
    stage_num = 2  # Runs between Stage 2 and 3
    stage_name = "Quality Refinement"
    
    # Quality thresholds
    KEYWORD_TARGET_MIN = 5
    KEYWORD_TARGET_MAX = 8
    FIRST_PARAGRAPH_MIN_WORDS = 60
    FIRST_PARAGRAPH_MAX_WORDS = 100
    
    # AI marker patterns
    AI_MARKERS = {
        "em_dash": "—",
        "en_dash": "–",
        "robotic_phrases": [
            "Here's how",
            "Here's what",
            "Key points:",
            "Key benefits include:",
            "Important considerations:",
            "That's why similarly",
            "If you want another",
            "You'll find to",
            "Here are key points:",
            "Here are the key points:",
            "Here are key takeaways:",
        ]
    }
    
    # COMPREHENSIVE QUALITY CHECKLIST
    # These are the issues Stage 2b must detect and fix
    QUALITY_CHECKLIST = """
    STAGE 2b QUALITY CHECKLIST - All issues to detect and fix:
    
    1. DUPLICATE BULLET LISTS
       Problem: Paragraph followed by <ul><li> that repeats the same content
       Example: "<p>AI improves X, Y, Z.</p><ul><li>AI improves X</li><li>Y</li><li>Z</li></ul>"
       Fix: Remove the duplicate bullet list, keep only the paragraph
    
    2. TRUNCATED LIST ITEMS
       Problem: List items cut off mid-sentence without punctuation
       Example: "<li>The best practice for 2025 is platformization - consolidating point solutions into</li>"
       Fix: Complete the sentence or remove the truncated item
    
    3. MALFORMED NESTED LISTS
       Problem: Improper HTML nesting like </p> inside <li>, or <ul> inside <li><ul>
       Example: "<ul><li>Text</p><ul><li>Nested</li></ul></li></ul>"
       Fix: Flatten the list structure, ensure proper HTML nesting
    
    4. ORPHANED INCOMPLETE PARAGRAPHS
       Problem: Paragraphs that are just "This" or incomplete sentences
       Example: "<p>This </p>" or "<p>. Also, the</p>"
       Fix: Remove the orphaned paragraph or complete it
    
    5. MISSING SOURCES
       Problem: Sources mentioned in text (IBM, Gartner, Forrester) not in Sources section
       Fix: Ensure all referenced sources appear in the Sources field with proper URLs
    
    6. ACADEMIC CITATIONS [N] IN BODY
       Problem: [1], [2], [1][2] markers appear directly in content
       Fix: Convert to natural language: "according to IBM" or remove
    
    7. EM DASHES AND EN DASHES
       Problem: — and – characters that look robotic
       Fix: Replace with regular hyphens or rewrite sentence
    
    8. ROBOTIC SUMMARY PHRASES
       Problem: "Here are key points:" followed by bullet list duplicating content
       Fix: Remove the phrase and the redundant list
    
    9. PERIOD AT START OF PARAGRAPH/LIST
       Problem: ". Also," or ". 3. Identity" at start of content
       Fix: Remove the orphaned period
    
    10. LOWERCASE AFTER PERIOD
        Problem: "sentence ends. new sentence" (lowercase after period)
        Fix: Capitalize the first letter after the period
    """
    
    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 2b: Detect and fix quality issues.
        
        NEW FLOW (Dec 2024):
        1. REGEX CLEANUP FIRST - fast, deterministic fixes
        2. GEMINI REVIEW - semantic fixes that need AI
        
        Args:
            context: ExecutionContext with structured_data from Stage 2
        
        Returns:
            Updated context with refined structured_data
        """
        logger.info(f"Stage 2b: {self.stage_name}")
        
        # Validate input
        if not context.structured_data:
            logger.warning("No structured_data available, skipping refinement")
            return context
        
        # ============================================================
        # STEP 1: REGEX CLEANUP (deterministic, fast)
        # ============================================================
        logger.info("🔧 Step 1: Applying regex cleanup...")
        context = self._apply_regex_cleanup(context)
        
        # ============================================================
        # STEP 2: GEMINI REVIEW (MANDATORY - always runs)
        # ============================================================
        logger.info("🤖 Step 2: Gemini quality review (MANDATORY)...")
        context = await self._gemini_full_review(context)
        
        # Log any remaining issues (for transparency)
        remaining_issues = self._detect_quality_issues(context)
        if remaining_issues:
            logger.info(f"📊 Post-review status: {len(remaining_issues)} minor issues detected")
            logger.info("🛡️  Layer 3 (html_renderer.py) will handle any remaining cleanup")
        else:
            logger.info("✅ All quality checks passed")
        
        return context
    
    def _apply_regex_cleanup(self, context: ExecutionContext) -> ExecutionContext:
        """
        Apply deterministic regex fixes to all content fields.
        
        These are fast, reliable fixes that don't need AI:
        - Em/en dashes → hyphens
        - Academic citations [N] → remove
        - Duplicate summary lists → remove
        - Double prefixes → fix
        - Truncated fragment lists → remove
        """
        data = context.structured_data
        if not data:
            return context
        
        # Get all fields as dict
        article_dict = data.dict() if hasattr(data, 'dict') else dict(data)
        changes_made = 0
        
        # Fields to process
        content_fields = [
            'Intro', 'Direct_Answer', 'Teaser',
            'section_01_content', 'section_02_content', 'section_03_content',
            'section_04_content', 'section_05_content', 'section_06_content',
            'section_07_content', 'section_08_content', 'section_09_content',
            'section_01_title', 'section_02_title', 'section_03_title',
            'section_04_title', 'section_05_title', 'section_06_title',
            'section_07_title', 'section_08_title', 'section_09_title',
        ]
        
        for field in content_fields:
            content = article_dict.get(field)
            if not content or not isinstance(content, str):
                continue
            
            original = content
            
            # 1. Em/en dashes → hyphens
            content = content.replace("—", " - ")
            content = content.replace("–", "-")
            
            # 2. Remove academic citations [N]
            content = re.sub(r'\[(\d+)\]', '', content)
            
            # 3. Remove "Here are key points:" + duplicate lists
            summary_patterns = [
                r'<p>Here are key points:</p>\s*<ul>.*?</ul>',
                r'<p>Key benefits include:</p>\s*<ul>.*?</ul>',
                r'<p>Important considerations:</p>\s*<ul>.*?</ul>',
                r"<p>Here's what matters:</p>\s*<ul>.*?</ul>",
            ]
            for pattern in summary_patterns:
                content = re.sub(pattern, '', content, flags=re.DOTALL)
            
            # 4. Fix ". Also,," → ". Also,"
            content = re.sub(r'\.\s*Also,+', '. Also,', content)
            
            # 5. Remove truncated fragment lists (75%+ items without punctuation)
            content = self._remove_fragment_lists(content)
            
            # 6. Fix double prefixes: "What is <p>How is..." → "<p>How is..."
            content = re.sub(r'What is\s*<p>', '<p>', content)
            content = re.sub(r'What are the future trends in\s*<p>', '<p>', content)
            content = re.sub(r'What is Why is\s*', '', content)
            
            # 7. Fix lowercase after period
            content = re.sub(r'(\. )([a-z])', lambda m: m.group(1) + m.group(2).upper(), content)
            
            # 8. Remove orphaned periods at start
            content = re.sub(r'^<p>\.\s*', '<p>', content)
            content = re.sub(r'<p>\.\s*Also,', '<p>Also,', content)
            
            if content != original:
                article_dict[field] = content
                changes_made += 1
        
        if changes_made > 0:
            logger.info(f"   ✅ Regex cleanup applied to {changes_made} fields")
            # Update context with cleaned data
            from ..models.output_schema import ArticleOutput
            context.structured_data = ArticleOutput(**article_dict)
        else:
            logger.info("   ℹ️ Regex cleanup: no changes needed")
        
        return context
    
    async def _gemini_full_review(self, context: ExecutionContext) -> ExecutionContext:
        """
        MANDATORY Gemini review with full quality checklist.
        
        Gemini reviews ALL content fields and fixes any issues it finds,
        even if our detection logic missed them.
        """
        from pydantic import BaseModel, Field
        from typing import List
        import json
        
        # Define response schema
        class ContentFix(BaseModel):
            issue_type: str = Field(description="Type of issue fixed")
            field: str = Field(description="Which field was fixed")
        
        class ReviewResponse(BaseModel):
            fixed_content: str = Field(description="The complete fixed content")
            issues_fixed: int = Field(description="Number of issues fixed")
            fixes: List[ContentFix] = Field(default_factory=list)
        
        # Full quality checklist
        CHECKLIST = """
You are a quality editor reviewing article content. Check for ALL issues:

STRUCTURAL ISSUES:
□ Truncated list items (end mid-word: "secur", "autom", "manag")
□ Duplicate summary lists ("Here are key points:" followed by bullets repeating content)
□ Orphaned HTML tags (</p> or </li> in wrong places)
□ Malformed paragraphs starting with period (<p>. Also,)
□ Empty or near-empty list items

FORMATTING ISSUES:
□ Em dashes (—) → replace with " - "
□ En dashes (–) → replace with "-"
□ Academic citations [N] → remove entirely
□ Bold keywords that shouldn't be bold → unbold
□ Lowercase after period → capitalize

CONTENT ISSUES:
□ Incomplete sentences ending abruptly
□ "What is Why is" double prefixes → fix
□ Repeated/redundant content
□ Awkward AI phrasing ("delve into", "crucial to note")

Fix ALL issues. Be surgical - only change what's broken.
Return the complete fixed content.
"""
        
        data = context.structured_data
        if not data:
            return context
        
        article_dict = data.dict() if hasattr(data, 'dict') else dict(data)
        total_fixes = 0
        
        # Content fields to review
        content_fields = [
            'section_01_content', 'section_02_content', 'section_03_content',
            'section_04_content', 'section_05_content', 'section_06_content',
            'section_07_content', 'section_08_content', 'section_09_content',
            'Intro', 'Direct_Answer',
        ]
        
        # Initialize Gemini client
        from ..models.gemini_client import GeminiClient
        gemini_client = GeminiClient()
        
        for field in content_fields:
            content = article_dict.get(field)
            if not content or not isinstance(content, str) or len(content) < 100:
                continue
            
            prompt = f"""{CHECKLIST}

FIELD: {field}

CONTENT TO REVIEW:
{content}

Return JSON with: fixed_content, issues_fixed, fixes[]
If no issues, return original content unchanged with issues_fixed=0.
"""
            
            try:
                response = await gemini_client.generate_content(
                    prompt=prompt,
                    enable_tools=False,
                    response_schema=ReviewResponse.model_json_schema()
                )
                
                if response:
                    # Parse response
                    json_str = response.strip()
                    if json_str.startswith('```'):
                        json_str = json_str.split('\n', 1)[1] if '\n' in json_str else json_str[3:]
                    if json_str.endswith('```'):
                        json_str = json_str[:-3]
                    
                    try:
                        result = json.loads(json_str)
                        issues_fixed = result.get('issues_fixed', 0)
                        
                        if issues_fixed > 0:
                            article_dict[field] = result.get('fixed_content', content)
                            total_fixes += issues_fixed
                            logger.info(f"   ✅ {field}: {issues_fixed} issues fixed")
                    except json.JSONDecodeError:
                        # If not valid JSON, skip this field
                        logger.debug(f"   ⚠️ {field}: Could not parse Gemini response")
                        
            except Exception as e:
                logger.debug(f"   ⚠️ {field}: Gemini review failed - {e}")
                # Continue with other fields
        
        if total_fixes > 0:
            logger.info(f"   📝 Gemini fixed {total_fixes} total issues across all fields")
            context.structured_data = ArticleOutput(**article_dict)
        else:
            logger.info("   ℹ️ Gemini review: no additional issues found")
        
        return context
    
    def _remove_fragment_lists(self, content: str) -> str:
        """Remove lists where 75%+ of items are truncated fragments."""
        pattern = r'<ul>((?:<li>(?:[^<]|<(?!/?li>)[^>]*>)*</li>\s*){2,})</ul>'
        
        def check_fragments(match):
            list_content = match.group(1)
            items_raw = re.findall(r'<li>((?:[^<]|<(?!/?li>)[^>]*>)*)</li>', list_content)
            if not items_raw:
                return match.group(0)
            
            items = [re.sub(r'<[^>]+>', '', item).strip() for item in items_raw]
            fragment_count = sum(1 for item in items if not item.endswith(('.', '!', '?', ':')))
            
            if fragment_count >= len(items) * 0.75:
                logger.debug(f"   🗑️ Removing fragment list ({fragment_count}/{len(items)} truncated)")
                return ''
            return match.group(0)
        
        return re.sub(pattern, check_fragments, content, flags=re.DOTALL)
    
    def _detect_quality_issues(self, context: ExecutionContext) -> List[QualityIssue]:
        """
        Detect quality issues in structured_data.
        
        Returns:
            List of QualityIssue objects
        """
        issues = []
        data = context.structured_data
        job_config = context.job_config or {}
        
        primary_keyword = job_config.get("primary_keyword", "")
        
        # Issue 1: Keyword over/under-optimization
        if primary_keyword:
            keyword_issue = self._check_keyword_density(data, primary_keyword)
            if keyword_issue:
                issues.append(keyword_issue)
        
        # Issue 2: First paragraph too short/long
        first_para_issue = self._check_first_paragraph_length(data)
        if first_para_issue:
            issues.append(first_para_issue)
        
        # Issue 3: AI language markers
        ai_marker_issues = self._check_ai_markers(data)
        issues.extend(ai_marker_issues)
        
        # Issue 4: Academic citations (needs conversion to natural language)
        academic_citation_issue = self._check_academic_citations(data)
        if academic_citation_issue:
            issues.append(academic_citation_issue)
        
        # Issue 5: Duplicate bullet lists (paragraph content repeated as list)
        duplicate_list_issues = self._check_duplicate_bullet_lists(data)
        issues.extend(duplicate_list_issues)
        
        # Issue 6: Truncated list items (incomplete sentences)
        truncated_item_issues = self._check_truncated_list_items(data)
        issues.extend(truncated_item_issues)
        
        # Issue 7: Malformed HTML (nested lists, improper tags)
        malformed_html_issues = self._check_malformed_html(data)
        issues.extend(malformed_html_issues)
        
        # Issue 8: Orphaned incomplete paragraphs
        orphaned_para_issues = self._check_orphaned_paragraphs(data)
        issues.extend(orphaned_para_issues)
        
        # Issue 9: Missing sources (mentioned but not in Sources)
        missing_sources_issue = self._check_missing_sources(data)
        if missing_sources_issue:
            issues.append(missing_sources_issue)
        
        return issues
    
    def _check_keyword_density(
        self,
        data: ArticleOutput,
        primary_keyword: str
    ) -> Optional[QualityIssue]:
        """
        Check if primary keyword is over/under-optimized.
        """
        # Count keyword mentions in content
        content_fields = ["Headline", "Intro"]
        
        # Add all section content fields
        for i in range(1, 10):
            field_name = f"section_{i:02d}_content"
            content_fields.append(field_name)
        
        # Concatenate all content
        all_content = " ".join([
            str(getattr(data, field, ""))
            for field in content_fields
            if getattr(data, field, None)
        ])
        
        # Count keyword (case-insensitive)
        keyword_count = all_content.lower().count(primary_keyword.lower())
        
        if keyword_count < self.KEYWORD_TARGET_MIN:
            return QualityIssue(
                issue_type="keyword_underuse",
                severity="warning",
                description=f"Keyword '{primary_keyword}' appears only {keyword_count} times (target: {self.KEYWORD_TARGET_MIN}-{self.KEYWORD_TARGET_MAX})",
                current_value=keyword_count,
                target_value=f"{self.KEYWORD_TARGET_MIN}-{self.KEYWORD_TARGET_MAX}",
                field="all_content"
            )
        
        elif keyword_count > self.KEYWORD_TARGET_MAX:
            return QualityIssue(
                issue_type="keyword_overuse",
                severity="critical",
                description=f"Keyword '{primary_keyword}' appears {keyword_count} times (target: {self.KEYWORD_TARGET_MIN}-{self.KEYWORD_TARGET_MAX})",
                current_value=keyword_count,
                target_value=f"{self.KEYWORD_TARGET_MIN}-{self.KEYWORD_TARGET_MAX}",
                field="all_sections"
            )
        
        return None
    
    def _check_first_paragraph_length(
        self,
        data: ArticleOutput
    ) -> Optional[QualityIssue]:
        """
        Check if first paragraph is too short or too long.
        """
        # Get first section content
        first_section = getattr(data, "section_01_content", "")
        
        if not first_section:
            return None
        
        # Extract first <p> tag
        first_p_match = re.search(r'<p>(.*?)</p>', first_section, re.DOTALL)
        
        if not first_p_match:
            return None
        
        first_paragraph = first_p_match.group(1)
        
        # Strip HTML tags from paragraph for word count
        text_only = re.sub(r'<[^>]+>', '', first_paragraph)
        word_count = len(text_only.split())
        
        if word_count < self.FIRST_PARAGRAPH_MIN_WORDS:
            return QualityIssue(
                issue_type="first_paragraph_short",
                severity="critical",
                description=f"First paragraph is only {word_count} words (target: {self.FIRST_PARAGRAPH_MIN_WORDS}-{self.FIRST_PARAGRAPH_MAX_WORDS})",
                current_value=word_count,
                target_value=f"{self.FIRST_PARAGRAPH_MIN_WORDS}-{self.FIRST_PARAGRAPH_MAX_WORDS}",
                field="section_01_content"
            )
        
        elif word_count > self.FIRST_PARAGRAPH_MAX_WORDS:
            return QualityIssue(
                issue_type="first_paragraph_long",
                severity="warning",
                description=f"First paragraph is {word_count} words (target: {self.FIRST_PARAGRAPH_MIN_WORDS}-{self.FIRST_PARAGRAPH_MAX_WORDS})",
                current_value=word_count,
                target_value=f"{self.FIRST_PARAGRAPH_MIN_WORDS}-{self.FIRST_PARAGRAPH_MAX_WORDS}",
                field="section_01_content"
            )
        
        return None
    
    def _check_ai_markers(self, data: ArticleOutput) -> List[QualityIssue]:
        """
        Check for AI language markers (em dashes, robotic phrases).
        """
        issues = []
        
        # Concatenate all content
        content_fields = ["Intro"] + [f"section_{i:02d}_content" for i in range(1, 10)]
        all_content = " ".join([
            str(getattr(data, field, ""))
            for field in content_fields
            if getattr(data, field, None)
        ])
        
        # Check for em dashes
        em_dash_count = all_content.count(self.AI_MARKERS["em_dash"])
        if em_dash_count > 0:
            issues.append(QualityIssue(
                issue_type="em_dashes",
                severity="warning",
                description=f"Found {em_dash_count} em dashes (—) - AI marker",
                current_value=em_dash_count,
                target_value=0,
                field="all_content"
            ))
        
        # Check for robotic phrases
        found_phrases = [
            phrase for phrase in self.AI_MARKERS["robotic_phrases"]
            if phrase in all_content
        ]
        
        if found_phrases:
            issues.append(QualityIssue(
                issue_type="robotic_phrases",
                severity="warning",
                description=f"Found {len(found_phrases)} robotic phrases: {', '.join(found_phrases[:3])}{'...' if len(found_phrases) > 3 else ''}",
                current_value=found_phrases,
                target_value=[],
                field="all_content"
            ))
        
        return issues
    
    def _check_academic_citations(self, data: ArticleOutput) -> Optional[QualityIssue]:
        """
        Check for academic citations [1], [2], [1][2] that need conversion to natural language.
        """
        import re
        
        # Get all content fields
        content_fields = ["Headline", "Direct_Answer", "Intro"]
        for i in range(1, 10):
            content_fields.extend([
                f"section_{i:02d}_title",
                f"section_{i:02d}_content"
            ])
        
        # Check for academic citation patterns [N], [N][M], etc.
        academic_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\[\d+\]\[\d+\]',  # [1][2], [2][3], etc.
            r'\[\d+\]\[\d+\]\[\d+\]',  # [1][2][3], etc.
        ]
        
        found_citations = []
        for field in content_fields:
            content = str(getattr(data, field, ""))
            if content:
                for pattern in academic_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        found_citations.extend([(field, match) for match in matches])
        
        if found_citations:
            return QualityIssue(
                issue_type="academic_citations",
                severity="critical",
                description=f"Found {len(found_citations)} academic citations [N] that must be converted to natural language inline links",
                current_value=len(found_citations),
                target_value=0,
                field="all_content"
            )
        
        return None
    
    def _check_duplicate_bullet_lists(self, data: ArticleOutput) -> List[QualityIssue]:
        """
        Check for paragraphs immediately followed by bullet lists that duplicate content.
        
        Pattern: <p>AI improves X, Y, Z.</p><ul><li>AI improves X</li>...
        """
        issues = []
        
        content_fields = ["Intro"] + [f"section_{i:02d}_content" for i in range(1, 10)]
        
        for field in content_fields:
            content = str(getattr(data, field, ""))
            if not content:
                continue
            
            # Find pattern: <p>text</p> followed by <ul><li> with overlapping content
            pattern = r'<p>([^<]{20,})</p>\s*<ul>\s*<li>([^<]+)</li>'
            matches = re.findall(pattern, content, re.DOTALL)
            
            for p_text, li_text in matches:
                # Check if list item is a substring of the paragraph
                p_words = set(p_text.lower().split()[:10])
                li_words = set(li_text.lower().split()[:10])
                
                # If >60% word overlap, it's likely duplicate
                if len(p_words & li_words) > 0.6 * len(li_words):
                    issues.append(QualityIssue(
                        issue_type="duplicate_bullet_list",
                        severity="critical",
                        description=f"Paragraph content duplicated as bullet list in {field}",
                        current_value=li_text[:50] + "...",
                        target_value="Remove duplicate list",
                        field=field
                    ))
        
        return issues
    
    def _check_truncated_list_items(self, data: ArticleOutput) -> List[QualityIssue]:
        """
        Check for list items that are incomplete (cut off mid-sentence).
        
        Pattern: <li>Text without proper ending punctuation</li>
        """
        issues = []
        
        content_fields = ["Intro"] + [f"section_{i:02d}_content" for i in range(1, 10)]
        
        for field in content_fields:
            content = str(getattr(data, field, ""))
            if not content:
                continue
            
            # Find all list items
            li_pattern = r'<li>([^<]+)</li>'
            list_items = re.findall(li_pattern, content)
            
            for item in list_items:
                item = item.strip()
                
                # Skip items that look complete
                if not item or len(item) < 20:
                    continue
                
                # Check if item ends without punctuation (., !, ?, :)
                if not item[-1] in '.!?:':
                    # Check if it ends with preposition/article (likely truncated)
                    truncation_endings = ['to', 'the', 'a', 'an', 'of', 'with', 'for', 'in', 'on', 'at', 'from', 'into', 'and', 'or']
                    last_word = item.split()[-1].lower()
                    
                    if last_word in truncation_endings:
                        issues.append(QualityIssue(
                            issue_type="truncated_list_item",
                            severity="critical",
                            description=f"Truncated list item in {field}: '{item[:40]}...'",
                            current_value=item,
                            target_value="Complete the sentence or remove",
                            field=field
                        ))
        
        return issues
    
    def _check_malformed_html(self, data: ArticleOutput) -> List[QualityIssue]:
        """
        Check for malformed HTML structure.
        
        Patterns:
        - </p> inside <li>
        - <ul> directly inside <ul>
        - Unclosed tags
        """
        issues = []
        
        content_fields = ["Intro"] + [f"section_{i:02d}_content" for i in range(1, 10)]
        
        for field in content_fields:
            content = str(getattr(data, field, ""))
            if not content:
                continue
            
            # Check for </p> inside list items
            if re.search(r'<li>[^<]*</p>', content):
                issues.append(QualityIssue(
                    issue_type="malformed_html",
                    severity="critical",
                    description=f"Found </p> inside <li> in {field}",
                    current_value="</p> inside <li>",
                    target_value="Fix HTML nesting",
                    field=field
                ))
            
            # Check for nested <ul><ul>
            if re.search(r'<ul>\s*<ul>', content):
                issues.append(QualityIssue(
                    issue_type="malformed_html",
                    severity="critical",
                    description=f"Found nested <ul><ul> in {field}",
                    current_value="<ul><ul>",
                    target_value="Flatten list structure",
                    field=field
                ))
            
            # Check for <p> immediately containing <ul>
            if re.search(r'<p>\s*<ul>', content):
                issues.append(QualityIssue(
                    issue_type="malformed_html",
                    severity="warning",
                    description=f"Found <ul> inside <p> in {field}",
                    current_value="<p><ul>",
                    target_value="Separate paragraph from list",
                    field=field
                ))
        
        return issues
    
    def _check_orphaned_paragraphs(self, data: ArticleOutput) -> List[QualityIssue]:
        """
        Check for orphaned incomplete paragraphs.
        
        Patterns:
        - <p>This </p>
        - <p>. Also,</p>
        - Very short paragraphs under 3 words
        """
        issues = []
        
        content_fields = ["Intro"] + [f"section_{i:02d}_content" for i in range(1, 10)]
        
        for field in content_fields:
            content = str(getattr(data, field, ""))
            if not content:
                continue
            
            # Find all paragraphs
            para_pattern = r'<p>([^<]*)</p>'
            paragraphs = re.findall(para_pattern, content)
            
            for para in paragraphs:
                para = para.strip()
                
                # Check for "This " only
                if para in ["This", "This ", "This.", "That", "That ", "These"]:
                    issues.append(QualityIssue(
                        issue_type="orphaned_paragraph",
                        severity="critical",
                        description=f"Orphaned incomplete paragraph in {field}: '{para}'",
                        current_value=para,
                        target_value="Remove or complete",
                        field=field
                    ))
                
                # Check for period at start
                if para.startswith('. ') or para.startswith(', '):
                    issues.append(QualityIssue(
                        issue_type="orphaned_paragraph",
                        severity="critical",
                        description=f"Paragraph starts with period/comma in {field}: '{para[:30]}'",
                        current_value=para[:30],
                        target_value="Remove orphaned punctuation",
                        field=field
                    ))
                
                # Check for very short paragraphs (under 3 words)
                word_count = len(para.split())
                if 0 < word_count < 3 and not para.endswith('?'):
                    issues.append(QualityIssue(
                        issue_type="orphaned_paragraph",
                        severity="warning",
                        description=f"Very short paragraph in {field}: '{para}'",
                        current_value=para,
                        target_value="Expand or remove",
                        field=field
                    ))
        
        return issues
    
    def _check_missing_sources(self, data: ArticleOutput) -> Optional[QualityIssue]:
        """
        Check for sources mentioned in text but missing from Sources field.
        
        Looks for: IBM, Gartner, Forrester, McKinsey, Deloitte, PwC, Google, etc.
        """
        # Common authoritative sources
        known_sources = [
            "IBM", "Gartner", "Forrester", "McKinsey", "Deloitte", "PwC", 
            "Google", "Microsoft", "Amazon", "Accenture", "KPMG", "EY",
            "Palo Alto", "CrowdStrike", "Cisco", "Splunk", "GitHub"
        ]
        
        # Get all content
        content_fields = ["Intro"] + [f"section_{i:02d}_content" for i in range(1, 10)]
        all_content = " ".join([
            str(getattr(data, field, ""))
            for field in content_fields
            if getattr(data, field, None)
        ])
        
        # Get Sources field
        sources = str(getattr(data, "Sources", "")).lower()
        
        # Find mentioned sources not in Sources field
        missing = []
        for source in known_sources:
            # Check if mentioned in content
            if source.lower() in all_content.lower():
                # Check if in Sources
                if source.lower() not in sources:
                    missing.append(source)
        
        if missing:
            return QualityIssue(
                issue_type="missing_sources",
                severity="critical",
                description=f"Sources mentioned but not in Sources field: {', '.join(missing)}",
                current_value=missing,
                target_value="Add these sources with proper URLs",
                field="Sources"
            )
        
        return None
    
    def _issues_to_rewrites(
        self,
        issues: List[QualityIssue],
        context: ExecutionContext
    ) -> List[RewriteInstruction]:
        """
        Convert quality issues to rewrite instructions.
        """
        rewrites = []
        job_config = context.job_config or {}
        primary_keyword = job_config.get("primary_keyword", "")
        
        for issue in issues:
            # Only fix critical issues and warnings (skip info)
            if issue.severity not in ["critical", "warning"]:
                continue
            
            if issue.issue_type == "keyword_overuse":
                # Generate semantic variations
                variations = self._generate_keyword_variations(primary_keyword)
                
                rewrites.append(RewriteInstruction(
                    target="all_sections",
                    instruction=f"Reduce '{primary_keyword}' from {issue.current_value} to {self.KEYWORD_TARGET_MIN}-{self.KEYWORD_TARGET_MAX} mentions. Replace excess with variations.",
                    mode=RewriteMode.QUALITY_FIX,
                    preserve_structure=True,
                    min_similarity=0.75,
                    max_similarity=0.95,
                    context={
                        "keyword": primary_keyword,
                        "current_count": issue.current_value,
                        "target_min": self.KEYWORD_TARGET_MIN,
                        "target_max": self.KEYWORD_TARGET_MAX,
                        "variations": variations
                    }
                ))
            
            elif issue.issue_type == "keyword_underuse":
                # Don't auto-fix underuse (risky to add keywords)
                # Just log it
                logger.info(f"Skipping keyword underuse fix (current={issue.current_value}, target={self.KEYWORD_TARGET_MIN}+)")
            
            elif issue.issue_type == "first_paragraph_short":
                rewrites.append(RewriteInstruction(
                    target="section_01_content",
                    instruction=f"First paragraph is only {issue.current_value} words. Expand to {self.FIRST_PARAGRAPH_MIN_WORDS}-{self.FIRST_PARAGRAPH_MAX_WORDS} words with context, examples, or data.",
                    mode=RewriteMode.QUALITY_FIX,
                    preserve_structure=True,
                    min_similarity=0.50,
                    max_similarity=0.85,
                    context={
                        "current_words": issue.current_value,
                        "target_min": self.FIRST_PARAGRAPH_MIN_WORDS,
                        "target_max": self.FIRST_PARAGRAPH_MAX_WORDS,
                        "paragraph_index": 1
                    }
                ))
            
            elif issue.issue_type == "first_paragraph_long":
                # Don't auto-fix long paragraphs (may be intentional)
                logger.info(f"Skipping long paragraph fix (current={issue.current_value} words)")
            
            elif issue.issue_type in ["em_dashes", "robotic_phrases"]:
                markers_found = []
                if issue.issue_type == "em_dashes":
                    markers_found.append(f"Em dashes (—) x{issue.current_value}")
                if issue.issue_type == "robotic_phrases":
                    markers_found.extend(issue.current_value)
                
                rewrites.append(RewriteInstruction(
                    target="all_content",
                    instruction="Remove AI language markers: em dashes and robotic phrases.",
                    mode=RewriteMode.QUALITY_FIX,
                    preserve_structure=True,
                    min_similarity=0.80,
                    max_similarity=0.95,
                    context={
                        "markers_found": markers_found
                    }
                ))
            
            elif issue.issue_type == "academic_citations":
                rewrites.append(RewriteInstruction(
                    target="all_content",
                    instruction="Convert academic citations [1], [2], [1][2] to natural language inline links. Replace [N] with contextual phrases like 'according to [source]', 'per [study]', '[company]'s research shows'. Format as: <a href=\"#source-N\" class=\"citation\">according to GitHub</a>",
                    mode=RewriteMode.QUALITY_FIX,
                    preserve_structure=True,
                    min_similarity=0.70,
                    max_similarity=0.90,
                    context={
                        "academic_citations_found": issue.current_value
                    }
                ))
            
            elif issue.issue_type == "duplicate_bullet_list":
                rewrites.append(RewriteInstruction(
                    target=issue.field,
                    instruction="""REMOVE duplicate bullet lists that repeat paragraph content.
                    
PATTERN TO FIX:
<p>AI improves detection, response, and automation.</p>
<ul>
<li>AI improves detection</li>
<li>Response</li>
<li>Automation</li>
</ul>

CORRECT OUTPUT:
<p>AI improves detection, response, and automation.</p>

RULES:
- If a <ul> immediately follows a <p> and the list items repeat words from the paragraph, DELETE the entire <ul>
- Keep ONLY the paragraph
- Do NOT add any new content
- Do NOT modify the paragraph itself""",
                    mode=RewriteMode.QUALITY_FIX,
                    preserve_structure=True,
                    min_similarity=0.80,
                    max_similarity=0.95,
                    context={
                        "duplicate_content": issue.current_value
                    }
                ))
            
            elif issue.issue_type == "truncated_list_item":
                rewrites.append(RewriteInstruction(
                    target=issue.field,
                    instruction=f"""Fix truncated list item that ends mid-sentence.
                    
TRUNCATED ITEM: {issue.current_value}

RULES:
- Either COMPLETE the sentence properly with a period
- Or REMOVE the list item entirely if it cannot be completed meaningfully
- Ensure the list item ends with proper punctuation (. or :)
- Do NOT leave sentences ending with: to, the, a, an, of, with, for, in, on, at, from, into, and, or""",
                    mode=RewriteMode.QUALITY_FIX,
                    preserve_structure=True,
                    min_similarity=0.70,
                    max_similarity=0.90,
                    context={
                        "truncated_item": issue.current_value
                    }
                ))
            
            elif issue.issue_type == "malformed_html":
                rewrites.append(RewriteInstruction(
                    target=issue.field,
                    instruction="""Fix malformed HTML structure.

RULES:
- Never place </p> inside <li> tags
- Never nest <ul> directly inside <ul> without <li>
- Never place <ul> directly inside <p>
- Ensure all lists are properly structured: <ul><li>item</li><li>item</li></ul>
- Separate paragraphs from lists with proper closing tags

CORRECT STRUCTURE:
<p>Paragraph text here.</p>
<ul>
<li>List item one.</li>
<li>List item two.</li>
</ul>""",
                    mode=RewriteMode.QUALITY_FIX,
                    preserve_structure=True,
                    min_similarity=0.80,
                    max_similarity=0.95,
                    context={
                        "html_issue": issue.current_value
                    }
                ))
            
            elif issue.issue_type == "orphaned_paragraph":
                rewrites.append(RewriteInstruction(
                    target=issue.field,
                    instruction=f"""Fix orphaned/incomplete paragraph: '{issue.current_value}'

RULES:
- If paragraph is just "This", "That", "These" - REMOVE it entirely
- If paragraph starts with ". " or ", " - REMOVE the leading punctuation
- If paragraph is under 3 words - EITHER expand it to a full sentence OR remove it
- Ensure all paragraphs are complete, meaningful sentences""",
                    mode=RewriteMode.QUALITY_FIX,
                    preserve_structure=True,
                    min_similarity=0.80,
                    max_similarity=0.95,
                    context={
                        "orphaned_content": issue.current_value
                    }
                ))
            
            elif issue.issue_type == "missing_sources":
                # Note: This is logged but not auto-fixed (too complex)
                # Layer 3 (html_renderer) will handle missing source validation
                logger.info(f"⚠️  Missing sources detected: {', '.join(issue.current_value)} - will be caught in Layer 3")
        
        return rewrites
    
    def _generate_keyword_variations(self, primary_keyword: str) -> List[str]:
        """
        Generate semantic variations for a keyword.
        
        This is a simple heuristic - could be improved with NLP.
        """
        # Extract the main concept (last 1-2 words usually)
        words = primary_keyword.split()
        
        variations = [
            "these tools",
            "these solutions",
            "these platforms",
            "the technology",
            "this approach"
        ]
        
        # Try to generate more specific variations
        if "AI" in primary_keyword or "artificial intelligence" in primary_keyword.lower():
            variations.extend([
                "AI assistants",
                "AI systems",
                "intelligent tools",
                "automated solutions"
            ])
        
        if "code" in primary_keyword.lower():
            variations.extend([
                "code generators",
                "development tools",
                "coding assistants"
            ])
        
        if "tool" in primary_keyword.lower():
            variations.extend([
                "software",
                "applications",
                "utilities"
            ])
        
        # Return unique variations (max 5)
        return list(dict.fromkeys(variations))[:5]

