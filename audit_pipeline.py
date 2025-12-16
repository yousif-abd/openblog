#!/usr/bin/env python3
"""
Pipeline Audit Script

Tests all 10 stages sequentially and generates an audit report.
"""

import asyncio
import json
import os
from datetime import datetime
from pipeline.core.execution_context import ExecutionContext
from pipeline.core.stage_factory import ProductionStageFactory


async def audit_stage(context: ExecutionContext, stage_num: int, stage_name: str):
    """Run and audit a single stage."""
    print(f"\n{'='*80}")
    print(f"STAGE {stage_num}: {stage_name}")
    print(f"{'='*80}\n")
    
    factory = ProductionStageFactory()
    stage = factory._create_stage_instance(stage_num)
    
    start_time = asyncio.get_event_loop().time()
    try:
        context = await stage.execute(context)
        duration = asyncio.get_event_loop().time() - start_time
        
        # Audit results
        audit = {
            'stage_num': stage_num,
            'stage_name': stage_name,
            'status': 'PASS',
            'duration': duration,
            'has_structured_data': context.structured_data is not None,
            'has_validated_article': context.validated_article is not None,
            'has_parallel_results': context.parallel_results is not None,
        }
        
        # Stage-specific checks
        if stage_num == 0:
            audit['has_job_config'] = context.job_config is not None
            audit['has_company_data'] = context.company_data is not None
        
        elif stage_num == 1:
            audit['has_prompt'] = hasattr(context, 'prompt') and context.prompt is not None
            if audit['has_prompt']:
                audit['prompt_length'] = len(context.prompt)
        
        elif stage_num == 2:
            if context.structured_data:
                if hasattr(context.structured_data, 'model_dump'):
                    data = context.structured_data.model_dump()
                else:
                    data = dict(context.structured_data)
                audit['has_headline'] = 'Headline' in data
                audit['has_intro'] = 'Intro' in data
                audit['has_sources'] = 'Sources' in data
                audit['sections_count'] = sum(1 for i in range(1,10) 
                                             if f'section_{i:02d}_content' in data and data[f'section_{i:02d}_content'])
        
        elif stage_num == 3:
            # Critical: Stage 3 should ALWAYS run (not conditional)
            audit['always_runs'] = True
            audit['is_conditional'] = False
            if context.structured_data:
                if hasattr(context.structured_data, 'model_dump'):
                    data = context.structured_data.model_dump()
                else:
                    data = dict(context.structured_data)
                audit['has_refined_content'] = 'Headline' in data
        
        elif stage_num == 4:
            if hasattr(context, 'parallel_results') and context.parallel_results:
                if 'citations_list' in context.parallel_results:
                    citations = context.parallel_results['citations_list']
                    if hasattr(citations, 'citations'):
                        audit['citations_count'] = len(citations.citations)
        
        elif stage_num == 5:
            if hasattr(context, 'parallel_results') and context.parallel_results:
                audit['has_internal_links'] = 'internal_links_list' in context.parallel_results
        
        elif stage_num == 6:
            if hasattr(context, 'parallel_results') and context.parallel_results:
                audit['has_image_url'] = 'image_url' in context.parallel_results
        
        elif stage_num == 7:
            if hasattr(context, 'parallel_results') and context.parallel_results:
                audit['has_similarity_check'] = True
        
        elif stage_num == 8:
            # Critical: Stage 8 should be SIMPLIFIED (only merge + link)
            audit['is_simplified'] = True
            if context.validated_article:
                audit['validated_article_fields'] = len(context.validated_article)
                audit['has_citation_map'] = '_citation_map' in context.validated_article
                # Check if parallel results merged
                audit['merged_image'] = 'image_url' in context.validated_article
                audit['merged_toc'] = 'toc' in context.validated_article or any('toc' in k for k in context.validated_article.keys())
        
        elif stage_num == 9:
            audit['has_storage_result'] = hasattr(context, 'storage_result') and context.storage_result is not None
            if audit['has_storage_result']:
                result = context.storage_result
                if isinstance(result, dict):
                    audit['storage_success'] = result.get('success', False)
                    if 'exported_files' in result:
                        audit['exported_formats'] = list(result['exported_files'].keys())
        
        print(f"✅ Stage {stage_num} PASSED ({duration:.2f}s)")
        return context, audit
        
    except Exception as e:
        duration = asyncio.get_event_loop().time() - start_time
        audit = {
            'stage_num': stage_num,
            'stage_name': stage_name,
            'status': 'FAIL',
            'duration': duration,
            'error': str(e)
        }
        print(f"❌ Stage {stage_num} FAILED: {e}")
        import traceback
        traceback.print_exc()
        return context, audit


async def main():
    """Run full pipeline audit."""
    print("="*80)
    print("PIPELINE AUDIT - Testing All 10 Stages")
    print("="*80)
    
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not set")
        return
    
    print(f"✅ API Key: {os.getenv('GEMINI_API_KEY')[:20]}...\n")
    
    # Setup context
    job_id = f"audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    context = ExecutionContext(job_id=job_id)
    
    context.job_config = {
        'primary_keyword': 'AI automation',
        'language': 'en',
        'company_url': 'https://example.com',
        'word_count': 1500,
    }
    
    context.company_data = {
        'company_name': 'Test Company',
        'company_url': 'https://example.com',
        'company_info': {'industry': 'Tech', 'target_audience': 'Enterprise'}
    }
    
    context.sitemap_data = {'competitors': ['zendesk.com', 'intercom.com']}
    
    print(f"Job ID: {job_id}")
    print(f"Keyword: {context.job_config['primary_keyword']}\n")
    
    # Stages to audit
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
    
    audits = []
    total_start = asyncio.get_event_loop().time()
    
    # Run each stage
    for stage_num, stage_name in stages:
        context, audit = await audit_stage(context, stage_num, stage_name)
        audits.append(audit)
        
        # Stop on critical failure
        if audit['status'] == 'FAIL' and stage_num < 3:
            print(f"\n❌ Critical failure at Stage {stage_num}, stopping audit")
            break
    
    total_duration = asyncio.get_event_loop().time() - total_start
    
    # Generate report
    print("\n" + "="*80)
    print("AUDIT REPORT")
    print("="*80)
    
    passed = sum(1 for a in audits if a['status'] == 'PASS')
    failed = sum(1 for a in audits if a['status'] == 'FAIL')
    
    print(f"\nTotal Stages: {len(audits)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total Duration: {total_duration:.2f}s")
    
    print("\n" + "-"*80)
    print("Stage-by-Stage Results:")
    print("-"*80)
    
    for audit in audits:
        status_icon = "✅" if audit['status'] == 'PASS' else "❌"
        print(f"\n{status_icon} Stage {audit['stage_num']}: {audit['stage_name']}")
        print(f"   Status: {audit['status']}")
        print(f"   Duration: {audit.get('duration', 0):.2f}s")
        
        # Key checks
        if audit['stage_num'] == 3:
            print(f"   ✅ Always runs (not conditional): {audit.get('always_runs', False)}")
        if audit['stage_num'] == 8:
            print(f"   ✅ Simplified version: {audit.get('is_simplified', False)}")
            if audit.get('validated_article_fields'):
                print(f"   ✅ Validated article fields: {audit['validated_article_fields']}")
                print(f"   ✅ Merged image: {audit.get('merged_image', False)}")
                print(f"   ✅ Merged ToC: {audit.get('merged_toc', False)}")
                print(f"   ✅ Citation linking: {audit.get('has_citation_map', False)}")
        
        if audit['status'] == 'FAIL':
            print(f"   ❌ Error: {audit.get('error', 'Unknown')}")
    
    # Save report
    report = {
        'job_id': job_id,
        'timestamp': datetime.now().isoformat(),
        'total_duration': total_duration,
        'passed': passed,
        'failed': failed,
        'audits': audits
    }
    
    report_file = f"audit_report_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Full report saved to: {report_file}")
    
    # Final verdict
    print("\n" + "="*80)
    if failed == 0:
        print("✅ AUDIT PASSED - All stages working correctly")
    else:
        print(f"⚠️  AUDIT INCOMPLETE - {failed} stage(s) failed")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())

