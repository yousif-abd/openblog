"""
Quick Export Test - Export existing article in all formats.

Loads an existing article and exports all formats to Downloads folder.
"""

import json
from pathlib import Path
from datetime import datetime

from pipeline.processors.article_exporter import ArticleExporter

def test_exports():
    """Test all export formats with existing article."""
    print("=" * 80)
    print("QUICK EXPORT TEST")
    print("=" * 80)
    print()
    
    # Find latest test output
    output_dirs = list(Path('output').glob('test-exports-*'))
    if not output_dirs:
        print("❌ No test output found. Run test_all_export_formats.py first.")
        return
    
    latest_dir = max(output_dirs, key=lambda p: p.stat().st_mtime)
    print(f"📁 Loading from: {latest_dir}")
    print()
    
    # Load article and HTML
    article_json = latest_dir / 'article.json'
    html_file = latest_dir / 'index.html'
    
    if not article_json.exists() or not html_file.exists():
        print(f"❌ Missing files in {latest_dir}")
        return
    
    with open(article_json) as f:
        article = json.load(f)
    
    html_content = html_file.read_text()
    
    print(f"✅ Loaded article:")
    print(f"   Headline: {article.get('Headline', 'N/A')[:60]}...")
    print(f"   HTML: {len(html_content)} chars")
    print()
    
    # Create export directory in Downloads
    downloads_dir = Path.home() / "Downloads"
    export_dir = downloads_dir / "openblog_exports" / datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Export directory: {export_dir}")
    print()
    
    # Export all formats
    print("🚀 Exporting all formats...")
    print()
    
    formats = ["html", "markdown", "pdf", "json", "csv", "xlsx"]
    
    try:
        exported_files = ArticleExporter.export_all(
            article=article,
            html_content=html_content,
            output_dir=export_dir,
            formats=formats,
        )
        
        print()
        print("=" * 80)
        print("EXPORT RESULTS")
        print("=" * 80)
        print()
        
        if exported_files:
            print(f"✅ Exported {len(exported_files)} format(s):")
            print()
            
            for format_name, file_path in exported_files.items():
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    size = file_path_obj.stat().st_size
                    size_kb = size / 1024
                    print(f"   ✅ {format_name.upper():8s}: {file_path_obj.name}")
                    print(f"      Size: {size_kb:.1f} KB")
                    print(f"      Path: {file_path_obj}")
                else:
                    print(f"   ❌ {format_name.upper():8s}: File not found: {file_path}")
            print()
            
            print("=" * 80)
            print("FILES READY FOR INSPECTION")
            print("=" * 80)
            print()
            print(f"📁 Location: {export_dir}")
            print()
            print("Files:")
            for format_name, file_path in exported_files.items():
                if Path(file_path).exists():
                    print(f"   • {Path(file_path).name}")
            print()
            print(f"✅ All export formats saved!")
            print(f"   Open: {export_dir}")
        else:
            print("❌ No files exported")
            
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_exports()

