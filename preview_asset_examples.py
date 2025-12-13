#!/usr/bin/env python3
"""
Generate HTML Preview of Found Assets

Creates an HTML file showing examples of assets found by both approaches.
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

def generate_html_preview(assets_data):
    """Generate HTML preview of assets."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Asset Finder Examples</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        .query-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        .query-info strong {
            color: #667eea;
        }
        .assets-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .asset-card {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
            background: white;
        }
        .asset-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }
        .asset-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 14px;
        }
        .asset-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .asset-info {
            padding: 15px;
        }
        .asset-title {
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        .asset-meta {
            font-size: 0.9em;
            color: #666;
            margin: 5px 0;
        }
        .asset-meta strong {
            color: #667eea;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 5px;
        }
        .badge-unsplash { background: #000; color: white; }
        .badge-pexels { background: #05A081; color: white; }
        .badge-pixabay { background: #2BAF2B; color: white; }
        .badge-other { background: #666; color: white; }
        .url-link {
            color: #667eea;
            text-decoration: none;
            word-break: break-all;
            font-size: 0.85em;
        }
        .url-link:hover {
            text-decoration: underline;
        }
        .stats {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            text-align: center;
        }
        .stats strong {
            color: #667eea;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Asset Finder Examples</h1>
"""
    
    for section in assets_data:
        html += f"""
        <div class="section">
            <h2>{section['title']}</h2>
            <div class="query-info">
                <strong>Query:</strong> {section['query']}<br>
                <strong>Method:</strong> {section['method']}
            </div>
            <div class="assets-grid">
"""
        
        for asset in section['assets']:
            source_lower = asset['source'].lower()
            badge_class = 'badge-other'
            if 'unsplash' in source_lower:
                badge_class = 'badge-unsplash'
            elif 'pexels' in source_lower:
                badge_class = 'badge-pexels'
            elif 'pixabay' in source_lower:
                badge_class = 'badge-pixabay'
            
            html += f"""
                <div class="asset-card">
                    <div class="asset-image">
                        <a href="{asset['url']}" target="_blank">
                            <img src="{asset['url']}" alt="{asset['title']}" onerror="this.parentElement.innerHTML='<div style=\\'padding:20px\\'>Image not available<br><small>Click to view source</small></div>'">
                        </a>
                    </div>
                    <div class="asset-info">
                        <div class="asset-title">{asset['title']}</div>
                        <div class="asset-meta">
                            <span class="badge {badge_class}">{asset['source']}</span>
                            {f"<strong>Size:</strong> {asset['width']}x{asset['height']}<br>" if asset.get('width') and asset.get('height') else ""}
                            <strong>Type:</strong> {asset['image_type']}<br>
                            <a href="{asset['url']}" target="_blank" class="url-link">View Source →</a>
                        </div>
                    </div>
                </div>
"""
        
        html += f"""
            </div>
            <div class="stats">
                <strong>✅ Found {len(section['assets'])} assets</strong>
            </div>
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    return html

async def main():
    """Generate examples and create HTML preview."""
    print("🔍 Finding assets for examples...\n")
    
    agent = AssetFinderAgent()
    assets_data = []
    
    # Example 1: Cloud Security
    print("📝 Example 1: Cloud Security Statistics Chart")
    request1 = AssetFinderRequest(
        article_topic="cloud security statistics chart",
        max_results=6
    )
    response1 = await agent.find_assets(request1)
    
    if response1.success and response1.assets:
        assets_data.append({
            'title': 'Example 1: Cloud Security Statistics Chart',
            'query': 'cloud security statistics chart',
            'method': 'Gemini + Google Search (images: prefix)',
            'assets': [
                {
                    'title': asset.title,
                    'url': asset.url,
                    'source': asset.source,
                    'image_type': asset.image_type,
                    'width': asset.width,
                    'height': asset.height
                }
                for asset in response1.assets
            ]
        })
        print(f"   ✅ Found {len(response1.assets)} assets\n")
    
    # Example 2: AI Automation
    print("📝 Example 2: AI Automation Workflow")
    request2 = AssetFinderRequest(
        article_topic="AI automation workflow diagram",
        max_results=4
    )
    response2 = await agent.find_assets(request2)
    
    if response2.success and response2.assets:
        assets_data.append({
            'title': 'Example 2: AI Automation Workflow Diagram',
            'query': 'AI automation workflow diagram',
            'method': 'Gemini + Google Search (images: prefix)',
            'assets': [
                {
                    'title': asset.title,
                    'url': asset.url,
                    'source': asset.source,
                    'image_type': asset.image_type,
                    'width': asset.width,
                    'height': asset.height
                }
                for asset in response2.assets
            ]
        })
        print(f"   ✅ Found {len(response2.assets)} assets\n")
    
    # Generate HTML
    if assets_data:
        html = generate_html_preview(assets_data)
        output_file = 'preview_asset_examples.html'
        with open(output_file, 'w') as f:
            f.write(html)
        print(f"✅ HTML preview generated: {output_file}")
        print(f"   Open it in your browser to see the images!")
    else:
        print("⚠️  No assets found to preview")

if __name__ == "__main__":
    asyncio.run(main())

