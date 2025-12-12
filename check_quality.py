#!/usr/bin/env python3
"""
Quality Check Script for OpenBlog HTML Output
Run: python check_quality.py <html_file>
"""

import re
import sys
from pathlib import Path


def check_quality(html_path: str) -> dict:
    """Run all quality checks on HTML file."""
    html = Path(html_path).read_text(encoding='utf-8')
    
    # Get visible content (exclude scripts)
    visible = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    
    # Get body (before sources section)
    body_end = html.find('<p>[1]:') if '<p>[1]:' in html else len(html)
    body = visible[:body_end] if body_end < len(visible) else visible
    
    results = {}
    
    # Critical checks (must be 0)
    results['raw_bold'] = len(re.findall(r'\*\*[^*]+\*\*', visible))
    results['raw_italic'] = len(re.findall(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', visible))
    results['n_citations'] = len(re.findall(r'\[\d+\]', body))
    results['unverified'] = html.count('[UNVERIFIED]')
    results['em_dashes'] = html.count('—')
    results['en_dashes'] = html.count('–')
    results['duplicate_phrases'] = len(re.findall(
        r'Here are key points|Important considerations|Key benefits include', 
        body, re.I
    ))
    
    # Content checks
    results['dot_dash'] = len(re.findall(r'\.\s*-\s+[A-Z]', html))
    
    # Find truncated sentences
    truncated = re.findall(r'<li>([^<]*\b(?:to|of|the|and|with|for|in|on|at|from|a|an))\s*</li>', html)
    results['truncated_items'] = len(truncated)
    results['truncated_examples'] = truncated[:3] if truncated else []
    
    # Find duplicate paragraphs
    paras = re.findall(r'<p>([^<]{50,})</p>', html)
    results['duplicate_paras'] = len(paras) - len(set(paras))
    
    # Feature checks
    results['has_toc'] = 'class="toc"' in html and 'Table of Contents' in html
    results['toc_items'] = len(re.findall(r'<li><a href="#toc_', html))
    results['images'] = len(re.findall(r'src="[^"]*\.(webp|png|jpg)"', html))
    results['internal_links'] = len(re.findall(r'href="https://[^"]*scaile[^"]+"', body))
    results['sources'] = len(re.findall(r'<p>\[\d+\]:', html))
    results['has_faq'] = 'class="faq"' in html
    results['has_paa'] = 'class="paa"' in html
    results['has_schema'] = 'application/ld+json' in html
    
    # Size
    results['html_size'] = len(html)
    results['body_words'] = len(body.split())
    
    return results


def print_report(results: dict):
    """Print quality report."""
    print("=" * 60)
    print("QUALITY CHECK REPORT")
    print("=" * 60)
    print()
    
    # Critical (must be 0)
    print("CRITICAL (must be 0):")
    critical = [
        ('Raw **bold**', results['raw_bold']),
        ('[N] in body', results['n_citations']),
        ('[UNVERIFIED]', results['unverified']),
        ('Em dashes', results['em_dashes']),
        ('Duplicate phrases', results['duplicate_phrases']),
        ('". - " pattern', results['dot_dash']),
        ('Truncated items', results['truncated_items']),
        ('Duplicate paras', results['duplicate_paras']),
    ]
    
    all_pass = True
    for name, value in critical:
        status = '✅' if value == 0 else '❌'
        if value != 0:
            all_pass = False
        print(f"  {status} {name}: {value}")
    
    if results['truncated_examples']:
        print(f"     Examples: {results['truncated_examples']}")
    
    print()
    print("FEATURES:")
    features = [
        ('TOC present', results['has_toc'], True),
        ('TOC items', results['toc_items'], 5),
        ('Images', results['images'], 1),
        ('Internal links', results['internal_links'], 1),
        ('Sources', results['sources'], 5),
        ('FAQ section', results['has_faq'], True),
        ('PAA section', results['has_paa'], True),
        ('JSON-LD Schema', results['has_schema'], True),
    ]
    
    for name, value, target in features:
        if isinstance(target, bool):
            status = '✅' if value == target else '⚠️'
        else:
            status = '✅' if value >= target else '⚠️'
        print(f"  {status} {name}: {value}")
    
    print()
    print(f"SIZE: {results['html_size']:,} chars, ~{results['body_words']:,} words")
    print()
    print("=" * 60)
    print(f"RESULT: {'✅ ALL CHECKS PASS' if all_pass else '❌ ISSUES FOUND'}")
    print("=" * 60)
    
    return all_pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_quality.py <html_file>")
        sys.exit(1)
    
    html_path = sys.argv[1]
    if not Path(html_path).exists():
        print(f"File not found: {html_path}")
        sys.exit(1)
    
    results = check_quality(html_path)
    success = print_report(results)
    sys.exit(0 if success else 1)

