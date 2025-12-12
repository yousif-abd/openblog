#!/usr/bin/env python3
"""
HTML Quality Checker - Standalone utility for validating generated blog articles.

Usage:
    python check_html_quality.py output/batch_test_1/index.html
    python check_html_quality.py output/batch_test_1/index.html output/batch_test_2/index.html
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def check_html_quality(html_content: str, filename: str = "article") -> Tuple[List[str], List[str]]:
    """
    Run comprehensive quality checks on HTML content.
    
    Args:
        html_content: HTML string to check
        filename: Name of file for reporting
        
    Returns:
        Tuple of (critical_issues, warnings)
    """
    critical = []
    warnings = []
    
    # ===== CRITICAL ISSUES =====
    
    # 1. Em dashes and en dashes (should be replaced with hyphens)
    em_dash_count = html_content.count('—')
    en_dash_count = html_content.count('–')
    if em_dash_count > 0:
        critical.append(f"❌ Found {em_dash_count} em dashes (—) - should be replaced")
    if en_dash_count > 0:
        critical.append(f"❌ Found {en_dash_count} en dashes (–) - should be replaced")
    
    # 2. Academic citations [N] in body (excluding script/JSON-LD)
    # Remove script tags first to avoid false positives
    body_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    academic_cites = re.findall(r'\[\d+\]', body_content)
    if len(academic_cites) > 0:
        critical.append(f"❌ Found {len(academic_cites)} academic citations [N] in body")
    
    # 3. Double-prefixed H2 titles ("What is What is")
    double_prefix_matches = re.findall(r'<h2[^>]*>(?:What is What is|How does How does|Why is Why is)', html_content, re.IGNORECASE)
    if double_prefix_matches:
        critical.append(f"❌ Found {len(double_prefix_matches)} double-prefixed H2 titles")
    
    # 4. Orphaned periods at start of paragraph or list item
    orphaned_periods = re.findall(r'<(?:p|li)>\s*\.\s*(?:\d+\.?\s*)?[A-Z]', html_content)
    if orphaned_periods:
        critical.append(f"❌ Found {len(orphaned_periods)} orphaned periods at start of content")
    
    # 5. Duplicate content (paragraph immediately followed by <ul> with same content)
    duplicate_pattern = re.findall(r'</p>\s*<ul>\s*<li>', html_content)
    if len(duplicate_pattern) > 5:  # Some are legitimate
        critical.append(f"⚠️ Found {len(duplicate_pattern)} paragraph+list patterns - check for duplicates")
    
    # 6. Raw markdown in HTML (**bold**, *italic*)
    markdown_bold = re.findall(r'(?<![*])\*\*[^*]+\*\*(?![*])', html_content)
    markdown_italic = re.findall(r'(?<![*])\*[^*]+\*(?![*])', html_content)
    if markdown_bold:
        critical.append(f"❌ Found {len(markdown_bold)} raw markdown **bold** patterns")
    if len(markdown_italic) > 3:  # Some might be legitimate
        warnings.append(f"⚠️ Found {len(markdown_italic)} raw markdown *italic* patterns")
    
    # 7. Truncated list items (items ending with articles/prepositions)
    truncated_items = re.findall(r'<li>[^<]*\s+(?:a|an|the|to|of|and|with|for)\s*</li>', html_content, re.IGNORECASE)
    if truncated_items:
        critical.append(f"❌ Found {len(truncated_items)} truncated list items")
    
    # 8. Sources starting at wrong number ([2]: instead of [1]:)
    sources_section = re.search(r'<section class="citations">.*?</section>', html_content, re.DOTALL)
    if sources_section:
        first_source = re.search(r'\[(\d+)\]:', sources_section.group())
        if first_source and first_source.group(1) != '1':
            critical.append(f"❌ Sources start at [{first_source.group(1)}] instead of [1]")
    
    # 9. Empty sections
    empty_sections = re.findall(r'<(?:p|li|div)>\s*</(?:p|li|div)>', html_content)
    if len(empty_sections) > 2:
        critical.append(f"❌ Found {len(empty_sections)} empty HTML tags")
    
    # ===== WARNINGS =====
    
    # 10. Missing meta tags
    if 'property="og:title"' not in html_content:
        warnings.append("⚠️ Missing og:title meta tag")
    if 'property="og:description"' not in html_content:
        warnings.append("⚠️ Missing og:description meta tag")
    if 'property="article:published_time"' not in html_content:
        warnings.append("⚠️ Missing article:published_time meta tag")
    
    # 11. Check date format (should be ISO 8601)
    date_match = re.search(r'content="(\d{2}\.\d{2}\.\d{4})"', html_content)
    if date_match:
        warnings.append(f"⚠️ Date in European format ({date_match.group(1)}) - should be ISO 8601")
    
    # 12. Check for external links in body
    body_main = re.search(r'<main[^>]*>.*?</main>', html_content, re.DOTALL)
    if body_main:
        external_links = re.findall(r'<a[^>]*href="https?://[^"]+class="citation"', body_main.group())
        if len(external_links) < 2:
            warnings.append(f"⚠️ Only {len(external_links)} external citation links in body")
    
    # 13. Check for internal links
    internal_links = re.findall(r'<a[^>]*href="[^"]*(?:magazine|blog|article)[^"]*"', html_content)
    if len(internal_links) < 1:
        warnings.append("⚠️ No internal links found")
    
    # 14. Check TOC exists and has entries
    toc = re.search(r'<div class="toc">.*?</div>', html_content, re.DOTALL)
    if not toc:
        warnings.append("⚠️ Table of Contents not found")
    else:
        toc_items = re.findall(r'<li><a href="#[^"]+">([^<]+)</a></li>', toc.group())
        if len(toc_items) < 3:
            warnings.append(f"⚠️ TOC has only {len(toc_items)} entries (should be 3+)")
        # Check for truncated TOC entries
        for item in toc_items:
            if item.endswith('...') and len(item) < 20:
                warnings.append(f"⚠️ TOC entry over-truncated: '{item}'")
    
    # 15. Check FAQ exists
    faq = re.search(r'<section class="faq">', html_content)
    if not faq:
        warnings.append("⚠️ FAQ section not found")
    
    # 16. Check schema markup
    if 'application/ld+json' not in html_content:
        warnings.append("⚠️ JSON-LD schema markup not found")
    
    # 17. Escaped HTML tags
    escaped_html = re.findall(r'&lt;/?(?:p|li|ul|ol|div|span|h[1-6])&gt;', html_content)
    if escaped_html:
        warnings.append(f"⚠️ Found {len(escaped_html)} escaped HTML tags")
    
    # 18. "Here are key points:" type phrases (should be cleaned)
    summary_phrases = re.findall(r'Here are (?:the )?(?:key )?(?:points|takeaways|considerations)', html_content, re.IGNORECASE)
    if summary_phrases:
        warnings.append(f"⚠️ Found {len(summary_phrases)} 'Here are key points:' type phrases")
    
    return critical, warnings


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python check_html_quality.py <html_file> [html_file2] ...")
        print("\nExample:")
        print("  python check_html_quality.py output/batch_test_1/index.html")
        sys.exit(1)
    
    all_passed = True
    
    for filepath in sys.argv[1:]:
        path = Path(filepath)
        if not path.exists():
            print(f"❌ File not found: {filepath}")
            all_passed = False
            continue
        
        print(f"\n{'='*60}")
        print(f"Checking: {filepath}")
        print('='*60)
        
        html_content = path.read_text()
        critical, warnings = check_html_quality(html_content, filepath)
        
        if critical:
            print("\n🔴 CRITICAL ISSUES:")
            for issue in critical:
                print(f"  {issue}")
            all_passed = False
        
        if warnings:
            print("\n🟡 WARNINGS:")
            for warning in warnings:
                print(f"  {warning}")
        
        if not critical and not warnings:
            print("\n✅ All checks passed!")
        elif not critical:
            print("\n✅ No critical issues (warnings only)")
        
        # Summary
        print(f"\nSummary: {len(critical)} critical, {len(warnings)} warnings")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL FILES PASSED")
    else:
        print("❌ SOME FILES HAVE ISSUES")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

