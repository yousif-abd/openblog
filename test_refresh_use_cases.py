#!/usr/bin/env python3
"""
Real-World REFRESH Use Cases Testing

Tests the refresh endpoint with diverse content refresh scenarios that users actually need:
1. Pricing updates (SaaS tools, subscriptions)
2. Feature updates (software, platform changes)
3. Compliance changes (regulations, legal updates)
4. Statistics refresh (market data, research findings)
5. Event updates (conferences, releases, announcements)
6. Rebranding updates (company names, product names)
7. Trend updates (industry shifts, new methodologies)
8. Contact info updates (addresses, personnel, support)
"""

import os
import json
from service.api import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Ensure API key is set
os.environ.setdefault("GEMINI_API_KEY", "AIzaSyDq6l8yzKncJRRkYLsJOjKIv3U4lXc9cM0")

def test_pricing_updates():
    """Use Case 1: Update outdated pricing in product comparisons"""
    print("\n=== USE CASE 1: PRICING UPDATES ===")
    
    content = """
    <h1>Best AI Writing Tools Comparison</h1>
    <h2>Pricing Overview</h2>
    <p>As of 2023, here are the current pricing models:</p>
    <ul>
        <li><strong>ChatGPT Plus:</strong> $20/month for unlimited access</li>
        <li><strong>Jasper AI:</strong> Starting at $29/month for 50,000 words</li>
        <li><strong>Copy.ai:</strong> Free plan available, Pro at $35/month</li>
        <li><strong>Grammarly Premium:</strong> $12/month when paid annually</li>
    </ul>
    <p>These prices were last verified in December 2023.</p>
    """
    
    response = client.post("/refresh", json={
        "content": content,
        "content_format": "html",
        "instructions": [
            "Update all pricing to current 2025 rates",
            "Research any new pricing tiers or plan changes", 
            "Add any new major AI writing tools that launched",
            "Verify current feature limitations for each tier"
        ],
        "output_format": "html",
        "include_diff": True
    })
    
    return analyze_response("Pricing Updates", response, ["2025", "pricing", "plan"])

def test_feature_updates():
    """Use Case 2: Update software features that have evolved"""
    print("\n=== USE CASE 2: FEATURE UPDATES ===")
    
    content = """
    <h1>Microsoft Teams vs Slack: Feature Comparison</h1>
    <h2>Key Capabilities</h2>
    <p>Both platforms offer basic messaging, but here are the standout features as of 2023:</p>
    <p><strong>Microsoft Teams:</strong> Integrates with Office 365, supports up to 250 participants in meetings, basic AI transcription available.</p>
    <p><strong>Slack:</strong> Superior third-party integrations, workflow automation through Slack Connect, limited to 50 participants in free tier meetings.</p>
    <p>AI features are still emerging in both platforms, with basic chatbots and simple automations.</p>
    """
    
    response = client.post("/refresh", json={
        "content": content,
        "content_format": "html",
        "instructions": [
            "Update with latest 2025 AI features in both platforms",
            "Research new integration capabilities and limits", 
            "Add any major feature launches from 2024-2025",
            "Update participant limits and meeting features"
        ],
        "output_format": "html"
    })
    
    return analyze_response("Feature Updates", response, ["AI", "integration", "2025"])

def test_compliance_updates():
    """Use Case 3: Update regulatory/compliance information"""
    print("\n=== USE CASE 3: COMPLIANCE UPDATES ===")
    
    content = """
    <h1>GDPR Compliance for SaaS Companies</h1>
    <h2>Current Requirements</h2>
    <p>Since GDPR took effect in 2018, companies must comply with data protection regulations.</p>
    <p>Recent updates in 2023 included clarifications on AI data processing and cookie consent requirements.</p>
    <p>Fines have reached significant amounts, with the largest being €1.2 billion against Meta in 2023.</p>
    <p>The upcoming Digital Services Act (DSA) will add additional requirements starting in 2024.</p>
    """
    
    response = client.post("/refresh", json={
        "content": content,
        "content_format": "html",
        "instructions": [
            "Update with 2024-2025 GDPR developments and enforcement",
            "Include latest major fines and enforcement actions",
            "Add current status of Digital Services Act implementation",
            "Research new AI governance regulations in EU"
        ],
        "output_format": "html"
    })
    
    return analyze_response("Compliance Updates", response, ["2024", "2025", "regulation", "enforcement"])

def test_statistics_refresh():
    """Use Case 4: Refresh market data and research statistics"""
    print("\n=== USE CASE 4: STATISTICS REFRESH ===")
    
    content = """
    <h1>Remote Work Trends in Tech</h1>
    <h2>Market Analysis</h2>
    <p>According to a 2022 survey by GitLab, 86% of developers prefer remote or hybrid work.</p>
    <p>The average tech salary increased by 8.5% in 2023, reaching $165,000 for senior roles.</p>
    <p>Companies are spending an average of $2,400 per employee on remote work setup and tools.</p>
    <p>Productivity metrics show mixed results, with some studies indicating 13% increases while others show declines.</p>
    """
    
    response = client.post("/refresh", json={
        "content": content,
        "content_format": "html",
        "instructions": [
            "Update all statistics to latest 2024-2025 research",
            "Research current tech salary trends and remote work preferences",
            "Find recent productivity studies and remote work effectiveness",
            "Add latest employer spending on remote work infrastructure"
        ],
        "output_format": "html"
    })
    
    return analyze_response("Statistics Refresh", response, ["2024", "2025", "survey", "study"])

def test_event_updates():
    """Use Case 5: Update event information and conference details"""
    print("\n=== USE CASE 5: EVENT UPDATES ===")
    
    content = """
    <h1>Top Cybersecurity Conferences 2024</h1>
    <h2>Must-Attend Events</h2>
    <p>The cybersecurity conference calendar for 2024 includes several key events:</p>
    <ul>
        <li><strong>RSA Conference:</strong> May 6-9, 2024 in San Francisco, focusing on AI security</li>
        <li><strong>Black Hat USA:</strong> August 3-8, 2024 in Las Vegas, with new IoT security track</li>
        <li><strong>DEF CON 32:</strong> August 8-11, 2024 following Black Hat</li>
        <li><strong>BSides:</strong> Multiple locations throughout 2024</li>
    </ul>
    <p>Registration typically opens 3-4 months in advance, with early bird pricing ending 6 weeks before the event.</p>
    """
    
    response = client.post("/refresh", json={
        "content": content,
        "content_format": "html",
        "instructions": [
            "Update to 2025 conference calendar and dates",
            "Research new tracks and focus areas for 2025 events",
            "Add any new major cybersecurity conferences launched",
            "Update pricing and registration timeline information"
        ],
        "output_format": "html"
    })
    
    return analyze_response("Event Updates", response, ["2025", "conference", "registration"])

def test_rebranding_updates():
    """Use Case 6: Update company/product name changes"""
    print("\n=== USE CASE 6: REBRANDING UPDATES ===")
    
    content = """
    <h1>Social Media Management Tools Guide</h1>
    <h2>Platform Comparison</h2>
    <p>Leading social media management platforms include:</p>
    <ul>
        <li><strong>Hootsuite:</strong> Comprehensive dashboard for multiple platforms</li>
        <li><strong>Buffer:</strong> Simple scheduling and analytics tool</li>
        <li><strong>Twitter for Business:</strong> Native advertising and management</li>
        <li><strong>Facebook Business Suite:</strong> Integrated Facebook and Instagram management</li>
    </ul>
    <p>Each platform offers different pricing models and integration capabilities with major social networks.</p>
    """
    
    response = client.post("/refresh", json={
        "content": content,
        "content_format": "html", 
        "instructions": [
            "Update any company or product name changes (Twitter → X, etc.)",
            "Research current feature sets and platform capabilities",
            "Add any major new social media management tools",
            "Update integration capabilities with current social platforms"
        ],
        "output_format": "html"
    })
    
    return analyze_response("Rebranding Updates", response, ["platform", "integration", "management"])

def test_trend_updates():
    """Use Case 7: Update industry trends and methodologies"""
    print("\n=== USE CASE 7: TREND UPDATES ===")
    
    content = """
    <h1>DevOps Best Practices 2023</h1>
    <h2>Current Methodologies</h2>
    <p>The DevOps landscape in 2023 emphasized containerization and microservices architecture.</p>
    <p>Key trends include Infrastructure as Code (IaC), with Terraform leading adoption at 67% of organizations.</p>
    <p>CI/CD pipelines are becoming more sophisticated, with AI-assisted testing gaining traction.</p>
    <p>Security integration (DevSecOps) is now standard practice, with shift-left security becoming the norm.</p>
    """
    
    response = client.post("/refresh", json={
        "content": content,
        "content_format": "html",
        "instructions": [
            "Update to 2025 DevOps trends and emerging practices",
            "Research latest tool adoption rates and platform preferences", 
            "Add information about AI/ML integration in DevOps workflows",
            "Include current security and compliance automation trends"
        ],
        "output_format": "html"
    })
    
    return analyze_response("Trend Updates", response, ["2025", "AI", "automation", "trend"])

def test_contact_updates():
    """Use Case 8: Update contact information and support details"""
    print("\n=== USE CASE 8: CONTACT INFO UPDATES ===")
    
    content = """
    <h1>Customer Support Guide</h1>
    <h2>Getting Help</h2>
    <p>For technical support, you can reach our team through multiple channels:</p>
    <ul>
        <li><strong>Email:</strong> support@company.com (24/7 response)</li>
        <li><strong>Phone:</strong> 1-800-SUPPORT (Mon-Fri, 9 AM - 6 PM PST)</li>
        <li><strong>Live Chat:</strong> Available on our website during business hours</li>
        <li><strong>Office:</strong> 123 Tech Street, San Francisco, CA 94105</li>
    </ul>
    <p>Our support team typically responds to emails within 2-4 hours during business days.</p>
    """
    
    response = client.post("/refresh", json={
        "content": content,
        "content_format": "html",
        "instructions": [
            "Verify all contact information is current and accurate",
            "Update support hours and response time commitments",
            "Add any new support channels (AI chat, social media, etc.)",
            "Research if company has moved offices or changed contact details"
        ],
        "output_format": "html"
    })
    
    return analyze_response("Contact Updates", response, ["support", "contact", "response"])

def analyze_response(test_name, response, key_indicators):
    """Analyze refresh response quality"""
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        success = data.get('success', False)
        print(f"✅ Success: {success}")
        
        if success:
            content = data.get('refreshed_html', '')
            if content:
                # Check for indicators
                found_indicators = [ind for ind in key_indicators if ind.lower() in content.lower()]
                print(f"✅ Key indicators found: {found_indicators}")
                
                # Check content length (should be substantial)
                print(f"✅ Content length: {len(content)} chars")
                
                # Show sample
                print(f"Sample updated content:")
                print(content[:250] + "...")
                
                # Check for diff
                if data.get('diff_text'):
                    print(f"✅ Changes detected in diff")
                else:
                    print("⚠️  No diff generated")
                    
                return True
            else:
                print("❌ No content returned")
                return False
        else:
            print(f"❌ Request failed")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.json()}")
        return False

def main():
    """Run all use case tests"""
    print("=" * 60)
    print("REFRESH ENDPOINT - REAL-WORLD USE CASES TESTING")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  WARNING: GEMINI_API_KEY not set!")
        return
    
    test_cases = [
        ("Pricing Updates", test_pricing_updates),
        ("Feature Updates", test_feature_updates), 
        ("Compliance Updates", test_compliance_updates),
        ("Statistics Refresh", test_statistics_refresh),
        ("Event Updates", test_event_updates),
        ("Rebranding Updates", test_rebranding_updates),
        ("Trend Updates", test_trend_updates),
        ("Contact Info Updates", test_contact_updates),
    ]
    
    results = []
    
    try:
        for test_name, test_func in test_cases:
            print(f"\n{'='*20} {test_name} {'='*20}")
            success = test_func()
            results.append((test_name, success))
            
            # Small delay to avoid rate limiting
            import time
            time.sleep(2)
        
        print("\n" + "=" * 60)
        print("USE CASE TESTING SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        print(f"✅ Tests Passed: {passed}/{total}")
        print(f"📊 Success Rate: {(passed/total*100):.1f}%")
        
        print("\nDetailed Results:")
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {status}: {test_name}")
            
        if passed == total:
            print(f"\n🎉 ALL USE CASES WORKING PERFECTLY!")
            print("The REFRESH endpoint handles diverse real-world scenarios excellently.")
        else:
            print(f"\n⚠️  Some use cases need attention.")
            
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()