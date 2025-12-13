#!/usr/bin/env python3
"""
Generate HTML Preview: Original vs Recreated Assets

Shows side-by-side comparison of:
- Original assets found from internet
- Recreated assets using Gemini Imagen + Design System
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

def generate_comparison_html(original_assets, recreated_assets, company_data):
    """Generate HTML showing original vs recreated comparison."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Original vs Recreated Assets - Gemini Imagen</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            opacity: 0.9;
        }
        .design-system {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .design-system h2 {
            color: #667eea;
            margin-bottom: 15px;
        }
        .design-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .design-item {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 6px;
        }
        .design-item strong {
            color: #667eea;
        }
        .comparison-grid {
            display: grid;
            gap: 30px;
            margin-top: 20px;
        }
        .comparison-item {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .comparison-item h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        .side-by-side {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .asset-box {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }
        .asset-box h4 {
            background: #f8f9fa;
            padding: 10px;
            margin: 0;
            color: #667eea;
            font-size: 0.9em;
        }
        .asset-image {
            width: 100%;
            height: 300px;
            object-fit: cover;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .asset-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .asset-info {
            padding: 15px;
            font-size: 0.9em;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 5px;
        }
        .badge-original { background: #28a745; color: white; }
        .badge-recreated { background: #667eea; color: white; }
        .url-link {
            color: #667eea;
            text-decoration: none;
            word-break: break-all;
            font-size: 0.85em;
        }
        .url-link:hover {
            text-decoration: underline;
        }
        @media (max-width: 768px) {
            .side-by-side {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Original vs Recreated Assets</h1>
        <p class="subtitle">Gemini Imagen 4.0 + Design System Recreation</p>
"""
    
    # Design System Info
    html += f"""
        <div class="design-system">
            <h2>🎨 Design System Applied</h2>
            <div class="design-info">
                <div class="design-item">
                    <strong>Company:</strong> {company_data.get('company_name', 'N/A')}
                </div>
                <div class="design-item">
                    <strong>Industry:</strong> {company_data.get('industry', 'N/A')}
                </div>
                <div class="design-item">
                    <strong>Style:</strong> {company_data.get('brand_tone', 'N/A')}
                </div>
                <div class="design-item">
                    <strong>Colors:</strong> {', '.join([company_data.get('primary_color', ''), company_data.get('secondary_color', '')]) if company_data.get('primary_color') else 'N/A'}
                </div>
            </div>
        </div>
"""
    
    # Comparison Items
    html += '<div class="comparison-grid">'
    
    for i, (original, recreated) in enumerate(zip(original_assets, recreated_assets), 1):
        html += f"""
        <div class="comparison-item">
            <h3>Asset {i}: {original['title']}</h3>
            <div class="side-by-side">
                <div class="asset-box">
                    <h4><span class="badge badge-original">ORIGINAL</span> {original['source']}</h4>
                    <div class="asset-image">
                        <a href="{original['url']}" target="_blank">
                            <img src="{original['url']}" alt="{original['title']}" onerror="this.parentElement.innerHTML='<div style=\\'padding:20px\\'>Image not available<br><small>Click to view source</small></div>'">
                        </a>
                    </div>
                    <div class="asset-info">
                        <strong>Title:</strong> {original['title']}<br>
                        <strong>Source:</strong> {original['source']}<br>
                        <strong>Type:</strong> {original['image_type']}<br>
                        <a href="{original['url']}" target="_blank" class="url-link">View Original →</a>
                    </div>
                </div>
                <div class="asset-box">
                    <h4><span class="badge badge-recreated">RECREATED</span> Gemini Imagen 4.0</h4>
                    <div class="asset-image">
                        <a href="{recreated['recreated_url']}" target="_blank">
                            <img src="{recreated['recreated_url']}" alt="Recreated {original['title']}" onerror="this.parentElement.innerHTML='<div style=\\'padding:20px\\'>Recreated image<br><small>Click to view</small></div>'">
                        </a>
                    </div>
                    <div class="asset-info">
                        <strong>Title:</strong> {original['title']} (Recreated)<br>
                        <strong>Method:</strong> Gemini Imagen 4.0<br>
                        <strong>Design System:</strong> Applied ✨<br>
                        <a href="{recreated['recreated_url']}" target="_blank" class="url-link">View Recreated →</a>
                    </div>
                </div>
            </div>
        </div>
"""
    
    html += """
        </div>
    </div>
</body>
</html>
"""
    
    return html

async def main():
    """Generate comparison preview."""
    print("🎨 Finding assets and recreating with Gemini Imagen...\n")
    
    agent = AssetFinderAgent()
    
    if agent.imagen_client and agent.imagen_client.mock_mode:
        print("⚠️  Imagen is in mock mode - will show structure but not real images")
        print("   Set GOOGLE_API_KEY or GEMINI_API_KEY to enable real recreation\n")
    
    company_data = {
        "company_name": "TechSecure Inc",
        "industry": "Technology",
        "brand_tone": "modern professional",
        "primary_color": "#0066CC",
        "secondary_color": "#00CCFF",
        "accent_color": "#333333",
    }
    
    request = AssetFinderRequest(
        article_topic="cloud security dashboard",
        company_data=company_data,
        max_results=3,
        recreate_in_design_system=True
    )
    
    response = await agent.find_assets(request)
    
    if not response.success or not response.assets:
        print("❌ No assets found")
        return
    
    if not response.recreated_assets:
        print("⚠️  No assets were recreated")
        return
    
    # Prepare data for HTML
    original_assets = [
        {
            'title': asset.title,
            'url': asset.url,
            'source': asset.source,
            'image_type': asset.image_type
        }
        for asset in response.assets[:len(response.recreated_assets)]
    ]
    
    recreated_assets = [
        {
            'recreated_url': rec.get('recreated_url', ''),
            'original_asset': {
                'title': rec.get('original_title', ''),
                'url': rec.get('original_url', '')
            }
        }
        for rec in response.recreated_assets
    ]
    
    # Generate HTML
    html = generate_comparison_html(original_assets, recreated_assets, company_data)
    
    output_file = 'preview_imagen_recreation.html'
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✅ Comparison preview generated: {output_file}")
    print(f"   Open it in your browser to see original vs recreated assets!")
    print(f"\n📊 Summary:")
    print(f"   • Found: {len(response.assets)} original assets")
    print(f"   • Recreated: {len(response.recreated_assets)} assets with Gemini Imagen")
    print(f"   • Design System: {company_data['brand_tone']} style, {company_data['industry']} industry")

if __name__ == "__main__":
    asyncio.run(main())

