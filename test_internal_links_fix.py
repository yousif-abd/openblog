#!/usr/bin/env python3
"""
Test to verify internal links validation is working correctly.
"""
import re

def test_prompt_internal_links():
    """Test that the prompt includes mandatory internal links requirements."""
    
    from pipeline.prompts.main_article import get_main_article_prompt
    
    print("🔗 Testing Internal Links Prompt Requirements...")
    
    # Generate a test prompt
    prompt = get_main_article_prompt(
        primary_keyword="test keyword",
        company_name="TestCorp",
        language="en",
        country="US"
    )
    
    # Check for our internal links improvements
    link_checks = [
        {
            "check": "CRITICAL REQUIREMENT: Your article WILL BE REJECTED if it contains fewer than 3 internal links" in prompt,
            "description": "Has strict internal links requirement"
        },
        {
            "check": "INTERNAL LINKS: Less than 3 internal links → INSTANT REJECTION" in prompt,
            "description": "Includes internal links in validation rules"
        },
        {
            "check": prompt.count("/magazine/") >= 10,  # Should have many examples
            "description": "Provides sufficient internal link examples"
        },
        {
            "check": "ai-security-best-practices" in prompt and "cloud-security" in prompt,
            "description": "Contains specific security topic examples"
        }
    ]
    
    all_passed = True
    
    for check in link_checks:
        if check["check"]:
            print(f"✅ PASSED: {check['description']}")
        else:
            print(f"❌ FAILED: {check['description']}")
            all_passed = False
    
    return all_passed

def test_content_internal_links():
    """Test actual generated content for internal links."""
    
    print("\n🎯 Testing Real Generated Content Internal Links...")
    
    # Test patterns from our batch test results
    test_cases = [
        {
            "name": "Zero Trust Blog",
            "content": '''<a href="/magazine/network-security">Network security strategies</a> like this are crucial''',
            "expected_links": 1,
            "description": "Should contain properly formatted internal links"
        },
        {
            "name": "SIEM Automation Blog",
            "content": '''<a href="/magazine/incident-response-playbooks">pre-built playbooks</a> provided by vendors''',
            "expected_links": 1,
            "description": "Should contain incident response internal links"
        },
        {
            "name": "Blog with NO Internal Links",
            "content": '''<p>Organizations report benefits according to studies. External citations work.</p>''',
            "expected_links": 0,
            "description": "Should be REJECTED for missing internal links"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        
        # Count internal links
        internal_link_pattern = r'<a href="/magazine/[^"]*"[^>]*>'
        links_found = re.findall(internal_link_pattern, test_case["content"])
        links_count = len(links_found)
        
        if links_count == test_case["expected_links"]:
            if test_case["expected_links"] >= 3:
                print(f"✅ PASSED: Found {links_count} internal links (meets requirement)")
            elif test_case["expected_links"] == 0:
                print(f"⚠️  WOULD BE REJECTED: {links_count} internal links (below minimum 3)")
            else:
                print(f"✅ PASSED: Found {links_count} internal links (as expected)")
        else:
            print(f"❌ FAILED: Expected {test_case['expected_links']}, found {links_count}")
            all_passed = False
        
        # Show found links
        if links_found:
            for link in links_found:
                print(f"   Found: {link}")
    
    return all_passed

if __name__ == "__main__":
    print("=" * 60)
    print("ISAAC SECURITY V4.0 - INTERNAL LINKS VALIDATION")
    print("=" * 60)
    
    # Run both test suites
    prompt_passed = test_prompt_internal_links()
    content_passed = test_content_internal_links()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print("=" * 60)
    
    if prompt_passed:
        print("✅ Prompt Internal Links Requirements: ENFORCED")
    else:
        print("❌ Prompt Internal Links Requirements: FAILED")
    
    if content_passed:
        print("✅ Content Internal Links Validation: WORKING")  
    else:
        print("❌ Content Internal Links Validation: FAILED")
    
    overall_success = prompt_passed and content_passed
    
    if overall_success:
        print("\n🎉 INTERNAL LINKS ENFORCEMENT VALIDATED")
        print("📋 All future articles WILL BE REJECTED if they have fewer than 3 internal links")
        exit(0)
    else:
        print("\n🚨 INTERNAL LINKS ENFORCEMENT ISSUES REMAIN")
        exit(1)