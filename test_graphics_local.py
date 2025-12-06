#!/usr/bin/env python3
"""
Local test script for graphics generation.
Tests HTML-based graphics (openfigma style) locally.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from service.graphics_generator import GraphicsGenerator, GraphicsGenerationRequest


async def test_graphics():
    """Test all graphic types locally."""
    print("🎨 Testing Graphics Generation Locally")
    print("=" * 70)
    
    generator = GraphicsGenerator()
    
    tests = [
        {
            "name": "Headline Graphic",
            "request": GraphicsGenerationRequest(
                graphic_type="headline",
                content={
                    "headline": "Client drove a 7x increase in demo requests",
                    "bold_parts": ["Client", "7x increase", "demo requests"],
                    "muted_parts": ["drove a", "in"]
                },
                company_data={"name": "Test Company"},
                project_folder_id=None,
                dimensions=(1080, 1350)
            ),
            "filename": "test_headline_local.png"
        },
        {
            "name": "Quote Graphic",
            "request": GraphicsGenerationRequest(
                graphic_type="quote",
                content={
                    "quote": "SCAILE transformed our content strategy. The AI-powered approach delivered results we never expected.",
                    "author": "Sarah Johnson",
                    "role": "CMO, TechCorp"
                },
                project_folder_id=None,
                dimensions=(1080, 1350)
            ),
            "filename": "test_quote_local.png"
        },
        {
            "name": "Metric Graphic",
            "request": GraphicsGenerationRequest(
                graphic_type="metric",
                content={
                    "value": "7x",
                    "label": "Increase in Demo Requests",
                    "change": "+150% YoY",
                    "change_type": "positive"
                },
                project_folder_id=None,
                dimensions=(1080, 1350)
            ),
            "filename": "test_metric_local.png"
        },
        {
            "name": "CTA Graphic",
            "request": GraphicsGenerationRequest(
                graphic_type="cta",
                content={
                    "headline": "Ready to Transform Your Content Strategy?",
                    "description": "Join hundreds of companies using AI-powered content to drive growth.",
                    "button_text": "Get Started"
                },
                project_folder_id=None,
                dimensions=(1080, 1350)
            ),
            "filename": "test_cta_local.png"
        },
        {
            "name": "Infographic",
            "request": GraphicsGenerationRequest(
                graphic_type="infographic",
                content={
                    "title": "Content Pipeline Stages",
                    "items": [
                        "Stage 1: Data Collection",
                        "Stage 2: AI Analysis",
                        "Stage 3: Content Generation",
                        "Stage 4: Quality Review"
                    ]
                },
                project_folder_id=None,
                dimensions=(1080, 1350)
            ),
            "filename": "test_infographic_local.png"
        }
    ]
    
    desktop = Path.home() / "Desktop"
    
    for i, test in enumerate(tests, 1):
        print(f"\n📝 Test {i}/{len(tests)}: {test['name']}")
        print("-" * 70)
        
        try:
            print("⏳ Generating HTML and converting to PNG...")
            result = await generator.generate(test['request'])
            
            if result.success and result.image_url:
                # Extract base64 image
                if result.image_url.startswith('data:image'):
                    header, encoded = result.image_url.split(',', 1)
                    import base64
                    image_data = base64.b64decode(encoded)
                    
                    output_path = desktop / test['filename']
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"✅ Generated successfully!")
                    print(f"   Time: {result.generation_time_seconds:.1f}s")
                    print(f"   Size: {len(image_data):,} bytes")
                    print(f"📸 Saved to: {output_path}")
                    
                    # Open the last one
                    if i == len(tests):
                        import subprocess
                        subprocess.run(['open', str(output_path)])
                        print(f"✅ Opened!")
                else:
                    print(f"📸 Image URL: {result.image_url}")
            else:
                print(f"❌ Error: {result.error}")
                if i == 1:  # Stop on first error
                    break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            if i == 1:  # Stop on first error
                break
    
    print("\n" + "=" * 70)
    print("✅ Testing complete!")
    print(f"📁 Check your Desktop for generated graphics")


if __name__ == "__main__":
    asyncio.run(test_graphics())

