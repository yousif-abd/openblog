# OpenContext Country/Language Detection - Implementation Guide

## Overview
This document outlines the changes needed to add country, language, and location detection to opencontext.

## Changes Required

### 1. Update `src/lib/types.ts`

Add three new fields to `AnalysisResponse`:

```typescript
export interface AnalysisResponse {
  company_name: string
  company_url: string
  industry: string
  description: string
  products: string[]
  target_audience: string
  competitors: string[]
  tone: string
  pain_points: string[]
  value_propositions: string[]
  use_cases: string[]
  content_themes: string[]
  // NEW FIELDS:
  country: string // Primary country (e.g., "Germany", "United States")
  language: string // Primary language code (e.g., "en", "de", "fr")
  location?: string // Optional: City/country (e.g., "Hamburg, Germany")
}
```

### 2. Update `src/app/api/analyze/route.ts`

#### 2.1 Update the Prompt

Add geographic and language detection instructions to the prompt:

```typescript
const prompt = `You are an expert business analyst. Analyze the company website at ${normalizedUrl} and extract comprehensive company context.

Visit the URL and carefully analyze all available information to provide:

1. Company basics (name, website, industry)
2. Products/services offered
3. Target audience and ideal customers
4. Brand voice and tone
5. Key value propositions
6. Customer pain points they address
7. Common use cases
8. Content themes they focus on
9. Main competitors (based on industry and offerings)
10. Geographic context:
    - Primary country (detect from domain TLD, content, location mentions, legal info)
    - Primary language (detect from HTML lang attribute, content language, domain)
    - Location (city/country if mentioned, e.g., "Hamburg, Germany")

For country detection:
- Check domain TLD (.de = Germany, .fr = France, .co.uk = UK, .com = analyze content)
- Look for location mentions in content (addresses, "based in", "located in")
- Check legal/contact pages for country information
- Use ISO country names (e.g., "Germany", "United States", "France")

For language detection:
- Check HTML lang attribute if accessible
- Analyze primary content language
- Use ISO 639-1 language codes (e.g., "en", "de", "fr", "es")
- Default to "en" if unclear

Return ONLY valid JSON in exactly this format:
{
  "company_name": "Official company name",
  "company_url": "Normalized company website URL", 
  "industry": "Primary industry category",
  "description": "Clear 2-3 sentence company description",
  "products": ["Product 1", "Product 2"],
  "target_audience": "Ideal customer profile description",
  "competitors": ["Competitor 1", "Competitor 2"],
  "tone": "Brand voice description",
  "pain_points": ["Pain point 1", "Pain point 2"],
  "value_propositions": ["Value prop 1", "Value prop 2"], 
  "use_cases": ["Use case 1", "Use case 2"],
  "content_themes": ["Theme 1", "Theme 2"],
  "country": "Primary country name (ISO format, e.g., 'Germany', 'United States')",
  "language": "Primary language code (ISO 639-1, e.g., 'en', 'de', 'fr')",
  "location": "City, Country (if available, e.g., 'Hamburg, Germany')"
}

Analyze: ${normalizedUrl}`
```

#### 2.2 Add TLD Fallback Logic

After parsing the JSON response, add fallback logic for country and language:

```typescript
// Parse and validate JSON response
const data = JSON.parse(responseText)

// Ensure country and language are always present (fallback if not detected)
if (!data.country) {
  // Try to infer from domain TLD
  const domain = new URL(normalizedUrl).hostname
  const tldMap: Record<string, string> = {
    '.de': 'Germany',
    '.fr': 'France',
    '.uk': 'United Kingdom',
    '.co.uk': 'United Kingdom',
    '.it': 'Italy',
    '.es': 'Spain',
    '.nl': 'Netherlands',
    '.at': 'Austria',
    '.ch': 'Switzerland',
    '.be': 'Belgium',
    '.pl': 'Poland',
    '.se': 'Sweden',
    '.no': 'Norway',
    '.dk': 'Denmark',
    '.fi': 'Finland',
  }
  
  for (const [tld, country] of Object.entries(tldMap)) {
    if (domain.endsWith(tld)) {
      data.country = country
      break
    }
  }
  
  // Default fallback
  if (!data.country) {
    data.country = 'Unknown'
  }
}

if (!data.language) {
  // Try to infer from domain TLD
  const domain = new URL(normalizedUrl).hostname
  const tldLangMap: Record<string, string> = {
    '.de': 'de',
    '.fr': 'fr',
    '.it': 'it',
    '.es': 'es',
    '.nl': 'nl',
    '.at': 'de',
    '.ch': 'de', // Default to German for Switzerland
    '.be': 'nl', // Default to Dutch for Belgium
    '.pl': 'pl',
    '.se': 'sv',
    '.no': 'no',
    '.dk': 'da',
    '.fi': 'fi',
  }
  
  for (const [tld, lang] of Object.entries(tldLangMap)) {
    if (domain.endsWith(tld)) {
      data.language = lang
      break
    }
  }
  
  // Default fallback
  if (!data.language) {
    data.language = 'en'
  }
}

return NextResponse.json(data)
```

## Detection Methods

### Country Detection Priority:
1. **Gemini Analysis** - AI extracts from content, legal pages, addresses
2. **TLD Analysis** - Domain extension (.de, .fr, etc.)
3. **Fallback** - "Unknown" if neither method works

### Language Detection Priority:
1. **Gemini Analysis** - HTML lang attribute, content language analysis
2. **TLD Analysis** - Domain extension mapping
3. **Fallback** - "en" (English) if unclear

## Example Output

After these changes, opencontext will return:

```json
{
  "company_name": "SCAILE",
  "company_url": "https://scaile.tech",
  "industry": "AI-powered go-to-market (GTM) solutions",
  "description": "...",
  "products": ["AI Visibility Engine", "AI GTM machines"],
  "target_audience": "...",
  "competitors": [],
  "tone": "Professional, innovative, data-driven",
  "pain_points": [...],
  "value_propositions": [...],
  "use_cases": [...],
  "content_themes": [...],
  "country": "Germany",
  "language": "en",
  "location": "Hamburg, Germany"
}
```

## Testing

Test with various domains:
- `scaile.tech` → Should detect: country="Germany" (from content), language="en"
- `example.de` → Should detect: country="Germany", language="de" (from TLD)
- `example.fr` → Should detect: country="France", language="fr" (from TLD)
- `example.com` → Should detect: country from content, language="en" (default)

## Next Steps

1. Apply these changes to opencontext repository
2. Test with scaile.tech and other domains
3. Update openblog to use the new fields (`country`, `language`, `location`)

