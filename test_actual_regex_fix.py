#!/usr/bin/env python3
"""
Test the actual fixed regex patterns from html_renderer.py.
"""

def test_fixed_cleanup_patterns():
    """Test the actual _cleanup_content function with our fixes."""
    
    from pipeline.processors.html_renderer import HTMLRenderer
    
    print("🧪 Testing Fixed HTML Cleanup Patterns...")
    
    test_cases = [
        {
            "name": "Valid list ending with preposition",
            "input": "<li>This security framework is what you need to rely on</li>",
            "should_survive": True,
            "description": "Should preserve valid sentences ending with prepositions"
        },
        {
            "name": "Invalid fragment 'a data'",
            "input": "<li>the average cost of a data</li>",
            "should_survive": False,
            "description": "Should remove incomplete fragment ending with 'a data'"
        },
        {
            "name": "Valid 'a data-driven' usage",
            "input": "<li>This approach provides a data-driven solution for security teams</li>",
            "should_survive": True,
            "description": "Should preserve valid usage of 'a data-driven'"
        },
        {
            "name": "Short 2-word item",
            "input": "<li>Speed matters</li>",
            "should_survive": False,
            "description": "Should remove 2-word list items"
        },
        {
            "name": "Valid 3+ word item",
            "input": "<li>Security teams benefit significantly</li>",
            "should_survive": True,
            "description": "Should preserve 3+ word list items"
        },
        {
            "name": "Mixed content with various patterns",
            "input": '''
            <li>Organizations rely on zero trust architecture</li>
            <li>Speed</li>
            <li>the average cost of a data</li>
            <li>Teams implement effective security controls</li>
            <li>a key</li>
            ''',
            "should_survive": True,  # Some content should survive
            "description": "Mixed content test"
        }
    ]
    
    issues = []
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        
        original = test_case["input"]
        cleaned = HTMLRenderer._cleanup_content(original)
        
        if test_case["should_survive"]:
            # Should preserve most content
            content_mostly_preserved = (len(cleaned.strip()) > len(original.strip()) * 0.5)
            if content_mostly_preserved:
                print(f"✅ PASSED: {test_case['description']}")
            else:
                print(f"❌ FAILED: {test_case['description']}")
                print(f"   Original: {original.strip()}")
                print(f"   Cleaned:  {cleaned.strip()}")
                issues.append(test_case["name"])
        else:
            # Should remove most content
            content_mostly_removed = (len(cleaned.strip()) < len(original.strip()) * 0.5)
            if content_mostly_removed:
                print(f"✅ PASSED: {test_case['description']}")
            else:
                print(f"❌ FAILED: {test_case['description']}")
                print(f"   Original: {original.strip()}")
                print(f"   Cleaned:  {cleaned.strip()}")
                issues.append(test_case["name"])
    
    return len(issues) == 0, issues

def test_specific_fixed_patterns():
    """Test the specific patterns we fixed."""
    
    print("\n🎯 Testing Specific Pattern Fixes...")
    
    from pipeline.processors.html_renderer import HTMLRenderer
    
    # Test the dangerous pattern we removed
    test_content = "<li>This security framework is what you need to rely on</li>"
    result = HTMLRenderer._cleanup_content(test_content)
    
    if test_content.strip() in result or "rely on" in result:
        print("✅ CRITICAL FIX CONFIRMED: Valid content ending with preposition is preserved")
        return True
    else:
        print("❌ CRITICAL ISSUE: Valid content still being destroyed")
        print(f"   Original: {test_content}")
        print(f"   Result:   {result}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ISAAC SECURITY V4.0 - REGEX FIX VALIDATION")
    print("=" * 60)
    
    patterns_safe, issues = test_fixed_cleanup_patterns()
    critical_fix_works = test_specific_fixed_patterns()
    
    print("\n" + "=" * 60)
    print("REGEX FIX RESULTS:")
    print("=" * 60)
    
    if patterns_safe:
        print("✅ Cleanup Pattern Safety: WORKING")
    else:
        print("❌ Cleanup Pattern Safety: ISSUES REMAIN")
        print(f"   Problems: {', '.join(issues)}")
    
    if critical_fix_works:
        print("✅ Critical Preposition Fix: WORKING")
    else:
        print("❌ Critical Preposition Fix: FAILED")
    
    overall_safe = patterns_safe and critical_fix_works
    
    if overall_safe:
        print("\n🎉 ALL REGEX FIXES VALIDATED - PRODUCTION SAFE")
    else:
        print("\n🚨 REGEX ISSUES REMAIN - NEEDS MORE FIXES")
    
    exit(0 if overall_safe else 1)