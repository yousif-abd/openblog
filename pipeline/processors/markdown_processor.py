"""
Markdown to HTML Processor

Production-grade markdown conversion for blog content.
Handles the specific patterns that Gemini outputs.

Design Principles:
- Single Responsibility: Only handles markdown→HTML conversion
- Open/Closed: Easy to extend with new patterns without modifying existing code
- DRY: Centralized logic, no duplication across renderers

Input: Raw markdown content from Gemini (may be mixed with HTML)
Output: Clean HTML with proper list structures

Key transformations:
1. Dash lists (- item) → <ul><li>item</li></ul>
2. Numbered lists (1. item) → <ol><li>item</li></ol>
3. Bold (**text**) → <strong>text</strong>
4. Italic (*text*) → <em>text</em>
5. Paragraphs with proper wrapping
"""

import re
import logging
from typing import List, Tuple
import markdown
from markdown.extensions import fenced_code, tables

logger = logging.getLogger(__name__)


class MarkdownProcessor:
    """
    Convert markdown content to HTML.
    
    Uses the Python markdown library for robust conversion,
    with custom pre/post processing for Gemini-specific patterns.
    """
    
    # Patterns that indicate content is already HTML (skip conversion)
    HTML_INDICATORS = ['<p>', '<ul>', '<ol>', '<li>', '<div>', '<article>']
    
    # Gemini sometimes outputs mixed format - these need special handling
    MIXED_FORMAT_PATTERNS = [
        # Dash list inside <p> tag: <p>text - item1 - item2</p>
        (r'<p>([^<]*?)((?:\s*-\s+[^<\n]+\n?)+)</p>', '_convert_inline_dash_list'),
        # Numbered list inside <p> tag: <p>text 1. item1 2. item2</p>
        (r'<p>([^<]*?)((?:\s*\d+\.\s+[^<\n]+\n?)+)</p>', '_convert_inline_numbered_list'),
    ]
    
    def __init__(self):
        """Initialize markdown converter with extensions."""
        self.md = markdown.Markdown(
            extensions=[
                'fenced_code',
                'tables',
                'nl2br',  # Newlines to <br>
            ]
        )
    
    def convert(self, content: str) -> str:
        """
        Convert markdown content to HTML.
        
        Args:
            content: Raw markdown or mixed markdown/HTML content
            
        Returns:
            Clean HTML with proper structure
        """
        if not content:
            return ""
        
        # Step 1: Pre-process - fix mixed format issues from Gemini
        content = self._preprocess_mixed_format(content)
        
        # Step 2: Check if content is mostly HTML already
        if self._is_mostly_html(content):
            # Still need to handle inline markdown within HTML
            content = self._convert_inline_markdown(content)
            content = self._convert_inline_lists(content)
        else:
            # Pure markdown - use library
            content = self.md.convert(content)
            self.md.reset()
        
        # Step 3: Post-process - clean up any remaining issues
        content = self._postprocess(content)
        
        return content
    
    def _is_mostly_html(self, content: str) -> bool:
        """Check if content is already mostly HTML."""
        html_tag_count = sum(content.count(tag) for tag in self.HTML_INDICATORS)
        return html_tag_count >= 2  # If 2+ HTML tags, treat as HTML
    
    def _preprocess_mixed_format(self, content: str) -> str:
        """
        Fix Gemini's mixed format output.
        
        Gemini sometimes outputs lists without proper blank line separation,
        which the markdown library requires. This preprocessor fixes that.
        
        Also handles:
        <p>Introduction text:
        - Item one
        - Item two
        </p>
        """
        # Fix 1: Add blank line before dash lists that follow text
        # Pattern: text (not starting with -) followed by newline + dash list
        content = re.sub(
            r'([^\n-])(\n)(- )',
            r'\1\n\n\3',  # Add extra newline
            content
        )
        
        # Fix 2: Add blank line before dash lists that follow colons
        # Pattern: colon followed by dash list (with or without newline)
        content = re.sub(
            r':(\s*\n?\s*)(- )',
            r':\n\n\2',
            content
        )
        
        # Fix 3: Handle inline dash lists (text: - item - item - item)
        # Convert to proper list with newlines
        def expand_inline_list(match):
            intro = match.group(1)
            items_str = match.group(2)
            items = re.findall(r'-\s+([^-]+?)(?=\s+-\s+|$)', items_str)
            if items and len(items) >= 2:
                items_formatted = '\n'.join(f'- {item.strip()}' for item in items if item.strip())
                return f'{intro}\n\n{items_formatted}\n'
            return match.group(0)
        
        content = re.sub(
            r'([^-\n]+:)\s*((?:-\s+[^-\n]+\s*){2,})',
            expand_inline_list,
            content
        )
        
        # Fix 4: Handle HTML paragraphs containing dash lists
        def fix_paragraph_with_list(match):
            """Extract list from paragraph and format properly."""
            full_content = match.group(1)
            
            # Find where the list starts (first dash after colon or period)
            list_start = re.search(r'[:.]\s*\n?\s*-\s+', full_content)
            if list_start:
                text_part = full_content[:list_start.end() - len(list_start.group()) + 1].strip()
                list_part = full_content[list_start.end() - 2:].strip()
                
                # Convert dash list to proper HTML
                items = re.findall(r'-\s+([^\n-]+)', list_part)
                if items:
                    list_html = '<ul>' + ''.join(f'<li>{item.strip()}</li>' for item in items if item.strip()) + '</ul>'
                    return f'<p>{text_part}</p>{list_html}'
            
            return match.group(0)
        
        content = re.sub(
            r'<p>([^<]*?(?:[:.])\s*\n?\s*-\s+[^<]+)</p>',
            fix_paragraph_with_list,
            content,
            flags=re.DOTALL
        )
        
        return content
    
    def _convert_inline_markdown(self, content: str) -> str:
        """Convert inline markdown (**bold**, *italic*) within HTML content."""
        # Bold: **text** → <strong>text</strong>
        content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)
        
        # Italic: *text* → <em>text</em> (but not if already processed as bold)
        content = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', content)
        
        return content
    
    def _convert_inline_lists(self, content: str) -> str:
        """
        Convert markdown lists that appear inline within HTML content.
        
        Handles:
        - Dash lists (- item) not already in <li> tags
        - Numbered lists (1. item) not already in <li> tags
        """
        # Find sequences of dash list items not in <ul>
        # Pattern: Multiple lines starting with "- " that aren't in <li>
        
        def convert_dash_sequence(match):
            """Convert a sequence of dash items to <ul><li>."""
            raw_list = match.group(0)
            items = re.findall(r'-\s+([^\n]+)', raw_list)
            if items:
                html_items = ''.join(f'<li>{item.strip()}</li>' for item in items if item.strip())
                return f'<ul>{html_items}</ul>'
            return raw_list
        
        def convert_numbered_sequence(match):
            """Convert a sequence of numbered items to <ol><li>."""
            raw_list = match.group(0)
            items = re.findall(r'\d+\.\s+([^\n]+)', raw_list)
            if items:
                html_items = ''.join(f'<li>{item.strip()}</li>' for item in items if item.strip())
                return f'<ol>{html_items}</ol>'
            return raw_list
        
        # Convert dash lists (- item\n- item\n...)
        # Only match if not already inside <ul> or <li>
        content = re.sub(
            r'(?<!</li>)(?<!</ul>)\n?((?:-\s+[^\n]+\n?){2,})',
            convert_dash_sequence,
            content
        )
        
        # Convert numbered lists (1. item\n2. item\n...)
        content = re.sub(
            r'(?<!</li>)(?<!</ol>)\n?((?:\d+\.\s+[^\n]+\n?){2,})',
            convert_numbered_sequence,
            content
        )
        
        # Handle single-line lists (less common but possible)
        # E.g., "Key points: - Item 1 - Item 2 - Item 3"
        # Only if there are 2+ items
        def convert_inline_dashes(match):
            text = match.group(0)
            items = re.split(r'\s+-\s+', text)
            if len(items) >= 3:  # Intro + at least 2 items
                intro = items[0]
                list_items = ''.join(f'<li>{item.strip()}</li>' for item in items[1:] if item.strip())
                return f'{intro}<ul>{list_items}</ul>'
            return text
        
        # Match text ending with : or . followed by dash items
        content = re.sub(
            r'[^<>\n]+[:.](?:\s+-\s+[^<>\n-]+){2,}',
            convert_inline_dashes,
            content
        )
        
        return content
    
    def _postprocess(self, content: str) -> str:
        """
        Clean up the converted HTML.
        
        Fixes:
        - Empty paragraphs
        - Double-wrapped lists
        - Orphaned list items
        - Dash bullets appearing in prose
        - Improperly nested lists (li containing ul/ol)
        """
        # Remove empty paragraphs
        content = re.sub(r'<p>\s*</p>', '', content)
        
        # Fix double-wrapped lists: <ul><ul>...</ul></ul>
        content = re.sub(r'<ul>\s*<ul>', '<ul>', content)
        content = re.sub(r'</ul>\s*</ul>', '</ul>', content)
        content = re.sub(r'<ol>\s*<ol>', '<ol>', content)
        content = re.sub(r'</ol>\s*</ol>', '</ol>', content)
        
        # FIX: Flatten improperly nested lists
        # Pattern: <li>text<ul><li>more text</li></ul></li>
        # Should become: <li>text</li><li>more text</li>
        content = self._fix_nested_list_issues(content)
        
        # CRITICAL FIX: Handle dash bullets appearing in prose
        # Pattern: "<p>text - Item: description - Item2: description</p>"
        # Should become: "<p>text</p><ul><li><strong>Item:</strong> description</li>..."
        def fix_inline_dash_bullets(match):
            """Convert inline dash bullets to proper list or clean them up."""
            para_content = match.group(1)
            
            # Check if this looks like inline bullet list (has "- Label:" pattern)
            dash_items = re.findall(r'-\s+([A-Z][^-]*?)(?=\s+-\s+[A-Z]|$)', para_content)
            
            if len(dash_items) >= 2:
                # Multiple dash items - convert to proper list
                # Find the intro text (before first dash)
                intro_match = re.match(r'^([^-]*?)(?=\s*-\s+[A-Z])', para_content)
                intro = intro_match.group(1).strip() if intro_match else ''
                
                # Build list items
                list_items = []
                for item in dash_items:
                    item = item.strip()
                    if ':' in item:
                        # Item has label: "Label: description"
                        label, desc = item.split(':', 1)
                        list_items.append(f'<li><strong>{label.strip()}:</strong>{desc}</li>')
                    else:
                        list_items.append(f'<li>{item}</li>')
                
                result = ''
                if intro:
                    result = f'<p>{intro}</p>'
                result += f'<ul>{"".join(list_items)}</ul>'
                return result
            
            # Single dash or not a list pattern - just clean up the dashes
            # "- Label:" at start of prose → "Label:"
            content_cleaned = re.sub(r'^\s*-\s+([A-Z])', r'\1', para_content)
            content_cleaned = re.sub(r'\.\s+-\s+([A-Z])', r'. \1', content_cleaned)  # ". - Item" → ". Item"
            return f'<p>{content_cleaned}</p>'
        
        # Apply dash bullet fix to paragraphs containing "- Label:" patterns
        content = re.sub(
            r'<p>([^<]*-\s+[A-Z][^<]*)</p>',
            fix_inline_dash_bullets,
            content
        )
        
        # Fix single dash at start of paragraph (not a list, just orphaned dash)
        content = re.sub(r'<p>\s*-\s+([A-Z])', r'<p>\1', content)
        
        # Ensure proper paragraph structure
        # If content starts with text (not a tag), wrap in <p>
        if content and not content.strip().startswith('<'):
            # Find first block tag
            first_tag = re.search(r'<(p|ul|ol|div|h[1-6]|article|section)', content)
            if first_tag:
                intro = content[:first_tag.start()].strip()
                rest = content[first_tag.start():]
                if intro:
                    content = f'<p>{intro}</p>{rest}'
        
        return content
    
    def _fix_nested_list_issues(self, html: str) -> str:
        """
        Fix malformed nested lists created by mixed Gemini output.
        
        Problem patterns:
        - <li>text<ul><li>more text</li></ul></li> → <li>text</li><li>more text</li>
        - <ul><li><ul><li>... → <ul><li>...
        - Orphaned closing tags
        """
        # Pattern 1: List directly inside list item - flatten to siblings
        # <li>text<ul><li>item</li></ul></li> → <li>text</li><li>item</li>
        html = re.sub(
            r'(<li>[^<]*)<(ul|ol)>\s*<li>',
            r'\1</li><li>',
            html
        )
        
        # Pattern 2: Clean up orphaned closing tags from Pattern 1
        html = re.sub(r'</li>\s*</(ul|ol)></li>', '</li>', html)
        
        # Pattern 3: List immediately inside another list (no li)
        # <ul><ul>... → <ul>...
        html = re.sub(r'<(ul|ol)>\s*<(ul|ol)>', r'<\2>', html)
        
        # Pattern 4: Multiple nested closing tags
        html = re.sub(r'</ul>\s*</li>\s*</ul>', '</ul>', html)
        html = re.sub(r'</ol>\s*</li>\s*</ol>', '</ol>', html)
        
        # Pattern 5: <p> directly followed by </li> (broken structure)
        html = re.sub(r'<p>([^<]+)</p>\s*</li>', r'\1</li>', html)
        
        # Pattern 6: List tags inside <p> tags (malformed nesting)
        html = re.sub(r'<p>\s*(<ul|<ol)', r'\1', html)
        html = re.sub(r'(</ul>|</ol>)\s*</p>', r'\1', html)
        
        return html


# Module-level function for easy import
def convert_markdown_to_html(content: str) -> str:
    """
    Convert markdown content to HTML.
    
    This is the main entry point for markdown conversion.
    Uses MarkdownProcessor internally.
    
    Args:
        content: Markdown or mixed markdown/HTML content
        
    Returns:
        Clean HTML
    """
    processor = MarkdownProcessor()
    return processor.convert(content)

