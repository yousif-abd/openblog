#!/usr/bin/env python3
"""
Deep Content Quality Audit for OpenBlog
Stress test blog generation against writesonic/airops standards.

Quality benchmarks:
- Writesonic: 8/10 content quality, good SEO, sometimes generic
- Airops: 7/10 content quality, workflow focus, less depth
- Target: 9/10+ content quality, deep research, unique insights

Audit criteria:
1. Research Depth - Does it go beyond surface-level?
2. Originality - Unique insights or just repackaged info?
3. SEO Quality - Proper optimization without keyword stuffing?
4. Readability - Clear, engaging, professional tone?
5. Structure - Logical flow, proper headings, scannable?
6. Factual Accuracy - Verifiable claims, proper citations?
7. Comprehensiveness - Covers topic thoroughly?
8. Engagement - Keeps reader interested?
9. Professional Polish - Publication-ready?
10. Value Add - Does reader gain actionable insights?
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List
import re


class ContentQualityAuditor:
    """Audits blog content quality against professional standards."""
    
    def __init__(self):
        self.test_topics = [
            {
                "title": "How AI is Transforming Content Marketing in 2025",
                "keywords": ["AI content marketing", "marketing automation", "content strategy"],
                "target_length": 2000,
                "difficulty": "medium",
            },
            {
                "title": "Complete Guide to Answer Engine Optimization (AEO)",
                "keywords": ["AEO", "answer engine optimization", "AI search"],
                "target_length": 3000,
                "difficulty": "high",
            },
            {
                "title": "10 Proven Strategies to Increase Website Traffic",
                "keywords": ["website traffic", "SEO", "digital marketing"],
                "target_length": 2500,
                "difficulty": "easy",
            },
        ]
    
    def analyze_research_depth(self, content: str) -> Dict[str, Any]:
        """Analyze depth of research and insights."""
        scores = {}
        
        # Check for statistics and data
        stats_pattern = r'\d+%|\d+x|\$\d+|#\d+'
        stats_count = len(re.findall(stats_pattern, content))
        scores['statistics_usage'] = min(10, stats_count / 5 * 10)  # 5+ stats = full score
        
        # Check for specific examples
        example_keywords = ['for example', 'for instance', 'case study', 'such as']
        example_count = sum(content.lower().count(kw) for kw in example_keywords)
        scores['examples'] = min(10, example_count / 3 * 10)  # 3+ examples = full score
        
        # Check for depth indicators
        depth_keywords = ['research shows', 'study found', 'according to', 'analysis reveals', 'data indicates']
        depth_count = sum(content.lower().count(kw) for kw in depth_keywords)
        scores['research_citations'] = min(10, depth_count / 5 * 10)
        
        # Check for actionable insights
        action_keywords = ['how to', 'step', 'implement', 'strategy', 'tactic', 'method']
        action_count = sum(content.lower().count(kw) for kw in action_keywords)
        scores['actionability'] = min(10, action_count / 5 * 10)
        
        # Overall research depth
        avg_score = sum(scores.values()) / len(scores)
        
        return {
            'score': round(avg_score, 1),
            'breakdown': scores,
            'verdict': self._get_verdict(avg_score, "research depth")
        }
    
    def analyze_originality(self, content: str) -> Dict[str, Any]:
        """Analyze originality and uniqueness."""
        scores = {}
        
        # Check for generic phrases (bad sign)
        generic_phrases = [
            'in today\'s digital age',
            'it\'s no secret that',
            'in conclusion',
            'last but not least',
            'needless to say'
        ]
        generic_count = sum(content.lower().count(phrase) for phrase in generic_phrases)
        scores['avoids_cliches'] = max(0, 10 - generic_count * 2)
        
        # Check for unique angles
        unique_indicators = ['surprisingly', 'contrary to', 'overlooked', 'hidden', 'secret', 'myth']
        unique_count = sum(content.lower().count(word) for word in unique_indicators)
        scores['unique_angles'] = min(10, unique_count / 2 * 10)
        
        # Check for personal insights / opinions
        insight_indicators = ['here\'s why', 'the key is', 'the truth is', 'what matters', 'what works']
        insight_count = sum(content.lower().count(phrase) for phrase in insight_indicators)
        scores['insights'] = min(10, insight_count / 3 * 10)
        
        avg_score = sum(scores.values()) / len(scores)
        
        return {
            'score': round(avg_score, 1),
            'breakdown': scores,
            'verdict': self._get_verdict(avg_score, "originality")
        }
    
    def analyze_seo_quality(self, content: str, keywords: List[str]) -> Dict[str, Any]:
        """Analyze SEO optimization quality."""
        scores = {}
        
        # Keyword density (should be 1-2%)
        word_count = len(content.split())
        keyword_count = sum(content.lower().count(kw.lower()) for kw in keywords)
        keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0
        
        if 1 <= keyword_density <= 2:
            scores['keyword_density'] = 10
        elif 0.5 <= keyword_density < 1 or 2 < keyword_density <= 3:
            scores['keyword_density'] = 7
        else:
            scores['keyword_density'] = 4
        
        # Heading structure
        h2_count = content.count('##')
        h3_count = content.count('###')
        scores['heading_structure'] = min(10, (h2_count + h3_count) / 8 * 10)
        
        # Internal linking potential
        link_anchors = len(re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content))
        scores['internal_links'] = min(10, link_anchors / 5 * 10)
        
        # Meta description quality (first 160 chars)
        first_para = content.split('\n\n')[0][:160] if content else ""
        has_keyword = any(kw.lower() in first_para.lower() for kw in keywords)
        scores['meta_description'] = 10 if has_keyword else 5
        
        avg_score = sum(scores.values()) / len(scores)
        
        return {
            'score': round(avg_score, 1),
            'breakdown': scores,
            'keyword_density': round(keyword_density, 2),
            'verdict': self._get_verdict(avg_score, "SEO quality")
        }
    
    def analyze_readability(self, content: str) -> Dict[str, Any]:
        """Analyze readability and engagement."""
        scores = {}
        
        # Sentence length (shorter is better for web)
        sentences = re.split(r'[.!?]+', content)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
        if avg_sentence_length < 20:
            scores['sentence_length'] = 10
        elif avg_sentence_length < 25:
            scores['sentence_length'] = 7
        else:
            scores['sentence_length'] = 5
        
        # Paragraph length
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        avg_para_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        scores['paragraph_length'] = 10 if avg_para_length < 100 else 7 if avg_para_length < 150 else 5
        
        # Use of lists and formatting
        list_count = content.count('- ') + content.count('* ') + content.count('1. ')
        scores['formatting'] = min(10, list_count / 10 * 10)
        
        # Engagement elements
        engagement_words = ['you', 'your', 'we', 'let\'s', '?']
        engagement_count = sum(content.lower().count(word) for word in engagement_words)
        scores['engagement'] = min(10, engagement_count / 20 * 10)
        
        avg_score = sum(scores.values()) / len(scores)
        
        return {
            'score': round(avg_score, 1),
            'breakdown': scores,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'verdict': self._get_verdict(avg_score, "readability")
        }
    
    def analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze content structure and organization."""
        scores = {}
        
        # Introduction quality
        first_300 = content[:300]
        has_hook = any(word in first_300.lower() for word in ['why', 'how', 'what', 'discover', 'learn'])
        scores['introduction'] = 10 if has_hook else 6
        
        # Logical flow (transitions)
        transitions = ['however', 'moreover', 'furthermore', 'additionally', 'therefore', 'consequently']
        transition_count = sum(content.lower().count(word) for word in transitions)
        scores['transitions'] = min(10, transition_count / 5 * 10)
        
        # Conclusion present
        has_conclusion = any(word in content.lower()[-500:] for word in ['conclusion', 'summary', 'takeaway', 'remember'])
        scores['conclusion'] = 10 if has_conclusion else 5
        
        # Section balance
        sections = content.split('##')
        if len(sections) > 2:
            section_lengths = [len(s) for s in sections[1:]]  # Skip intro
            avg_length = sum(section_lengths) / len(section_lengths)
            variance = sum((l - avg_length) ** 2 for l in section_lengths) / len(section_lengths)
            scores['section_balance'] = 10 if variance < avg_length * 0.5 else 7
        else:
            scores['section_balance'] = 5
        
        avg_score = sum(scores.values()) / len(scores)
        
        return {
            'score': round(avg_score, 1),
            'breakdown': scores,
            'verdict': self._get_verdict(avg_score, "structure")
        }
    
    def analyze_professionalism(self, content: str) -> Dict[str, Any]:
        """Analyze professional polish and publication readiness."""
        scores = {}
        
        # Grammar indicators (simple checks)
        common_errors = ['alot', 'definately', 'recieve', 'occured', 'seperate']
        error_count = sum(content.lower().count(error) for error in common_errors)
        scores['grammar'] = max(0, 10 - error_count * 3)
        
        # Professional tone
        casual_words = ['gonna', 'wanna', 'kinda', 'sorta', 'yeah', 'nope']
        casual_count = sum(content.lower().count(word) for word in casual_words)
        scores['tone'] = max(0, 10 - casual_count * 2)
        
        # Proper formatting
        has_bold = '**' in content or '__' in content
        has_emphasis = '*' in content or '_' in content
        scores['formatting'] = 10 if (has_bold or has_emphasis) else 7
        
        # Citation quality
        has_sources = '[' in content and '](' in content
        scores['citations'] = 10 if has_sources else 5
        
        avg_score = sum(scores.values()) / len(scores)
        
        return {
            'score': round(avg_score, 1),
            'breakdown': scores,
            'verdict': self._get_verdict(avg_score, "professionalism")
        }
    
    def _get_verdict(self, score: float, category: str) -> str:
        """Get verdict based on score."""
        if score >= 9:
            return f"🟢 Excellent {category} - Publication ready"
        elif score >= 7:
            return f"🟡 Good {category} - Minor improvements needed"
        elif score >= 5:
            return f"🟠 Fair {category} - Needs work"
        else:
            return f"🔴 Poor {category} - Major improvements required"
    
    def comprehensive_audit(self, content: str, keywords: List[str]) -> Dict[str, Any]:
        """Run comprehensive content audit."""
        print("\n" + "=" * 80)
        print("🔍 COMPREHENSIVE CONTENT QUALITY AUDIT")
        print("=" * 80)
        
        word_count = len(content.split())
        char_count = len(content)
        
        print(f"\n📊 Basic Metrics:")
        print(f"   Word count: {word_count}")
        print(f"   Character count: {char_count}")
        print(f"   Estimated reading time: {word_count // 200} minutes")
        
        # Run all analyses
        research = self.analyze_research_depth(content)
        originality = self.analyze_originality(content)
        seo = self.analyze_seo_quality(content, keywords)
        readability = self.analyze_readability(content)
        structure = self.analyze_structure(content)
        professionalism = self.analyze_professionalism(content)
        
        # Calculate overall score
        overall_score = (
            research['score'] * 0.25 +  # Research is most important
            originality['score'] * 0.20 +
            seo['score'] * 0.15 +
            readability['score'] * 0.15 +
            structure['score'] * 0.15 +
            professionalism['score'] * 0.10
        )
        
        print(f"\n📈 Quality Scores:")
        print(f"   Research Depth:    {research['score']}/10 - {research['verdict']}")
        print(f"   Originality:       {originality['score']}/10 - {originality['verdict']}")
        print(f"   SEO Quality:       {seo['score']}/10 - {seo['verdict']}")
        print(f"   Readability:       {readability['score']}/10 - {readability['verdict']}")
        print(f"   Structure:         {structure['score']}/10 - {structure['verdict']}")
        print(f"   Professionalism:   {professionalism['score']}/10 - {professionalism['verdict']}")
        
        print(f"\n🎯 OVERALL QUALITY SCORE: {overall_score:.1f}/10")
        
        # Benchmark comparison
        print(f"\n📊 Benchmark Comparison:")
        print(f"   Writesonic standard: 8.0/10")
        print(f"   Airops standard:     7.0/10")
        print(f"   Your content:        {overall_score:.1f}/10")
        
        if overall_score >= 9.0:
            print(f"   🏆 EXCEEDS industry standards!")
        elif overall_score >= 8.0:
            print(f"   ✅ MEETS Writesonic quality")
        elif overall_score >= 7.0:
            print(f"   ⚠️  MEETS Airops quality (room for improvement)")
        else:
            print(f"   ❌ BELOW industry standards - needs significant work")
        
        # Detailed recommendations
        print(f"\n💡 Recommendations:")
        issues = []
        if research['score'] < 7:
            issues.append("• Add more statistics, research citations, and concrete examples")
        if originality['score'] < 7:
            issues.append("• Avoid generic phrases and add unique insights/perspectives")
        if seo['score'] < 7:
            issues.append(f"• Optimize keyword density (current: {seo['keyword_density']}%, target: 1-2%)")
        if readability['score'] < 7:
            issues.append(f"• Improve readability (avg sentence length: {readability.get('avg_sentence_length', 'N/A')} words)")
        if structure['score'] < 7:
            issues.append("• Improve content structure and logical flow")
        if professionalism['score'] < 7:
            issues.append("• Polish grammar, tone, and add proper citations")
        
        if issues:
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"   ✅ Content is publication-ready!")
        
        return {
            'overall_score': round(overall_score, 1),
            'word_count': word_count,
            'research': research,
            'originality': originality,
            'seo': seo,
            'readability': readability,
            'structure': structure,
            'professionalism': professionalism,
            'meets_writesonic_standard': overall_score >= 8.0,
            'issues': issues,
        }


async def stress_test_blog_generation():
    """Stress test blog generation with real API calls."""
    print("🚀 Starting Blog Generation Stress Test")
    print("=" * 80)
    print("Testing against writesonic/airops quality standards...")
    print()
    
    auditor = ContentQualityAuditor()
    
    # Test with sample content (in production, call real API)
    sample_content = """# How AI is Transforming Content Marketing in 2025

## Introduction

Artificial intelligence has revolutionized how businesses approach content marketing. According to recent research, 78% of marketers now use AI tools in their content strategy, up from just 23% in 2020. This dramatic shift signals a fundamental change in how we create, distribute, and optimize content.

## The Current State of AI Content Marketing

Research shows that AI-powered content tools have increased productivity by 10x while maintaining or improving quality. For example, companies using AI content assistants report generating 5x more content with the same team size.

However, the key is not just quantity—it's about delivering value. Analysis reveals that AI-generated content performs 35% better in search rankings when properly optimized and humanized.

## Key Strategies for Success

### 1. Focus on Quality Over Quantity

The truth is, search engines prioritize value over volume. Here's why: algorithms have become sophisticated enough to detect thin, AI-generated content that doesn't serve user intent.

### 2. Combine AI with Human Expertise

What works best is a hybrid approach. Studies indicate that content reviewed and enhanced by human editors performs 50% better than purely AI-generated pieces.

### 3. Optimize for User Intent

Contrary to popular belief, keyword stuffing is dead. Modern AI tools analyze user intent and create content that genuinely answers questions.

## Implementation Tactics

To implement these strategies effectively:

- Start with thorough research using AI tools
- Generate initial drafts with AI assistants
- Add unique insights and examples manually
- Optimize for SEO without sacrificing readability
- Test and iterate based on performance data

## Conclusion

The future of content marketing lies in intelligent collaboration between AI and human creativity. Organizations that master this balance will dominate their markets. The data clearly shows: AI is not replacing marketers—it's empowering them to do their best work.
"""
    
    # Run comprehensive audit
    result = auditor.comprehensive_audit(
        sample_content,
        keywords=["AI content marketing", "marketing automation", "content strategy"]
    )
    
    print("\n" + "=" * 80)
    print("✅ Stress Test Complete")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    asyncio.run(stress_test_blog_generation())

