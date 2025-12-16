"""
Test All Export Formats

Generates a test article and exports in all formats:
- HTML
- Markdown
- PDF
- JSON
- CSV
- XLSX

Saves to ~/Downloads/openblog_exports/ for inspection.
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.core.stage_factory import ProductionStageFactory

async def test_all_exports():
    """Test all export formats."""
    print("=" * 80)
    print("TESTING ALL EXPORT FORMATS")
    print("=" * 80)
    print()
    
    # Create output directory in Downloads
    downloads_dir = Path.home() / "Downloads"
    export_dir = downloads_dir / "openblog_exports" / datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Export directory: {export_dir}")
    print()
    
    # Test configuration
    job_config = {
        "primary_keyword": "AI code generation tools",
        "company_url": "https://scaile.tech",
        "company_name": "Scaile",
        "word_count": 1500,  # Shorter for faster testing
        "language": "en",
        "country": "US",
        "tone": "professional",
        "export_formats": ["html", "markdown", "pdf", "json", "csv", "xlsx"],  # All formats
        "sitemap_urls": [
            "https://scaile.tech/blog/ai-visibility-engine",
            "https://scaile.tech/blog/enterprise-ai-solutions",
        ],
    }
    
    job_id = f"test-exports-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print(f"📋 Job ID: {job_id}")
    print(f"📝 Keyword: {job_config['primary_keyword']}")
    print(f"🏢 Company: {job_config['company_name']}")
    print(f"📦 Export formats: {', '.join(job_config['export_formats'])}")
    print()
    
    try:
        # Create workflow engine
        print("🔧 Initializing workflow engine...")
        factory = ProductionStageFactory()
        stages = factory.create_all_stages()
        
        engine = WorkflowEngine()
        engine.register_stages(stages)
        
        print(f"✅ Registered {len(stages)} stages")
        print()
        
        # Execute pipeline
        print("🚀 Starting pipeline execution...")
        print("   (This will take ~2-3 minutes for full generation)")
        print()
        
        context = await engine.execute(
            job_id=job_id,
            job_config=job_config,
        )
        
        print()
        print("=" * 80)
        print("EXPORT RESULTS")
        print("=" * 80)
        print()
        
        # Check exported files
        if hasattr(context, 'storage_result') and context.storage_result:
            exported_files = context.storage_result.get("exported_files", {})
            
            if exported_files:
                print(f"✅ Exported {len(exported_files)} format(s):")
                print()
                
                for format_name, file_path in exported_files.items():
                    file_path_obj = Path(file_path)
                    if file_path_obj.exists():
                        size = file_path_obj.stat().st_size
                        size_kb = size / 1024
                        print(f"   ✅ {format_name.upper():8s}: {file_path}")
                        print(f"      Size: {size_kb:.1f} KB")
                    else:
                        print(f"   ❌ {format_name.upper():8s}: File not found: {file_path}")
                print()
                
                # Copy files to Downloads folder
                print("📋 Copying files to Downloads folder...")
                copied_files = []
                
                for format_name, file_path in exported_files.items():
                    source = Path(file_path)
                    if source.exists():
                        # Get filename from source
                        filename = source.name
                        # Create new filename with format suffix
                        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                        ext = source.suffix
                        dest = export_dir / f"{base_name}.{format_name}{ext}"
                        
                        # Copy file
                        import shutil
                        shutil.copy2(source, dest)
                        copied_files.append((format_name, dest))
                        print(f"   ✅ Copied {format_name}: {dest.name}")
                
                print()
                print("=" * 80)
                print("FILES READY FOR INSPECTION")
                print("=" * 80)
                print()
                print(f"📁 Location: {export_dir}")
                print()
                print("Files:")
                for format_name, file_path in copied_files:
                    print(f"   • {file_path.name}")
                print()
                print("✅ All export formats saved to Downloads folder!")
                print(f"   Open: {export_dir}")
            else:
                print("⚠️  No exported files found in storage_result")
                print("   Checking if files were saved to output directory...")
                
                # Check output directory
                output_dir = Path("output") / job_id
                if output_dir.exists():
                    files = list(output_dir.glob("*"))
                    if files:
                        print(f"   Found {len(files)} file(s) in {output_dir}:")
                        for f in files:
                            print(f"      • {f.name}")
                        
                        # Copy to Downloads
                        import shutil
                        for f in files:
                            dest = export_dir / f.name
                            shutil.copy2(f, dest)
                        print(f"\n   ✅ Copied to: {export_dir}")
                    else:
                        print("   No files found in output directory")
        else:
            print("❌ No storage_result found")
        
        return context
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(test_all_exports())

