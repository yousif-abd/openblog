#!/usr/bin/env python3
"""
Show Examples of Assets Found

Demonstrates both Gemini and DataForSEO approaches with real examples.
"""

import asyncio
import os
from pathlib import Path

# Load env
env_file = Path('.env.local')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip('"').strip("'")

from pipeline.agents.asset_finder import AssetFinderAgent, AssetFinderRequest

async def show_gemini_examples():
    """Show examples from Gemini + Google Search approach."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Gemini + Google Search (images: prefix)")
    print("="*80)
    
    agent = AssetFinderAgent()
    
    # Example 1: Cloud Security
    print("\n📝 Query: 'cloud security statistics chart'")
    print("-" * 80)
    
    request1 = AssetFinderRequest(
        article_topic="cloud security statistics chart",
        max_results=5
    )
    
    response1 = await agent.find_assets(request1)
    
    if response1.success and response1.assets:
        print(f"\n✅ Found {len(response1.assets)} assets:\n")
        for i, asset in enumerate(response1.assets, 1):
            print(f"  {i}. {asset.title}")
            print(f"     📷 URL: {asset.url[:70]}...")
            print(f"     📦 Source: {asset.source}")
            print(f"     📐 Size: {asset.width}x{asset.height}" if asset.width and asset.height else "     📐 Size: Unknown")
            print(f"     📄 Type: {asset.image_type}")
            print()
    else:
        print(f"\n⚠️  No assets found: {response1.error}")
    
    # Example 2: AI Automation
    print("\n" + "="*80)
    print("EXAMPLE 2: AI Automation Infographic")
    print("="*80)
    print("\n📝 Query: 'AI automation workflow diagram'")
    print("-" * 80)
    
    request2 = AssetFinderRequest(
        article_topic="AI automation workflow diagram",
        max_results=3
    )
    
    response2 = await agent.find_assets(request2)
    
    if response2.success and response2.assets:
        print(f"\n✅ Found {len(response2.assets)} assets:\n")
        for i, asset in enumerate(response2.assets, 1):
            print(f"  {i}. {asset.title}")
            print(f"     📷 URL: {asset.url[:70]}...")
            print(f"     📦 Source: {asset.source}")
            print()
    else:
        print(f"\n⚠️  No assets found: {response2.error}")

async def show_dataforseo_examples():
    """Show examples from DataForSEO Google Images API."""
    print("\n" + "="*80)
    print("EXAMPLE 3: DataForSEO Google Images API (Fallback)")
    print("="*80)
    
    from pipeline.agents.google_images_finder import GoogleImagesFinder
    
    finder = GoogleImagesFinder()
    
    if not finder.is_configured():
        print("\n⚠️  DataForSEO not configured - skipping examples")
        return
    
    print("\n📝 Query: 'cloud security statistics chart'")
    print("   Filters: size=large, license=creativeCommons")
    print("-" * 80)
    
    images = await finder.search_images(
        query="cloud security statistics chart",
        max_results=5,
        size="large",
        license="creativeCommons"
    )
    
    if images:
        print(f"\n✅ Found {len(images)} images:\n")
        for i, img in enumerate(images, 1):
            print(f"  {i}. {img.title}")
            print(f"     📷 URL: {img.url[:70]}...")
            print(f"     📦 Source: {img.source}")
            print(f"     📐 Size: {img.width}x{img.height}" if img.width and img.height else "     📐 Size: Unknown")
            print(f"     📄 License: {img.license or 'Unknown'}")
            print()
    else:
        print("\n⚠️  No images found (may need parsing adjustment)")

async def show_comparison():
    """Show side-by-side comparison."""
    print("\n" + "="*80)
    print("COMPARISON: Gemini vs DataForSEO")
    print("="*80)
    
    print("\n📝 Same Query: 'cloud security dashboard'")
    print("-" * 80)
    
    # Gemini
    agent = AssetFinderAgent()
    request = AssetFinderRequest(
        article_topic="cloud security dashboard",
        max_results=3
    )
    
    gemini_response = await agent.find_assets(request)
    
    print("\n🔵 Gemini + Google Search:")
    if gemini_response.success and gemini_response.assets:
        print(f"   ✅ Found {len(gemini_response.assets)} assets")
        for asset in gemini_response.assets[:2]:
            print(f"      • {asset.title[:50]} ({asset.source})")
    else:
        print(f"   ⚠️  {gemini_response.error or 'No results'}")
    
    # DataForSEO
    from pipeline.agents.google_images_finder import GoogleImagesFinder
    finder = GoogleImagesFinder()
    
    if finder.is_configured():
        print("\n🟢 DataForSEO Google Images:")
        images = await finder.search_images(
            query="cloud security dashboard",
            max_results=3,
            size="large"
        )
        if images:
            print(f"   ✅ Found {len(images)} images")
            for img in images[:2]:
                print(f"      • {img.title[:50]} ({img.source})")
        else:
            print("   ⚠️  No results (may need parsing adjustment)")

async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("ASSET FINDER - REAL EXAMPLES")
    print("="*80)
    print("\nShowing real examples of assets found by both approaches...")
    
    # Show Gemini examples
    await show_gemini_examples()
    
    # Show DataForSEO examples
    await show_dataforseo_examples()
    
    # Show comparison
    await show_comparison()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\n✅ Gemini + Google Search: Primary method (free, fast)")
    print("✅ DataForSEO Google Images: Fallback (better filtering)")
    print("\n💡 Both approaches are integrated and ready to use!")

if __name__ == "__main__":
    asyncio.run(main())

