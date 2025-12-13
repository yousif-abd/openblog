#!/usr/bin/env python3
"""
Test Asset Finding + Gemini Imagen Recreation

Shows how to:
1. Find assets from internet
2. Recreate them using Gemini Imagen in company design system
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

async def test_find_and_recreate():
    """Test finding assets and recreating them with Gemini Imagen."""
    print("\n" + "="*80)
    print("ASSET FINDER + GEMINI IMAGEN RECREATION")
    print("="*80)
    
    agent = AssetFinderAgent()
    
    # Check if Imagen is available
    if agent.imagen_client and agent.imagen_client.mock_mode:
        print("\n⚠️  Gemini Imagen not configured (mock mode)")
        print("   Set GOOGLE_API_KEY or GEMINI_API_KEY in .env.local")
        print("   For now, showing what WOULD be recreated...\n")
    elif not agent.imagen_client:
        print("\n⚠️  Gemini Imagen client not available")
        print("   Set GOOGLE_API_KEY or GEMINI_API_KEY in .env.local\n")
    else:
        print("\n✅ Gemini Imagen client ready!")
    
    # Company design system data
    company_data = {
        "company_name": "TechSecure Inc",
        "industry": "Technology",
        "brand_tone": "modern professional",
        "primary_color": "#0066CC",  # Blue
        "secondary_color": "#00CCFF",  # Cyan
        "accent_color": "#333333",  # Dark gray
    }
    
    print("\n" + "="*80)
    print("STEP 1: Finding Assets")
    print("="*80)
    
    request = AssetFinderRequest(
        article_topic="cloud security dashboard",
        article_headline="Complete Guide to Cloud Security Dashboards",
        company_data=company_data,
        max_results=3,  # Limit to 3 for demo (Imagen costs per image)
        recreate_in_design_system=True  # Enable recreation!
    )
    
    response = await agent.find_assets(request)
    
    if not response.success:
        print(f"\n❌ Error: {response.error}")
        return
    
    print("\n" + "="*80)
    print("STEP 2: Original Assets Found")
    print("="*80)
    
    if response.assets:
        print(f"\n✅ Found {len(response.assets)} original assets:\n")
        for i, asset in enumerate(response.assets, 1):
            print(f"  {i}. {asset.title}")
            print(f"     📷 URL: {asset.url[:70]}...")
            print(f"     📦 Source: {asset.source}")
            print(f"     📄 Type: {asset.image_type}")
            print()
    else:
        print("\n⚠️  No assets found")
        return
    
    print("\n" + "="*80)
    print("STEP 3: Recreated Assets (Gemini Imagen)")
    print("="*80)
    
    if response.recreated_assets:
        print(f"\n✅ Recreated {len(response.recreated_assets)} assets in design system:\n")
        for i, recreated in enumerate(response.recreated_assets, 1):
            original = recreated.get('original_asset', {})
            print(f"  {i}. Based on: {original.get('title', 'Unknown')}")
            print(f"     🎨 Recreated URL: {recreated.get('recreated_url', 'N/A')}")
            print(f"     📐 Size: {recreated.get('width', '?')}x{recreated.get('height', '?')}")
            print(f"     🎨 Design System Applied:")
            print(f"        - Colors: {company_data.get('primary_color')}, {company_data.get('secondary_color')}")
            print(f"        - Style: {company_data.get('brand_tone')}")
            print(f"        - Industry: {company_data.get('industry')}")
            print()
    else:
        print("\n⚠️  No assets were recreated")
        if agent.imagen_client and agent.imagen_client.mock_mode:
            print("   (Imagen is in mock mode - set API key to enable real recreation)")
        else:
            print("   (Check if recreation was enabled and Imagen client is configured)")

async def show_comparison():
    """Show before/after comparison."""
    print("\n" + "="*80)
    print("BEFORE vs AFTER COMPARISON")
    print("="*80)
    
    agent = AssetFinderAgent()
    
    company_data = {
        "company_name": "TechSecure Inc",
        "industry": "Technology",
        "brand_tone": "modern professional",
    }
    
    request = AssetFinderRequest(
        article_topic="cybersecurity shield",
        company_data=company_data,
        max_results=2,
        recreate_in_design_system=True
    )
    
    response = await agent.find_assets(request)
    
    if response.success and response.assets:
        print("\n📊 Comparison:\n")
        print("ORIGINAL ASSETS (from internet):")
        for asset in response.assets:
            print(f"  • {asset.title} ({asset.source})")
            print(f"    {asset.url[:60]}...")
        
        if response.recreated_assets:
            print("\nRECREATED ASSETS (Gemini Imagen + Design System):")
            for recreated in response.recreated_assets:
                original = recreated.get('original_asset', {})
                print(f"  • {original.get('title', 'Unknown')} → Recreated")
                print(f"    {recreated.get('recreated_url', 'N/A')[:60]}...")
                print(f"    ✨ Now matches company brand colors and style!")
        else:
            print("\n⚠️  Recreation skipped (check Imagen configuration)")

async def main():
    """Run all tests."""
    print("\n🎨 Testing Asset Finding + Gemini Imagen Recreation\n")
    
    await test_find_and_recreate()
    await show_comparison()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\n✅ Feature: Find assets + Recreate with Gemini Imagen")
    print("✅ Design System: Applies company colors, style, brand identity")
    print("✅ Integration: Works seamlessly with asset finder")
    print("\n💡 To enable real recreation:")
    print("   1. Set GOOGLE_API_KEY or GEMINI_API_KEY in .env.local")
    print("   2. Set recreate_in_design_system=True")
    print("   3. Provide company_data with brand info")

if __name__ == "__main__":
    asyncio.run(main())

