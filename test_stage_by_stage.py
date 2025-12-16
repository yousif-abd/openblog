#!/usr/bin/env python3
"""
Manual Stage-by-Stage Test

Run each stage individually, inspect output, then proceed.
"""

import asyncio
import json
import os
from datetime import datetime
from pipeline.core.execution_context import ExecutionContext
from pipeline.core.stage_factory import ProductionStageFactory


async def run_stage(context: ExecutionContext, stage_num: int, stage_name: str):
    """Run a single stage and return context."""
    print(f"\n{'='*80}")
    print(f"STAGE {stage_num}: {stage_name}")
    print(f"{'='*80}\n")
    
    factory = ProductionStageFactory()
    stage = factory._create_stage_instance(stage_num)
    
    print(f"Executing {stage_name}...")
    start_time = asyncio.get_event_loop().time()
    context = await stage.execute(context)
    duration = asyncio.get_event_loop().time() - start_time
    
    print(f"\n✅ Completed in {duration:.2f}s")
    return context


def inspect_context(context: ExecutionContext, stage_num: int):
    """Inspect context after stage."""
    print(f"\n{'─'*80}")
    print(f"INSPECTION: After Stage {stage_num}")
    print(f"{'─'*80}\n")
    
    # Basic info
    print(f"Job ID: {context.job_id}")
    print(f"Has structured_data: {context.structured_data is not None}")
    print(f"Has validated_article: {context.validated_article is not None}")
    print(f"Has parallel_results: {context.parallel_results is not None}")
    
    # Execution times
    if hasattr(context, 'execution_times') and context.execution_times:
        print(f"\nExecution Times:")
        for stage, duration in context.execution_times.items():
            print(f"  {stage}: {duration:.2f}s")
    
    # Errors
    if hasattr(context, 'errors') and context.errors:
        print(f"\n⚠️  Errors:")
        for stage, error in context.errors.items():
            print(f"  {stage}: {error}")
    
    # Stage-specific inspection
    if stage_num == 2 and context.structured_data:
        print(f"\n📄 Structured Data Preview:")
        if hasattr(context.structured_data, 'model_dump'):
            data = context.structured_data.model_dump()
        else:
            data = dict(context.structured_data)
        
        for field in ['Headline', 'Subtitle', 'Intro']:
            if field in data:
                val = str(data[field])[:150]
                print(f"  {field}: {val}...")
        
        if 'Sources' in data:
            sources = str(data['Sources'])[:200]
            print(f"\n  Sources preview: {sources}...")
    
    if stage_num == 8 and context.validated_article:
        print(f"\n📄 Validated Article:")
        print(f"  Total fields: {len(context.validated_article)}")
        for field in ['Headline', 'Subtitle', 'Intro']:
            if field in context.validated_article:
                val = str(context.validated_article[field])[:150]
                print(f"  {field}: {val}...")
    
    if stage_num >= 6 and context.parallel_results:
        print(f"\n📄 Parallel Results:")
        print(f"  Keys: {list(context.parallel_results.keys())}")
        if 'image_url' in context.parallel_results:
            print(f"  Image URL: {context.parallel_results['image_url']}")
    
    print(f"\n{'─'*80}\n")


async def main():
    """Run stages one by one."""
    print("="*80)
    print("MANUAL PIPELINE TEST - Stage by Stage")
    print("="*80)
    
    # Check API key
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not set")
        return
    
    print(f"✅ API Key: {os.getenv('GEMINI_API_KEY')[:20]}...\n")
    
    # Setup context
    job_id = f"manual-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    context = ExecutionContext(job_id=job_id)
    
    context.job_config = {
        "primary_keyword": "AI customer service automation",
        "language": "en",
        "company_url": "https://example.com",
        "content_generation_instruction": "Write about AI customer service automation",
        "word_count": 2000,
    }
    
    context.company_data = {
        "company_name": "Test Company",
        "company_url": "https://example.com",
        "company_info": {"industry": "Tech", "target_audience": "Enterprise"}
    }
    
    context.sitemap_data = {"competitors": ["zendesk.com", "intercom.com"]}
    
    print(f"Job ID: {job_id}")
    print(f"Keyword: {context.job_config['primary_keyword']}\n")
    
    # Stages to run
    stages = [
        (0, "Data Fetch"),
        (1, "Prompt Build"),
        (2, "Content Generation"),
        (3, "Quality Refinement"),
        (4, "Citations Validation"),
        (5, "Internal Links"),
        (6, "Image Generation"),
        (7, "Similarity Check"),
        (8, "Merge & Link"),
        (9, "Storage & Export"),
    ]
    
    # Run each stage
    for stage_num, stage_name in stages:
        try:
            context = await run_stage(context, stage_num, stage_name)
            inspect_context(context, stage_num)
            
            # Stop here for manual inspection
            print("⏸️  PAUSED - Review output above")
            print("Press Enter to continue to next stage...")
            # In real manual run, user would press Enter here
            
        except Exception as e:
            print(f"\n❌ Stage {stage_num} FAILED: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

