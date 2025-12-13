#!/usr/bin/env python3
"""Quick test script for the pipeline with HTML-first approach."""

import asyncio
import sys
import os
import re

sys.path.insert(0, '.')
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.local')
if 'GOOGLE_GEMINI_API_KEY' in os.environ and 'GEMINI_API_KEY' not in os.environ:
    os.environ['GEMINI_API_KEY'] = os.environ['GOOGLE_GEMINI_API_KEY']

print(f"Using API key: {os.environ.get('GEMINI_API_KEY', 'NOT SET')[:20]}...")

from service.api import write_blog, BlogGenerationRequest

async def run_single():
    kw = 'enterprise AI security automation best practices 2025'
    print(f'🔄 Testing single article: {kw[:50]}...')
    print()
    
    try:
        result = await write_blog(BlogGenerationRequest(
            primary_keyword=kw,
            company_url='https://scaile.tech',
            language='en',
            country='US',
        ))
        
        if result.success and (result.html_content or result.html):
            html = result.html_content or result.html
            os.makedirs('output/html_first_test', exist_ok=True)
            output_path = 'output/html_first_test/index.html'
            with open(output_path, 'w') as f:
                f.write(html)
            
            print(f'✅ Generated {len(html):,} chars')
            print(f'📁 Saved to: {output_path}')
            print()
            
            # ============================================
            # COMPREHENSIVE QUALITY CHECK
            # ============================================
            print("=" * 60)
            print("📊 QUALITY CHECK RESULTS")
            print("=" * 60)
            
            issues = []
            
            # 1. Em/En dashes
            em_dashes = html.count('—')
            en_dashes = html.count('–')
            print(f'Em dashes (—): {em_dashes} {"✅" if em_dashes == 0 else "❌"}')
            print(f'En dashes (–): {en_dashes} {"✅" if en_dashes == 0 else "❌"}')
            if em_dashes > 0 or en_dashes > 0:
                issues.append(f"Found {em_dashes} em-dashes and {en_dashes} en-dashes")
            
            # 2. Academic citations [N]
            academic = len(re.findall(r'\[\d+\]', html))
            print(f'Academic [N] citations: {academic} {"✅" if academic == 0 else "⚠️ (should be inline)"}')
            if academic > 0:
                issues.append(f"Found {academic} academic [N] citations")
            
            # 3. Duplicate summary lists
            dup_lists = len(re.findall(r'Here are (?:key|the key)', html, re.IGNORECASE))
            print(f'"Here are key points": {dup_lists} {"✅" if dup_lists == 0 else "❌"}')
            if dup_lists > 0:
                issues.append(f"Found {dup_lists} duplicate summary lists")
            
            # 4. HTML structure (should have proper tags)
            strong_count = len(re.findall(r'<strong>', html))
            ul_count = len(re.findall(r'<ul>', html))
            li_count = len(re.findall(r'<li>', html))
            print(f'HTML <strong> tags: {strong_count} {"✅" if strong_count > 0 else "⚠️"}')
            print(f'HTML <ul> tags: {ul_count} {"✅" if ul_count > 0 else "⚠️"}')
            print(f'HTML <li> tags: {li_count} {"✅" if li_count > 0 else "⚠️"}')
            
            # 5. Markdown remnants (should be 0)
            md_bold = len(re.findall(r'\*\*[^*]+\*\*', html))
            md_lists = len(re.findall(r'^\s*[-*]\s+', html, re.MULTILINE))
            print(f'Markdown **bold**: {md_bold} {"✅" if md_bold == 0 else "❌"}')
            print(f'Markdown - lists: {md_lists} {"✅" if md_lists == 0 else "⚠️ (may be in code blocks)"}')
            if md_bold > 0:
                issues.append(f"Found {md_bold} markdown bold patterns")
            
            # 6. Inline source links (from groundingSupports)
            source_links = len(re.findall(r'<a[^>]+href="https?://[^"]+(?:ibm|gartner|forrester|mckinsey|deloitte|accenture|nist)[^"]*"[^>]*>', html, re.IGNORECASE))
            external_links = len(re.findall(r'<a[^>]+href="https?://(?!scaile)[^"]+', html))
            internal_links = len(re.findall(r'<a[^>]+href="/magazine/', html))
            print(f'External source links: {external_links} {"✅" if external_links > 0 else "⚠️"}')
            print(f'Authoritative source links: {source_links} {"✅" if source_links > 0 else "⚠️"}')
            print(f'Internal /magazine/ links: {internal_links} {"✅" if internal_links > 0 else "⚠️"}')
            
            # 7. References section
            has_references = 'class="references"' in html or 'References</h' in html or '>Sources<' in html
            print(f'References section: {"✅ Present" if has_references else "⚠️ Not found"}')
            
            # 8. Fragment lists (malformed HTML)
            fragment_lists = len(re.findall(r'</li>\s*</ul>\s*[a-z]', html, re.IGNORECASE))
            orphan_li = len(re.findall(r'<li>[^<]{1,30}</li>\s*</ul>\s*<p>', html))
            print(f'Fragment lists: {fragment_lists} {"✅" if fragment_lists == 0 else "❌"}')
            print(f'Orphan short list items: {orphan_li} {"✅" if orphan_li == 0 else "❌"}')
            if fragment_lists > 0 or orphan_li > 0:
                issues.append(f"Found {fragment_lists} fragment lists and {orphan_li} orphan items")
            
            print()
            print("=" * 60)
            if not issues:
                print('🎉 ALL QUALITY CHECKS PASSED!')
            else:
                print(f'⚠️ {len(issues)} ISSUE(S) FOUND:')
                for issue in issues:
                    print(f'   - {issue}')
            print("=" * 60)
            
        else:
            print(f'❌ Failed: {result.error}')
    except Exception as e:
        print(f'❌ Error: {str(e)[:200]}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_single())
