#!/usr/bin/env python3
"""
Interactive Pipeline Test Script

Runs the pipeline stage-by-stage, pausing after each stage for inspection.
Only proceeds to next stage after user verification.

Usage:
    python3 test_pipeline_interactive.py
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from pipeline.core.execution_context import ExecutionContext
from pipeline.core.stage_factory import ProductionStageFactory
from pipeline.core.workflow_engine import WorkflowEngine


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    print("\n" + char * 80)
    print(f"  {text}")
    print(char * 80 + "\n")


def print_section(text: str):
    """Print a section header."""
    print(f"\n{'─' * 80}")
    print(f"  {text}")
    print(f"{'─' * 80}\n")


def print_context_summary(context: ExecutionContext, stage_num: int):
    """Print a summary of context after a stage."""
    print_section(f"Context Summary After Stage {stage_num}")
    
    # Key fields to show
    fields_to_show = {
        "job_id": context.job_id,
        "has_structured_data": context.structured_data is not None,
        "has_validated_article": context.validated_article is not None,
        "has_parallel_results": context.parallel_results is not None,
        "has_final_article": hasattr(context, 'final_article') and context.final_article is not None,
        "has_storage_result": hasattr(context, 'storage_result') and context.storage_result is not None,
    }
    
    for key, value in fields_to_show.items():
        print(f"  {key:30s}: {value}")
    
    # Show execution times
    if hasattr(context, 'execution_times') and context.execution_times:
        print(f"\n  Execution Times:")
        for stage, duration in context.execution_times.items():
            print(f"    {stage:20s}: {duration:.2f}s")
    
    # Show errors if any
    if hasattr(context, 'errors') and context.errors:
        print(f"\n  ⚠️  Errors:")
        for stage, error in context.errors.items():
            print(f"    {stage}: {error}")


def print_structured_data_preview(context: ExecutionContext):
    """Print a preview of structured_data."""
    if not context.structured_data:
        print("  No structured_data available")
        return
    
    print_section("Structured Data Preview")
    
    # Convert to dict if needed
    if hasattr(context.structured_data, 'model_dump'):
        data = context.structured_data.model_dump()
    elif hasattr(context.structured_data, 'dict'):
        data = context.structured_data.dict()
    else:
        data = dict(context.structured_data)
    
    # Show key fields
    key_fields = [
        'Headline', 'Subtitle', 'Meta_Title', 'Meta_Description',
        'Intro', 'Direct_Answer', 'Key_Takeaways'
    ]
    
    for field in key_fields:
        if field in data:
            value = str(data[field])[:200]  # First 200 chars
            if len(str(data[field])) > 200:
                value += "..."
            print(f"  {field:25s}: {value}")
    
    # Count sections
    section_count = sum(1 for i in range(1, 10) 
                        if f'section_{i:02d}_content' in data and data[f'section_{i:02d}_content'])
    print(f"\n  Sections with content: {section_count}")
    
    # Show Sources if available
    if 'Sources' in data and data['Sources']:
        sources_preview = str(data['Sources'])[:300]
        if len(str(data['Sources'])) > 300:
            sources_preview += "..."
        print(f"\n  Sources preview:\n    {sources_preview}")


def print_validated_article_preview(context: ExecutionContext):
    """Print a preview of validated_article."""
    if not context.validated_article:
        print("  No validated_article available")
        return
    
    print_section("Validated Article Preview")
    
    article = context.validated_article
    
    # Show key fields
    key_fields = [
        'Headline', 'Subtitle', 'Meta_Title', 'Meta_Description',
        'Intro', 'Direct_Answer', 'Key_Takeaways'
    ]
    
    for field in key_fields:
        if field in article:
            value = str(article[field])[:200]
            if len(str(article[field])) > 200:
                value += "..."
            print(f"  {field:25s}: {value}")
    
    # Count sections
    section_count = sum(1 for i in range(1, 10) 
                        if f'section_{i:02d}_content' in article and article[f'section_{i:02d}_content'])
    print(f"\n  Sections with content: {section_count}")
    
    # Show field count
    print(f"  Total fields: {len(article)}")


def print_parallel_results_preview(context: ExecutionContext):
    """Print a preview of parallel_results."""
    if not context.parallel_results:
        print("  No parallel_results available")
        return
    
    print_section("Parallel Results Preview")
    
    results = context.parallel_results
    
    print(f"  Keys in parallel_results: {list(results.keys())}")
    
    # Show specific results
    if 'image_url' in results:
        print(f"\n  Image URL: {results['image_url']}")
    if 'toc_dict' in results:
        toc = results['toc_dict']
        print(f"\n  ToC entries: {len(toc) if isinstance(toc, dict) else 'N/A'}")
    if 'faq_items' in results:
        faq = results['faq_items']
        if hasattr(faq, 'to_dict_list'):
            print(f"\n  FAQ items: {len(faq.to_dict_list())}")
        elif isinstance(faq, list):
            print(f"\n  FAQ items: {len(faq)}")
    if 'paa_items' in results:
        paa = results['paa_items']
        if hasattr(paa, 'to_dict_list'):
            print(f"\n  PAA items: {len(paa.to_dict_list())}")
        elif isinstance(paa, list):
            print(f"\n  PAA items: {len(paa)}")


def print_storage_result_preview(context: ExecutionContext):
    """Print a preview of storage_result."""
    if not hasattr(context, 'storage_result') or not context.storage_result:
        print("  No storage_result available")
        return
    
    print_section("Storage Result Preview")
    
    result = context.storage_result
    
    if isinstance(result, dict):
        print(f"  Success: {result.get('success', 'N/A')}")
        if 'exported_files' in result:
            files = result['exported_files']
            print(f"\n  Exported files:")
            for fmt, path in files.items():
                print(f"    {fmt:10s}: {path}")
        if 'error' in result:
            print(f"\n  ⚠️  Error: {result['error']}")
    else:
        print(f"  Result: {result}")


def wait_for_user(stage_name: str, stage_num: int) -> str:
    """Wait for user input before proceeding."""
    print(f"\n{'=' * 80}")
    print(f"  Stage {stage_num}: {stage_name} - COMPLETE")
    print(f"{'=' * 80}\n")
    
    while True:
        response = input(
            "Options:\n"
            "  [Enter] - Continue to next stage\n"
            "  [i]     - Inspect full context data\n"
            "  [s]     - Skip remaining stages\n"
            "  [q]     - Quit test\n"
            "  [r]     - Retry this stage\n"
            "\nYour choice: "
        ).strip().lower()
        
        if response == '':
            return 'continue'
        elif response == 'i':
            return 'inspect'
        elif response == 's':
            return 'skip'
        elif response == 'q':
            return 'quit'
        elif response == 'r':
            return 'retry'
        else:
            print("Invalid choice. Please try again.\n")


def inspect_full_context(context: ExecutionContext):
    """Show full context data."""
    print_header("Full Context Inspection")
    
    print("Context attributes:")
    for attr in dir(context):
        if not attr.startswith('_'):
            value = getattr(context, attr)
            if not callable(value):
                if isinstance(value, (str, int, float, bool, type(None))):
                    print(f"  {attr:30s}: {value}")
                elif isinstance(value, dict):
                    print(f"  {attr:30s}: dict with {len(value)} keys")
                elif isinstance(value, list):
                    print(f"  {attr:30s}: list with {len(value)} items")
                else:
                    print(f"  {attr:30s}: {type(value).__name__}")
    
    # Ask if user wants to see specific data
    print("\n")
    choice = input("View specific data? [structured_data/s/validated_article/v/parallel_results/p/storage_result/st] or [Enter] to continue: ").strip().lower()
    
    if choice in ['structured_data', 's']:
        if context.structured_data:
            print("\n" + json.dumps(
                context.structured_data.model_dump() if hasattr(context.structured_data, 'model_dump')
                else context.structured_data.dict() if hasattr(context.structured_data, 'dict')
                else dict(context.structured_data),
                indent=2,
                default=str
            )[:5000])  # Limit to 5000 chars
        else:
            print("No structured_data available")
    
    elif choice in ['validated_article', 'v']:
        if context.validated_article:
            print("\n" + json.dumps(context.validated_article, indent=2, default=str)[:5000])
        else:
            print("No validated_article available")
    
    elif choice in ['parallel_results', 'p']:
        if context.parallel_results:
            print("\n" + json.dumps(context.parallel_results, indent=2, default=str)[:5000])
        else:
            print("No parallel_results available")
    
    elif choice in ['storage_result', 'st']:
        if hasattr(context, 'storage_result') and context.storage_result:
            print("\n" + json.dumps(context.storage_result, indent=2, default=str)[:5000])
        else:
            print("No storage_result available")
    
    input("\nPress Enter to continue...")


async def run_stage_interactive(
    context: ExecutionContext,
    stage_num: int,
    stage_name: str
) -> Tuple[ExecutionContext, str]:
    """Run a single stage and wait for user verification."""
    print_header(f"Stage {stage_num}: {stage_name}", "=")
    
    try:
        # Get the stage from factory
        factory = ProductionStageFactory()
        stage = factory._create_stage_instance(stage_num)
        
        print(f"Executing {stage_name}...\n")
        
        # Execute stage
        start_time = asyncio.get_event_loop().time()
        context = await stage.execute(context)
        duration = asyncio.get_event_loop().time() - start_time
        
        print(f"\n✅ Stage {stage_num} completed in {duration:.2f}s")
        
        # Show preview based on stage
        if stage_num == 2:  # After Gemini Call
            print_structured_data_preview(context)
        elif stage_num == 3:  # After Quality Refinement
            print_structured_data_preview(context)
        elif stage_num == 8:  # After Merge & Link
            print_validated_article_preview(context)
            print_parallel_results_preview(context)
        elif stage_num == 9:  # After Storage
            print_storage_result_preview(context)
        
        # Always show context summary
        print_context_summary(context, stage_num)
        
        # Wait for user
        action = wait_for_user(stage_name, stage_num)
        
        return context, action
        
    except Exception as e:
        print(f"\n❌ Stage {stage_num} failed: {e}")
        import traceback
        traceback.print_exc()
        
        action = input("\nContinue anyway? [y/n]: ").strip().lower()
        if action == 'y':
            return context, 'continue'
        else:
            return context, 'quit'


async def main():
    """Main test function."""
    print_header("Interactive Pipeline Test", "=")
    print("This script runs the pipeline stage-by-stage, pausing after each")
    print("stage for inspection and verification.\n")
    
    # Check environment
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ ERROR: GEMINI_API_KEY environment variable not set")
        print("Please set it in your .env.local file or export it:")
        print("  export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)
    
    print(f"✅ GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')[:20]}...")
    print()
    
    # Create execution context
    job_id = f"interactive-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    context = ExecutionContext(job_id=job_id)
    
    # Set minimal job config
    context.job_config = {
        "primary_keyword": "AI-powered customer service automation",
        "language": "en",
        "company_url": "https://example.com",
        "content_generation_instruction": "Write a comprehensive guide about AI-powered customer service automation with real examples and statistics",
        "word_count": 2000,
    }
    
    # Set minimal company data
    context.company_data = {
        "company_name": "Example Company",
        "company_url": "https://example.com",
        "company_info": {
            "industry": "Technology",
            "target_audience": "Enterprise customers",
            "description": "Leading provider of AI solutions"
        }
    }
    
    # Set sitemap data for citations
    context.sitemap_data = {
        "competitors": ["zendesk.com", "intercom.com", "salesforce.com"]
    }
    
    print(f"Job ID: {job_id}")
    print(f"Primary Keyword: {context.job_config['primary_keyword']}")
    print(f"Language: {context.job_config['language']}")
    print()
    
    input("Press Enter to start the pipeline...")
    
    # Define stages
    stages = [
        (0, "Data Fetch"),
        (1, "Prompt Build"),
        (2, "Content Generation (Gemini)"),
        (3, "Quality Refinement"),
        (4, "Citations Validation"),
        (5, "Internal Links"),
        (6, "Image Generation (parallel)"),
        (7, "Similarity Check (parallel)"),
        (8, "Merge & Link"),
        (9, "Storage & Export"),
    ]
    
    # Run stages sequentially (note: stages 6-7 normally run in parallel)
    for stage_num, stage_name in stages:
        context, action = await run_stage_interactive(
            context,
            stage_num,
            stage_name
        )
        
        if action == 'quit':
            print("\n❌ Test stopped by user")
            break
        elif action == 'skip':
            print(f"\n⏭️  Skipping remaining stages (after Stage {stage_num})")
            break
        elif action == 'inspect':
            inspect_full_context(context)
            # Ask again what to do
            action = wait_for_user(stage_name, stage_num)
            if action == 'quit':
                break
            elif action == 'skip':
                break
        elif action == 'retry':
            # Retry the same stage
            stage_num -= 1  # Will be incremented in next iteration
            continue
    
    # Final summary
    print_header("Test Complete", "=")
    print_context_summary(context, "FINAL")
    
    if context.validated_article:
        print(f"\n✅ Pipeline completed successfully!")
        print(f"   Validated article has {len(context.validated_article)} fields")
    else:
        print(f"\n⚠️  Pipeline did not complete fully")
        print(f"   No validated_article available")


if __name__ == "__main__":
    asyncio.run(main())

