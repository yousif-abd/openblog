# Legal Content Engine - Project Context

## Overview

This is a specialized fork of openblog for **Braun & Kollegen**, a German law firm. The goal is to enhance the existing blog generation pipeline to produce legally accurate, defensible content for German law.

**Client Website:** https://www.braun-kollegen.de/

## Problem Statement

The current openblog pipeline uses Google Search grounding for sourcing, which is insufficient for legal content because:

- German law requires citing specific statutes (§§), court decisions, and established commentary
- Legal claims must be traceable to authoritative sources (not general web results)
- Legal reasoning requires referencing precedent and Beck-Onlineprudence
- Incorrect legal statements pose professional liability risks for the firm

## Project Objective

Enhance openblog so that all major legal claims and key information are grounded in authoritative German legal sources, specifically:

- Court decisions from beck-online.beck.de (BGH, OLG, etc.)
- Statute text from official sources
- Standard German legal citation format

## Architecture Approach

We are implementing a **three-layer hybrid approach**:

### Layer 1: Court Decisions via browserUse + Beck-Online
- Use browserUse (browser automation) to navigate beck-online.beck.de
- Extract relevant court decisions for each article topic
- Capture: Gericht, Aktenzeichen, Datum, Leitsatz, relevante Normen

### Layer 2: Statute Text via dejure.org
- Scrape statute text from dejure.org (free, no authentication)
- Get full text of relevant §§ cited in court decisions
- Provide direct links for citations

### Layer 3: Verification
- Cross-check all legal claims in generated content against retrieved sources
- Flag or revise unsupported claims before publishing

## Pipeline Modifications

The existing pipeline stages remain, with new stages inserted:

```
Stage 1 (Context)        → Existing: Company info, sitemap, voice persona
    ↓
Stage 1.5 (Legal Research) → NEW: browserUse + Beck-Online, dejure.org
    ↓
Stage 2 (Generation)     → Modified: Legal-specific prompts, citation requirements
    ↓
Stage 2.5 (Verification) → NEW: Claim extraction and source matching
    ↓
Stage 3 (Quality)        → Existing: AI phrase fixes
    ↓
Stage 4 (URL Verify)     → Existing: Dead link detection
    ↓
Stage 5 (Links)          → Existing: Internal linking
    ↓
Export                   → Existing: HTML/MD/JSON/PDF
```

## New Components to Build

### Stage 1.5: Legal Research
- **Location:** `stage1/legal_researcher.py`
- **Purpose:** Retrieve relevant legal sources before article generation
- **Inputs:** Article topic, Rechtsgebiet (legal area)
- **Outputs:** LegalContext object with decisions, statutes

### Legal Models
- **Location:** `stage1/legal_models.py`
- **Models needed:**
  - `CourtDecision` - German court decision with full citation details
  - `Statute` - German statute provision with text and reference
  - `LegalContext` - Complete research package for article generation

### Browser Agent for Beck-Online
- **Location:** `stage1/browser_agent.py`
- **Purpose:** Navigate beck-online.beck.de, authenticate, search, extract decisions
- **Technology:** browserUse with Gemini as the LLM (consistent with rest of pipeline)

### Legal Prompts
- **Location:** `stage2/prompts/system_instruction_legal.txt`
- **Location:** `stage2/prompts/user_prompt_legal.txt`
- **Purpose:** Legal-specific generation instructions requiring citations

### Stage 2.5: Legal Verification
- **Location:** `stage2/legal_verifier.py`
- **Purpose:** Extract legal claims from generated content, match to sources
- **Output:** Verification report with supported/unsupported claims

### Schema Extensions
- **Location:** `shared/models.py`
- **New fields on ArticleOutput:**
  - `rechtliche_grundlagen` - List of legal sources cited
  - `rechtsgebiet` - Legal area of the article
  - `stand_der_rechtsprechung` - Date of legal research

## Key Files to Understand

Before making changes, familiarize yourself with:

- `run_pipeline.py` - Main orchestrator, shows how stages connect
- `stage1/stage_1.py` - Context gathering stage
- `stage2/blog_writer.py` - Article generation logic
- `stage2/prompts/` - Generation prompt templates
- `shared/models.py` - ArticleOutput schema
- `shared/gemini_client.py` - How Gemini API calls work

## German Legal Citation Format

When generating or verifying content, use standard German legal citation:

**Statutes:**
- § 623 BGB (single paragraph)
- §§ 623, 626 BGB (multiple paragraphs)
- § 1 Abs. 1 S. 1 KSchG (paragraph, subsection, sentence)

**Court Decisions:**
- BGH, Urt. v. 12.05.2024 – 6 AZR 123/23
- BAG, Beschl. v. 15.03.2024 – 2 AZR 456/23
- OLG München, Urt. v. 01.02.2024 – 7 U 789/23

## Legal Areas (Rechtsgebiete)

Priority areas to be confirmed with client, likely include:

- Arbeitsrecht (Employment Law)
- Mietrecht (Tenancy Law)
- Vertragsrecht (Contract Law)
- Familienrecht (Family Law)
- Erbrecht (Inheritance Law)

## Language

All generated content will be in **German** for a German audience. The pipeline should:

- Use German legal terminology correctly
- Follow German legal writing conventions
- Include appropriate disclaimers ("Dies ist keine Rechtsberatung...")

## Testing Approach

1. Start with a single Rechtsgebiet (e.g., Arbeitsrecht)
2. Test with known topics that have clear legal foundations
3. Verify citations manually against Beck-Online
4. Get lawyer review on sample articles before scaling

## Reference Documents

- `docs/LEGAL_ENGINE_PROPOSAL.md` - Full technical proposal with implementation details
- `CLAUDE.md` - Original openblog architecture documentation

---

## Credentials & Configuration

### Environment Variables

Add these to `.env` file (never commit credentials):

```
# Existing - used for all AI operations including browserUse
GEMINI_API_KEY=

# Legal Engine - beck-online.beck.de
BECK_USERNAME=
BECK_PASSWORD=
```

### beck-online.beck.de Access

- **Status:** Pending
- **URL:** https://www.beck-online.beck.de/
- **Tier/Package:** TBD
- **Rate Limits:** TBD

---

## Current Status

**Phase:** Pre-implementation / Scoping

**Blockers:**
- Awaiting Beck-Online credentials from Simon
- Awaiting confirmation of priority Rechtsgebiete
- Awaiting confirmation of review workflow

**Next Steps:**
1. Receive credentials and access confirmation
2. Build Beck-Online browserUse PoC
3. Create legal models
4. Implement Stage 1.5
5. Modify Stage 2 prompts
6. Implement Stage 2.5 verification
7. Integration testing