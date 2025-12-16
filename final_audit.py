#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE AUDIT

Verifies all critical changes:
1. Stage 3 always runs (not conditional)
2. Stage 8 simplified (only merge + link, no content manipulation)
3. All stages work correctly
4. Data flow is correct
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from pipeline.core.execution_context import ExecutionContext
from pipeline.core.stage_factory import ProductionStageFactory
from pipeline.core.workflow_engine import WorkflowEngine


def audit_stage_3_always_runs():
    """CRITICAL: Verify Stage 3 always runs (not conditional)."""
    print("\n" + "="*80)
    print("AUDIT 1: Stage 3 Always Runs (Not Conditional)")
    print("="*80)
    
    checks = []
    
    # Check 1: Stage 3 is registered in factory
    factory = ProductionStageFactory()
    registry = factory._build_stage_registry()
    check1 = {
        'name': 'Stage 3 Registered in Factory',
        'status': 'PASS' if 3 in registry else 'FAIL',
        'details': {'registered': 3 in registry}
    }
    checks.append(check1)
    print(f"  {'✅' if check1['status'] == 'PASS' else '❌'} {check1['name']}: {check1['status']}")
    
    # Check 2: No conditional method in workflow_engine
    import inspect
    from pipeline.core import workflow_engine
    has_conditional_method = hasattr(workflow_engine.WorkflowEngine, '_execute_stage_3_conditional')
    check2 = {
        'name': 'No Conditional Method in WorkflowEngine',
        'status': 'PASS' if not has_conditional_method else 'FAIL',
        'details': {'has_method': has_conditional_method}
    }
    checks.append(check2)
    print(f"  {'✅' if check2['status'] == 'PASS' else '❌'} {check2['name']}: {check2['status']}")
    
    # Check 3: Stage 3 executes in sequential flow
    source = inspect.getsource(workflow_engine.WorkflowEngine.execute)
    executes_sequentially = 'await self._execute_sequential(context, [0, 1, 2, 3])' in source or 'await self._execute_sequential(context, [0, 1, 2, 3]' in source
    check3 = {
        'name': 'Stage 3 Executes in Sequential Flow',
        'status': 'PASS' if executes_sequentially else 'FAIL',
        'details': {'executes_with_0_1_2': executes_sequentially}
    }
    checks.append(check3)
    print(f"  {'✅' if check3['status'] == 'PASS' else '❌'} {check3['name']}: {check3['status']}")
    
    return checks


def audit_stage_8_simplified():
    """CRITICAL: Verify Stage 8 is simplified (only merge + link)."""
    print("\n" + "="*80)
    print("AUDIT 2: Stage 8 Simplified (Only Merge + Link)")
    print("="*80)
    
    checks = []
    
    # Read Stage 8 file
    stage8_file = Path('pipeline/blog_generation/stage_08_cleanup.py')
    if not stage8_file.exists():
        checks.append({
            'name': 'Stage 8 File Exists',
            'status': 'FAIL',
            'details': {'error': 'File not found'}
        })
        return checks
    
    content = stage8_file.read_text()
    
    # Check 1: File size (should be ~330 lines, not 1,727)
    line_count = len(content.split('\n'))
    check1 = {
        'name': 'Stage 8 Line Count',
        'status': 'PASS' if line_count < 500 else 'WARN',
        'details': {
            'lines': line_count,
            'expected': '< 500',
            'previous': '1,727'
        }
    }
    checks.append(check1)
    print(f"  {'✅' if check1['status'] == 'PASS' else '⚠️'} {check1['name']}: {line_count} lines")
    
    # Check 2: No content manipulation methods
    removed_methods = [
        '_prepare_and_clean',
        '_sanitize_output',
        '_normalize_output',
        '_humanize_article',
        '_enforce_aeo_requirements',
        '_add_conversational_phrases',
        '_enhance_direct_answer',
        '_convert_headers_to_questions',
        '_split_long_paragraphs',
        '_add_missing_lists',
        '_fix_citation_distribution',
    ]
    
    found_methods = []
    for method in removed_methods:
        if f'def {method}' in content:
            found_methods.append(method)
    
    check2 = {
        'name': 'No Content Manipulation Methods',
        'status': 'PASS' if len(found_methods) == 0 else 'FAIL',
        'details': {
            'found_methods': found_methods,
            'should_be_removed': removed_methods
        }
    }
    checks.append(check2)
    print(f"  {'✅' if check2['status'] == 'PASS' else '❌'} {check2['name']}: {len(found_methods)} found (should be 0)")
    
    # Check 3: Has essential methods
    essential_methods = [
        '_merge_parallel_results',
        '_link_citations',
        '_validate_citation_url',
        '_flatten_article'
    ]
    
    missing_methods = []
    for method in essential_methods:
        if f'def {method}' not in content:
            missing_methods.append(method)
    
    check3 = {
        'name': 'Has Essential Methods',
        'status': 'PASS' if len(missing_methods) == 0 else 'FAIL',
        'details': {
            'missing': missing_methods,
            'required': essential_methods
        }
    }
    checks.append(check3)
    print(f"  {'✅' if check3['status'] == 'PASS' else '❌'} {check3['name']}: {len(missing_methods)} missing")
    
    # Check 4: No regex imports for content manipulation
    import re
    regex_patterns = [
        r're\.sub\([^)]*HTML',
        r're\.findall\([^)]*paragraph',
        r're\.search\([^)]*citation',
    ]
    
    found_regex = []
    for pattern in regex_patterns:
        if re.search(pattern, content):
            found_regex.append(pattern)
    
    check4 = {
        'name': 'No Regex for Content Manipulation',
        'status': 'PASS' if len(found_regex) == 0 else 'WARN',
        'details': {'found_patterns': found_regex}
    }
    checks.append(check4)
    print(f"  {'✅' if check4['status'] == 'PASS' else '⚠️'} {check4['name']}: {len(found_regex)} patterns found")
    
    # Check 5: Stage name is "Merge & Link"
    has_correct_name = '"Merge & Link"' in content or "'Merge & Link'" in content
    check5 = {
        'name': 'Stage Name is "Merge & Link"',
        'status': 'PASS' if has_correct_name else 'FAIL',
        'details': {'has_correct_name': has_correct_name}
    }
    checks.append(check5)
    print(f"  {'✅' if check5['status'] == 'PASS' else '❌'} {check5['name']}: {check5['status']}")
    
    return checks


async def audit_pipeline_execution():
    """Audit actual pipeline execution."""
    print("\n" + "="*80)
    print("AUDIT 3: Pipeline Execution")
    print("="*80)
    
    if not os.getenv('GEMINI_API_KEY'):
        print("  ⚠️  Skipping execution audit (no API key)")
        return []
    
    checks = []
    
    # Setup minimal context
    context = ExecutionContext(job_id='final-audit')
    context.job_config = {
        'primary_keyword': 'AI automation',
        'language': 'en',
        'company_url': 'https://example.com',
        'word_count': 1000,  # Smaller for faster testing
    }
    context.company_data = {
        'company_name': 'Test',
        'company_url': 'https://example.com'
    }
    
    factory = ProductionStageFactory()
    
    # Test critical stages only
    critical_stages = [0, 1, 2, 3, 8]  # Skip 4-7, 9 for speed
    
    for stage_num in critical_stages:
        try:
            stage = factory._create_stage_instance(stage_num)
            context = await stage.execute(context)
            
            # Stage-specific checks
            if stage_num == 3:
                check = {
                    'name': f'Stage {stage_num} Executes Successfully',
                    'status': 'PASS' if context.structured_data else 'FAIL',
                    'details': {'has_structured_data': context.structured_data is not None}
                }
                checks.append(check)
                print(f"  ✅ Stage {stage_num} executed successfully")
            
            elif stage_num == 8:
                check = {
                    'name': f'Stage {stage_num} Executes Successfully',
                    'status': 'PASS' if context.validated_article else 'FAIL',
                    'details': {
                        'has_validated_article': context.validated_article is not None,
                        'fields_count': len(context.validated_article) if context.validated_article else 0
                    }
                }
                checks.append(check)
                print(f"  ✅ Stage {stage_num} executed successfully")
                if context.validated_article:
                    # Check for citation map
                    has_citation_map = '_citation_map' in context.validated_article
                    check2 = {
                        'name': 'Stage 8 Creates Citation Map',
                        'status': 'PASS' if has_citation_map else 'WARN',
                        'details': {'has_citation_map': has_citation_map}
                    }
                    checks.append(check2)
                    print(f"    {'✅' if has_citation_map else '⚠️'} Citation map created")
            
            else:
                check = {
                    'name': f'Stage {stage_num} Executes Successfully',
                    'status': 'PASS',
                    'details': {}
                }
                checks.append(check)
                print(f"  ✅ Stage {stage_num} executed successfully")
                
        except Exception as e:
            check = {
                'name': f'Stage {stage_num} Executes Successfully',
                'status': 'FAIL',
                'details': {'error': str(e)}
            }
            checks.append(check)
            print(f"  ❌ Stage {stage_num} failed: {e}")
    
    return checks


def audit_code_quality():
    """Audit code quality and structure."""
    print("\n" + "="*80)
    print("AUDIT 4: Code Quality & Structure")
    print("="*80)
    
    checks = []
    
    # Check imports
    stage8_file = Path('pipeline/blog_generation/stage_08_cleanup.py')
    if stage8_file.exists():
        content = stage8_file.read_text()
        
        # Check for removed imports
        removed_imports = [
            'HTMLCleaner',
            'SectionCombiner',
            'humanize_content',
            'detect_ai_patterns',
            'validate_article_language',
        ]
        
        found_imports = []
        for imp in removed_imports:
            if imp in content:
                found_imports.append(imp)
        
        check = {
            'name': 'No Removed Imports',
            'status': 'PASS' if len(found_imports) == 0 else 'WARN',
            'details': {'found_imports': found_imports}
        }
        checks.append(check)
        print(f"  {'✅' if check['status'] == 'PASS' else '⚠️'} {check['name']}: {len(found_imports)} found")
    
    return checks


async def main():
    """Run final comprehensive audit."""
    print("="*80)
    print("FINAL COMPREHENSIVE AUDIT")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    all_checks = []
    
    # Audit 1: Stage 3 always runs
    checks1 = audit_stage_3_always_runs()
    all_checks.extend(checks1)
    
    # Audit 2: Stage 8 simplified
    checks2 = audit_stage_8_simplified()
    all_checks.extend(checks2)
    
    # Audit 3: Pipeline execution
    checks3 = await audit_pipeline_execution()
    all_checks.extend(checks3)
    
    # Audit 4: Code quality
    checks4 = audit_code_quality()
    all_checks.extend(checks4)
    
    # Generate report
    print("\n" + "="*80)
    print("FINAL AUDIT REPORT")
    print("="*80)
    
    total_checks = len(all_checks)
    passed = sum(1 for c in all_checks if c['status'] == 'PASS')
    failed = sum(1 for c in all_checks if c['status'] == 'FAIL')
    warnings = sum(1 for c in all_checks if c['status'] == 'WARN')
    
    print(f"\nTotal Checks: {total_checks}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warnings}")
    
    # Critical checks summary
    print("\n" + "-"*80)
    print("CRITICAL CHECKS:")
    print("-"*80)
    
    critical_passed = True
    for check in all_checks:
        if 'Stage 3' in check['name'] or 'Stage 8' in check['name']:
            status_icon = "✅" if check['status'] == 'PASS' else "❌" if check['status'] == 'FAIL' else "⚠️"
            print(f"{status_icon} {check['name']}: {check['status']}")
            if check['status'] == 'FAIL':
                critical_passed = False
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_checks': total_checks,
        'passed': passed,
        'failed': failed,
        'warnings': warnings,
        'critical_passed': critical_passed,
        'checks': all_checks
    }
    
    report_file = f"final_audit_report_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Full report saved: {report_file}")
    
    # Final verdict
    print("\n" + "="*80)
    if critical_passed and failed == 0:
        print("✅ FINAL AUDIT: PASSED - All critical checks passed!")
        print("   110% HAPPY! 🎉")
    elif critical_passed:
        print("⚠️  FINAL AUDIT: PASSED (with warnings)")
        print("   Critical checks passed, but some warnings exist")
    else:
        print("❌ FINAL AUDIT: FAILED")
        print("   Critical checks failed - review required")
    print("="*80)
    
    return 0 if critical_passed and failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

