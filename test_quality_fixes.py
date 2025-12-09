#!/usr/bin/env python3
"""
Quick test to verify content quality fixes are working.
"""
import re

def test_content_cleanup():
    """Test the HTML renderer content cleanup function."""
    
    # Import the function we fixed
    from pipeline.processors.html_renderer import HTMLRenderer
    
    # Test cases for broken content patterns we fixed
    test_cases = [
        {
            "name": "Broken grammar pattern",
            "input": "<p>You can to implement this solution effectively.</p>",
            "should_not_contain": ["You can to"],
            "description": "Should fix broken 'You can to' patterns"
        },
        {
            "name": "Incomplete list items",
            "input": "<li>The cybersecurity landscape has shifted dramatically, driven by the relentless sophistication of</li>",
            "should_not_contain": ["of</li>"],  # Should not end mid-thought
            "description": "Should not have incomplete sentence fragments in lists"
        },
        {
            "name": "Academic citation cleanup",
            "input": "<p>Organizations report 55% improvements [1][2].</p>",
            "should_not_contain": ["[1]", "[2]"],
            "description": "Should remove all academic citations [N]"
        }
    ]
    
    print("🧪 Testing Content Quality Fixes...")
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        
        # Apply the cleanup function
        cleaned_content = HTMLRenderer._cleanup_content(test_case["input"])
        
        # Check if prohibited patterns are removed
        failed_checks = []
        for prohibited_pattern in test_case["should_not_contain"]:
            if prohibited_pattern in cleaned_content:
                failed_checks.append(prohibited_pattern)
        
        if failed_checks:
            print(f"❌ FAILED: Still contains: {failed_checks}")
            print(f"   Input:  {test_case['input']}")
            print(f"   Output: {cleaned_content}")
            all_passed = False
        else:
            print(f"✅ PASSED: {test_case['description']}")
    
    return all_passed

def test_prompt_improvements():
    """Test that the prompt includes our quality improvements."""
    
    from pipeline.prompts.main_article import get_main_article_prompt
    
    print("\n🎯 Testing Prompt Quality Improvements...")
    
    # Generate a test prompt
    prompt = get_main_article_prompt(
        primary_keyword="test keyword",
        company_name="TestCorp",
        language="en",
        country="US"
    )
    
    # Check for our quality improvements
    quality_checks = [
        {
            "check": "Complete, grammatically correct sentences at ALL times" in prompt,
            "description": "Includes grammar quality requirement"
        },
        {
            "check": "Every list item MUST be a complete thought" in prompt,
            "description": "Includes list quality requirement"
        },
        {
            "check": "NO broken patterns like \"You can to implement\"" in prompt,
            "description": "Explicitly forbids broken grammar patterns"
        },
        {
            "check": "CONTENT QUALITY VIOLATIONS → INSTANT REJECTION" in prompt,
            "description": "Has strict quality validation rules"
        }
    ]
    
    all_passed = True
    
    for check in quality_checks:
        if check["check"]:
            print(f"✅ PASSED: {check['description']}")
        else:
            print(f"❌ FAILED: {check['description']}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("=" * 60)
    print("ISAAC SECURITY V4.0 - CONTENT QUALITY VALIDATION")
    print("=" * 60)
    
    # Run both test suites
    cleanup_passed = test_content_cleanup()
    prompt_passed = test_prompt_improvements()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print("=" * 60)
    
    if cleanup_passed:
        print("✅ Content Cleanup Fixes: WORKING")
    else:
        print("❌ Content Cleanup Fixes: FAILED")
    
    if prompt_passed:
        print("✅ Prompt Quality Improvements: WORKING")  
    else:
        print("❌ Prompt Quality Improvements: FAILED")
    
    overall_success = cleanup_passed and prompt_passed
    
    if overall_success:
        print("\n🎉 ALL QUALITY FIXES VALIDATED - PRODUCTION READY")
        exit(0)
    else:
        print("\n🚨 QUALITY ISSUES REMAIN - NEEDS FURTHER FIXES")
        exit(1)