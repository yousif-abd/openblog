#!/usr/bin/env python3
"""
ISAAC SECURITY V4.0 - 10-BLOG PARALLEL BATCH TEST
Complete pipeline test with comprehensive analysis
"""
import sys
import os
import json
import asyncio
import time
from datetime import datetime
from pathlib import Path

# Ensure API key is set (should be in environment)
if not os.environ.get('GEMINI_API_KEY'):
    print("❌ GEMINI_API_KEY not set in environment. Please set it first:")
    print("   export GEMINI_API_KEY='your-key-here'")
    sys.exit(1)

# Configure comprehensive logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_test_10_comprehensive.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.core.execution_context import ExecutionContext
from pipeline.blog_generation.stage_00_data_fetch import DataFetchStage
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
from pipeline.blog_generation.stage_02b_quality_refinement import QualityRefinementStage
from pipeline.blog_generation.stage_03_extraction import ExtractionStage
from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.blog_generation.stage_05_internal_links import InternalLinksStage
from pipeline.blog_generation.stage_06_toc import TableOfContentsStage
from pipeline.blog_generation.stage_07_metadata import MetadataStage
from pipeline.blog_generation.stage_08_faq_paa import FAQPAAStage
from pipeline.blog_generation.stage_09_image import ImageStage
from pipeline.blog_generation.stage_10_cleanup import CleanupStage
from pipeline.blog_generation.stage_11_storage import StorageStage

# Test configurations for 10 diverse cybersecurity blogs
BATCH_CONFIGS = [
    {
        "job_id": "batch-test-001-zero-trust",
        "primary_keyword": "zero trust security architecture",
        "company_name": "CyberGuard Solutions", 
        "company_url": "https://cyberguard.tech",
        "industry": "Enterprise Security",
        "content_instruction": "Write a comprehensive guide about implementing zero trust security architecture for enterprise networks"
    },
    {
        "job_id": "batch-test-002-siem-automation", 
        "primary_keyword": "SIEM automation and orchestration",
        "company_name": "SecureOps Technologies",
        "company_url": "https://secureops.io", 
        "industry": "Security Operations",
        "content_instruction": "Create an in-depth analysis of SIEM automation tools and orchestration platforms for SOC teams"
    },
    {
        "job_id": "batch-test-003-cloud-compliance",
        "primary_keyword": "cloud security compliance frameworks", 
        "company_name": "CloudSecure Partners",
        "company_url": "https://cloudsecure.com",
        "industry": "Cloud Security",
        "content_instruction": "Develop a detailed guide on cloud security compliance frameworks for regulated industries"
    },
    {
        "job_id": "batch-test-004-threat-intelligence",
        "primary_keyword": "threat intelligence and analysis",
        "company_name": "ThreatTracker Intelligence", 
        "company_url": "https://threattracker.ai",
        "industry": "Threat Intelligence",
        "content_instruction": "Write an expert guide on threat intelligence collection, analysis, and implementation strategies"
    },
    {
        "job_id": "batch-test-005-devsecops",
        "primary_keyword": "DevSecOps pipeline security",
        "company_name": "DevSec Innovations",
        "company_url": "https://devsec.tech", 
        "industry": "DevSecOps",
        "content_instruction": "Create a comprehensive guide on securing CI/CD pipelines with DevSecOps best practices"
    },
    {
        "job_id": "batch-test-006-incident-response",
        "primary_keyword": "cybersecurity incident response",
        "company_name": "Rapid Response Security",
        "company_url": "https://rapidresponse.security",
        "industry": "Incident Response", 
        "content_instruction": "Develop an expert guide on cybersecurity incident response planning and execution"
    },
    {
        "job_id": "batch-test-007-identity-management",
        "primary_keyword": "identity and access management",
        "company_name": "IdentityFirst Solutions",
        "company_url": "https://identityfirst.com",
        "industry": "Identity Management",
        "content_instruction": "Write a comprehensive guide on modern identity and access management strategies"
    },
    {
        "job_id": "batch-test-008-network-security",
        "primary_keyword": "network security monitoring",
        "company_name": "NetWatch Security",
        "company_url": "https://netwatch.security", 
        "industry": "Network Security",
        "content_instruction": "Create an in-depth analysis of network security monitoring tools and techniques"
    },
    {
        "job_id": "batch-test-009-vulnerability-management",
        "primary_keyword": "vulnerability assessment and management",
        "company_name": "VulnGuard Technologies", 
        "company_url": "https://vulnguard.tech",
        "industry": "Vulnerability Management",
        "content_instruction": "Develop a detailed guide on vulnerability assessment methodologies and management practices"
    },
    {
        "job_id": "batch-test-010-security-awareness",
        "primary_keyword": "security awareness training programs",
        "company_name": "AwareTech Solutions",
        "company_url": "https://awaretech.training",
        "industry": "Security Training", 
        "content_instruction": "Write a comprehensive guide on designing and implementing effective security awareness training programs"
    }
]

async def run_single_blog(config: dict) -> dict:
    """Run complete 13-stage pipeline for a single blog."""
    
    start_time = time.time()
    job_id = config["job_id"]
    
    logger.info(f"🚀 Starting blog generation: {job_id}")
    logger.info(f"   Keyword: {config['primary_keyword']}")
    logger.info(f"   Company: {config['company_name']}")
    
    try:
        # Create execution context
        context = ExecutionContext(job_id=job_id)
        
        # Set job configuration
        context.job_config = {
            "primary_keyword": config["primary_keyword"],
            "language": "en",
            "content_generation_instruction": config["content_instruction"],
            "company_url": config["company_url"],
            "batch_siblings": [
                {"title": f"Related Guide 1", "url": f"/magazine/guide-1", "description": "Related security guide"},
                {"title": f"Related Guide 2", "url": f"/magazine/guide-2", "description": "Another security guide"},
            ]
        }
        
        # Set company data
        context.company_data = {
            "company_name": config["company_name"],
            "company_url": config["company_url"],
            "company_info": {
                "industry": config["industry"],
                "target_audience": "Enterprise security teams",
                "description": f"Leading provider of {config['industry'].lower()} solutions"
            }
        }
        
        # Add sitemap data for citation validation
        context.sitemap_data = {
            "competitors": ["crowdstrike.com", "paloaltonetworks.com", "fortinet.com", "rapid7.com", "splunk.com"]
        }
        
        # Initialize all 13 stages
        stages = [
            DataFetchStage(),           # Stage 0
            PromptBuildStage(),         # Stage 1
            GeminiCallStage(),          # Stage 2
            QualityRefinementStage(),   # Stage 2b
            ExtractionStage(),          # Stage 3
            CitationsStage(),           # Stage 4
            InternalLinksStage(),       # Stage 5
            TableOfContentsStage(),     # Stage 6
            MetadataStage(),           # Stage 7
            FAQPAAStage(),             # Stage 8
            ImageStage(),              # Stage 9
            CleanupStage(),            # Stage 10
            StorageStage()             # Stage 11
        ]
        
        stage_results = {}
        
        # Execute all stages
        for i, stage in enumerate(stages):
            stage_start = time.time()
            stage_name = stage.__class__.__name__
            
            logger.info(f"   Stage {i:2d}: {stage_name}")
            
            try:
                context = await stage.execute(context)
                stage_time = time.time() - stage_start
                stage_results[f"stage_{i}_{stage_name}"] = {
                    "duration": round(stage_time, 2),
                    "status": "success"
                }
                logger.info(f"      ✅ Completed in {stage_time:.1f}s")
                
            except Exception as e:
                stage_time = time.time() - stage_start
                stage_results[f"stage_{i}_{stage_name}"] = {
                    "duration": round(stage_time, 2),
                    "status": "failed",
                    "error": str(e)
                }
                logger.error(f"      ❌ Failed in {stage_time:.1f}s: {e}")
                raise
        
        total_time = time.time() - start_time
        
        # Analyze final output
        analysis = {}
        if hasattr(context, 'final_html') and context.final_html:
            html = context.final_html
            analysis = {
                "word_count": len(html.split()),
                "list_count": html.count('<ul>') + html.count('<ol>'),
                "item_count": html.count('<li>'),
                "links_count": html.count('href="http'),
                "images_count": html.count('<img'),
                "file_size": len(html),
                "has_faqs": 'faq' in html.lower(),
                "has_toc": 'table of contents' in html.lower() or 'toc' in html.lower()
            }
            
            # Save output
            output_path = f"output/{job_id}/index.html"
            Path(f"output/{job_id}").mkdir(exist_ok=True, parents=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            analysis["output_path"] = output_path
            
        logger.info(f"✅ Blog completed: {job_id} in {total_time:.1f}s")
        
        return {
            "job_id": job_id,
            "keyword": config["primary_keyword"],
            "company": config["company_name"],
            "status": "success",
            "total_duration": round(total_time, 2),
            "stage_results": stage_results,
            "analysis": analysis
        }
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"❌ Blog failed: {job_id} after {total_time:.1f}s - {e}")
        
        return {
            "job_id": job_id,
            "keyword": config["primary_keyword"], 
            "company": config["company_name"],
            "status": "failed",
            "total_duration": round(total_time, 2),
            "error": str(e),
            "stage_results": stage_results if 'stage_results' in locals() else {}
        }

async def run_batch_test():
    """Run complete batch test with 10 blogs."""
    
    print("🛡️ ISAAC SECURITY V4.0 - 10-BLOG BATCH TEST")
    print("=" * 70)
    print("🔧 Testing complete 13-stage pipeline:")
    print("   ✅ Natural paragraph variety (no rigid limits)")
    print("   ✅ Conservative list preservation") 
    print("   ✅ Engaging lists with real content")
    print("   ✅ Citation validation with Gemini")
    print("   ✅ Internal link generation")
    print("   ✅ Parallel processing")
    print("")
    
    batch_start = time.time()
    
    print(f"🚀 Starting parallel generation of {len(BATCH_CONFIGS)} blogs...")
    
    # Run all blogs in parallel for maximum performance
    tasks = [run_single_blog(config) for config in BATCH_CONFIGS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "job_id": BATCH_CONFIGS[i]["job_id"],
                "status": "failed",
                "error": str(result),
                "total_duration": 0
            })
        else:
            processed_results.append(result)
    
    batch_time = time.time() - batch_start
    
    # Comprehensive analysis
    print("\n" + "=" * 70)
    print("🎉 BATCH TEST RESULTS")
    print("=" * 70)
    
    successful = [r for r in processed_results if r["status"] == "success"]
    failed = [r for r in processed_results if r["status"] == "failed"]
    
    print(f"✅ Successful: {len(successful)}/{len(BATCH_CONFIGS)}")
    print(f"❌ Failed: {len(failed)}/{len(BATCH_CONFIGS)}")
    print(f"🕒 Total batch time: {batch_time:.1f} seconds")
    
    if successful:
        avg_time = sum(r["total_duration"] for r in successful) / len(successful)
        total_words = sum(r["analysis"].get("word_count", 0) for r in successful if "analysis" in r)
        total_lists = sum(r["analysis"].get("list_count", 0) for r in successful if "analysis" in r)
        total_items = sum(r["analysis"].get("item_count", 0) for r in successful if "analysis" in r)
        total_links = sum(r["analysis"].get("links_count", 0) for r in successful if "analysis" in r)
        
        print(f"📊 Average generation time: {avg_time:.1f}s per blog")
        print(f"📝 Total content generated: {total_words:,} words")
        print(f"📋 Lists created: {total_lists} lists with {total_items} items")
        print(f"🔗 External links: {total_links}")
    
    print("\n📋 Individual Results:")
    for result in processed_results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        duration = result.get("total_duration", 0)
        
        if result["status"] == "success" and "analysis" in result:
            analysis = result["analysis"]
            word_count = analysis.get("word_count", 0)
            list_count = analysis.get("list_count", 0)
            print(f"{status_icon} {result['job_id']} ({duration:.1f}s) - {word_count:,} words, {list_count} lists")
        else:
            error = result.get("error", "Unknown error")[:50]
            print(f"{status_icon} {result['job_id']} ({duration:.1f}s) - FAILED: {error}")
    
    # Save comprehensive results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"batch_test_10_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "batch_duration": round(batch_time, 2),
            "total_blogs": len(BATCH_CONFIGS),
            "successful_blogs": len(successful),
            "failed_blogs": len(failed),
            "results": processed_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved: {results_file}")
    
    if successful:
        print(f"\n🌐 Generated blogs available in output/ directory")
        for result in successful:
            if "analysis" in result and "output_path" in result["analysis"]:
                print(f"   - {result['analysis']['output_path']}")
    
    return processed_results

if __name__ == "__main__":
    results = asyncio.run(run_batch_test())
    
    successful = sum(1 for r in results if r["status"] == "success")
    total = len(results)
    
    if successful == total:
        print(f"\n🎯 PERFECT SUCCESS: All {total} blogs generated successfully!")
    elif successful > 0:
        print(f"\n⚡ PARTIAL SUCCESS: {successful}/{total} blogs generated")
    else:
        print(f"\n💥 BATCH FAILED: No blogs generated successfully")