#!/usr/bin/env python3
"""
Test regex patterns to ensure they don't destroy valid content.
"""
import re

def test_dangerous_regex_patterns():
    """Test regex patterns that could destroy valid content."""
    
    print("🚨 Testing Potentially Dangerous Regex Patterns...")
    
    # Test cases with content that should NOT be removed
    test_cases = [
        {
            "name": "List item ending with preposition (VALID)",
            "content": "<li>This security framework is what you need to rely on</li>",
            "pattern": r'<li>[^<]*\b(of|by|the|and|with|for|to|in|on|at|from)\s*</li>',
            "should_be_removed": False,
            "description": "Valid list item ending with preposition 'on'"
        },
        {
            "name": "List item ending with 'the' (VALID)",
            "content": "<li>Organizations must understand the risks and mitigate the</li>",
            "pattern": r'<li>[^<]*\b(of|by|the|and|with|for|to|in|on|at|from)\s*</li>',
            "should_be_removed": True,  # This one should be removed as it's incomplete
            "description": "Invalid fragment ending with 'the' (should be removed)"
        },
        {
            "name": "List with 'a data' pattern (QUESTIONABLE)",
            "content": "<li>This approach provides a data-driven solution for security teams</li>",
            "pattern": r'<li>[^<]*\ba\s+[a-z]{2,8}\s*</li>',
            "should_be_removed": False,
            "description": "Valid list item with 'a data-driven' should NOT be removed"
        },
        {
            "name": "Short but valid list item",
            "content": "<li>Speed matters</li>",
            "pattern": r'<li>\s*\w+\s*\w*\s*</li>',
            "should_be_removed": True,  # This is 2 words, should be removed per our rule
            "description": "2-word list item (correctly removed per rule)"
        },
        {
            "name": "Valid 3-word list item",
            "content": "<li>Security teams benefit</li>",
            "pattern": r'<li>\s*\w+\s*\w*\s*</li>',
            "should_be_removed": False,
            "description": "3-word list item should NOT be removed"
        }
    ]
    
    issues_found = []
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        
        original = test_case["content"]
        result = re.sub(test_case["pattern"], '', original)
        was_removed = (result != original)
        
        if was_removed == test_case["should_be_removed"]:
            print(f"✅ CORRECT: {test_case['description']}")
        else:
            print(f"❌ PROBLEM: {test_case['description']}")
            print(f"   Original: {original}")
            print(f"   Result:   {result}")
            print(f"   Expected removal: {test_case['should_be_removed']}, Actual: {was_removed}")
            issues_found.append(test_case["name"])
    
    return len(issues_found) == 0, issues_found

def test_conservative_patterns():
    """Test that our patterns are conservative enough."""
    
    print("\n🛡️  Testing Conservative Pattern Behavior...")
    
    # These should definitely NOT be removed
    protected_content = [
        "<li>Organizations rely on zero trust architecture for security</li>",
        "<li>Teams implement SIEM automation to reduce alert fatigue</li>",
        "<li>Security professionals need training on cloud compliance frameworks</li>",
        "<li>Multi-factor authentication prevents 99% of account takeovers</li>",
        "<li>Incident response plans must be tested quarterly</li>",
    ]
    
    dangerous_patterns = [
        r'<li>[^<]*\b(of|by|the|and|with|for|to|in|on|at|from)\s*</li>',  # Preposition endings
        r'<li>[^<]*\ba\s+[a-z]{2,8}\s*</li>',  # 'a word' patterns
        r'<li>\s*\w+\s*\w*\s*</li>',  # 1-2 word items
    ]
    
    issues = []
    
    for content in protected_content:
        for i, pattern in enumerate(dangerous_patterns):
            result = re.sub(pattern, '', content)
            if result != content:
                issues.append(f"Pattern {i+1} incorrectly removed: {content}")
    
    if issues:
        print("❌ DANGEROUS PATTERNS FOUND:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("✅ All valid content is protected")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("ISAAC SECURITY V4.0 - REGEX SAFETY AUDIT")
    print("=" * 60)
    
    patterns_safe, pattern_issues = test_dangerous_regex_patterns()
    conservative_safe = test_conservative_patterns()
    
    print("\n" + "=" * 60)
    print("REGEX SAFETY RESULTS:")
    print("=" * 60)
    
    if patterns_safe:
        print("✅ Regex Pattern Logic: SAFE")
    else:
        print("❌ Regex Pattern Logic: ISSUES FOUND")
        print(f"   Problems with: {', '.join(pattern_issues)}")
    
    if conservative_safe:
        print("✅ Content Protection: WORKING")
    else:
        print("❌ Content Protection: DESTROYING VALID CONTENT")
    
    overall_safe = patterns_safe and conservative_safe
    
    if overall_safe:
        print("\n🎉 ALL REGEX PATTERNS ARE SAFE FOR PRODUCTION")
    else:
        print("\n🚨 DANGEROUS REGEX PATTERNS DETECTED - NEEDS FIXES")
    
    exit(0 if overall_safe else 1)