#!/usr/bin/env python3
"""Quick test script for the pipeline with new fixes."""

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
    kw = 'enterprise cloud security automation best practices 2025'
    print(f'🔄 Testing single article: {kw[:40]}...')
    
    try:
        result = await write_blog(BlogGenerationRequest(
            primary_keyword=kw,
            company_url='https://scaile.tech',
            language='en',
            country='US',
        ))
        
        if result.success and (result.html_content or result.html):
            html = result.html_content or result.html
            os.makedirs('output/fixed_test', exist_ok=True)
            with open('output/fixed_test/index.html', 'w') as f:
                f.write(html)
            
            # Quick quality check
            em_dashes = html.count('—')
            en_dashes = html.count('–')
            academic = len(re.findall(r'\[\d+\]', html))
            dup_lists = len(re.findall(r'Here are (?:key|the key)', html, re.IGNORECASE))
            
            print(f'✅ Generated {len(html):,} chars')
            print(f'   Em dashes: {em_dashes}')
            print(f'   En dashes: {en_dashes}')
            print(f'   Academic [N]: {academic}')
            print(f'   "Here are key points": {dup_lists}')
            
            if em_dashes == 0 and en_dashes == 0 and dup_lists == 0:
                print('🎉 All fixes working!')
            else:
                print('⚠️ Some issues remain')
        else:
            print(f'❌ Failed: {result.error}')
    except Exception as e:
        print(f'❌ Error: {str(e)[:100]}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_single())
