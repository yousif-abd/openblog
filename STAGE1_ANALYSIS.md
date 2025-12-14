# Stage 1 Analysis: Prompt Build

**Date:** December 14, 2025

---

## 📋 Stage 1 Full Output

### Generated Prompt (2,910 characters)

```
Write a comprehensive, high-quality blog article about "cloud security best practices".


COMPANY CONTEXT:
Company: Test Company
Website: https://example.com
Industry: Cybersecurity
Description: A leading cybersecurity company providing cloud security solutions.
Products/Services: Cloud Security Platform, Threat Detection, Compliance Management
Target Audience: Enterprise IT security teams
Brand Tone: professional

CUSTOMER PAIN POINTS:
- Complex cloud environments
- Regulatory compliance challenges
- Threat detection gaps

VALUE PROPOSITIONS:
- Unified security platform
- Real-time threat detection
- Automated compliance

USE CASES:
- Multi-cloud security
- Compliance automation
- Threat response

CONTENT THEMES: Cloud Security, Compliance, Threat Detection

COMPETITORS TO DIFFERENTIATE FROM: Competitor A, Competitor B

SYSTEM INSTRUCTIONS:
Focus on practical, actionable advice. Include real-world examples.

COMPANY KNOWLEDGE BASE:
- Founded in 2015
- Serves Fortune 500 companies
- ISO 27001 certified

CONTENT WRITING INSTRUCTIONS:
Use conversational tone. Include statistics. Add case studies.

ARTICLE REQUIREMENTS:
- Target language: en
- Write in professional tone
- Focus on providing genuine value to readers
- Include specific examples and actionable insights
- Structure with clear headings and subheadings
- Aim for 1,500-2,500 words
- Include introduction, main sections, and conclusion
- Make it engaging and informative

CRITICAL CITATION REQUIREMENTS:
- MANDATORY: Include citations in 70%+ of paragraphs (minimum 2 citations per paragraph)
- Use natural attribution format: "according to [Source Name]", "based on [Study Name]", "[Expert Name] reports that"
- Combine with academic format for key statistics: "According to Gartner [1]", "HubSpot research shows [2]"
- Target 8-12 total citations for optimal balance of authority and performance
- Cite statistics, studies, expert opinions, and industry data
- Every major claim must be backed by a credible source

SECTION HEADER REQUIREMENTS:
- MANDATORY: Include 2+ question-format section headers
- Examples: "What is...", "How does...", "Why should...", "When can..."
- Mix question headers with declarative headers for variety
- Question headers improve content discoverability

CONVERSATIONAL TONE REQUIREMENTS:
- Use conversational language throughout ("you", "your", direct address)
- Include rhetorical questions to engage readers
- Use transitional phrases like "Let's explore...", "Consider this...", "Here's why..."
- Write as if speaking directly to the reader

IMPORTANT GUIDELINES:
- Write from an authoritative, knowledgeable perspective
- Include relevant statistics and data when possible
- Reference industry best practices
- Provide actionable takeaways for readers
- Ensure content is original and valuable
- Optimize for search engines while prioritizing reader value

Please write the complete article now.
```

---

## 🔍 Current Company Context Fields (openblog)

### Required Fields
- `company_url` (required)

### Optional Fields - Company Information
- `company_name`
- `industry`
- `description`

### Optional Fields - Products & Services
- `products_services` (List[str])
- `target_audience`

### Optional Fields - Competitive Context
- `competitors` (List[str])
- `brand_tone`

### Optional Fields - Business Context
- `pain_points` (List[str])
- `value_propositions` (List[str])
- `use_cases` (List[str])
- `content_themes` (List[str])

### Optional Fields - Content Guidelines
- `system_instructions`
- `client_knowledge_base` (List[str])
- `content_instructions`

---

## 🔍 OpenContext Fields (from README)

Based on the README, opencontext extracts:
- `company_name`
- `company_url`
- `industry`
- `description`
- `products` (not `products_services`)
- `target_audience`
- `competitors`
- `tone` (not `brand_tone`)
- `pain_points`
- `value_propositions`
- `use_cases`
- `content_themes`

**Missing in opencontext:**
- `system_instructions`
- `client_knowledge_base`
- `content_instructions`

**Field name differences:**
- `products` vs `products_services`
- `tone` vs `brand_tone`

---

## ⚠️ Issues Found

### 1. Word Count Mismatch
- **Stage 1 prompt says:** "Aim for 1,500-2,500 words"
- **Stage 2 system instruction says:** "Minimum: 2,500 words, Target: 3,000-4,000 words"
- **Issue:** Conflicting requirements

### 2. String Manipulation
- **Location:** `company_context.py` line 136
- **Code:** `items = [item.strip() for item in value.replace('\n', ',').split(',') if item.strip()]`
- **Purpose:** Input normalization (converting strings to lists)
- **Question:** Should this be AI-only or acceptable for input normalization?

### 3. Field Name Differences with OpenContext
- `products` vs `products_services`
- `tone` vs `brand_tone`
- **Question:** Should we align field names with opencontext?

---

## ✅ What's Good

1. ✅ No regex usage
2. ✅ Clean, simple structure
3. ✅ Proper validation
4. ✅ Good logging
5. ✅ Flexible (all fields optional except company_url)
6. ✅ Comprehensive prompt template

---

## 📝 Recommendations

1. **Fix word count mismatch:** Update Stage 1 prompt to match Stage 2 (2,500-4,000 words)
2. **Align with opencontext:** Consider renaming fields to match opencontext schema
3. **String manipulation:** Keep as-is for input normalization (acceptable)

