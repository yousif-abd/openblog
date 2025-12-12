#!/usr/bin/env python3
"""Run a single article generation test."""
import asyncio
import sys
import os

sys.path.insert(0, '.')
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.local')
if 'GOOGLE_GEMINI_API_KEY' in os.environ and 'GEMINI_API_KEY' not in os.environ:
    os.environ['GEMINI_API_KEY'] = os.environ['GOOGLE_GEMINI_API_KEY']


async def main():
    try:
        from service.api import write_blog, BlogGenerationRequest
        
        print("🚀 Starting generation...")
        result = await write_blog(BlogGenerationRequest(
            primary_keyword='AI cybersecurity automation',
            company_url='https://scaile.tech',
            language='en',
            country='US',
        ))
        
        if not result.success:
            print(f"❌ FAILED: {result.error}")
            return 1
        
        html = result.html_content or result.html or ''
        if not html:
            print("❌ No HTML content")
            return 1
        
        Path('PROD_TEST.html').write_text(html, encoding='utf-8')
        print(f"✅ SUCCESS: {len(html):,} chars saved to PROD_TEST.html")
        return 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

