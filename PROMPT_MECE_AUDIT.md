# Prompt MECE Audit - Duplication & Contradiction Analysis

## Critical Contradictions Found

### 1. Citation Count Targets (CONTRADICTION)
**Location:** System Instruction vs Main Prompt
- **System Instruction (line 277):** "Minimum 8-12 authoritative citations"
- **System Instruction (line 445):** "Target 12-15 citations"
- **Main Prompt (line 214):** "Target 8-12 total citations"
- **Issue:** Three different targets (8-12, 12-15, 8-12)
- **Fix:** Consolidate to single target: "Target 12-15 citations" (system instruction is authoritative)

### 2. Citation Frequency (CONTRADICTION)
**Location:** System Instruction vs Main Prompt
- **System Instruction (line 438):** "EVERY paragraph MUST include a natural language citation"
- **Main Prompt (line 211):** "Include citations in 70%+ of paragraphs (minimum 2 citations per paragraph)"
- **Issue:** "Every paragraph" vs "70%+" - direct contradiction
- **Fix:** System instruction should be authoritative. Choose one:
  - Option A: "EVERY paragraph MUST include..." (stricter)
  - Option B: "70%+ of paragraphs should include..." (more flexible)
  - Recommendation: Keep "EVERY paragraph" in system instruction, remove from main prompt

### 3. Research Quality Standards (DUPLICATION)
**Location:** System Instruction (appears twice)
- **Line 277:** "Minimum 8-12 authoritative citations"
- **Line 445:** "Target 12-15 citations"
- **Issue:** Same concept stated twice with different numbers
- **Fix:** Remove one, keep "Target 12-15 citations" (more specific)

## Duplications (Non-Contradictory)

### 4. Conversational Tone Requirements (DUPLICATION)
**Location:** System Instruction vs Main Prompt
- **System Instruction (line 463-471):** Detailed requirements with "10+ times", specific phrases
- **Main Prompt (line 224-228):** Generic "Use conversational language throughout"
- **Issue:** Main prompt is redundant, less specific
- **Fix:** Remove from main prompt (system instruction is comprehensive)

### 5. Section Header Requirements (MISSING FROM SYSTEM INSTRUCTION)
**Location:** Main Prompt only
- **Main Prompt (line 218-222):** "MANDATORY: Include 2+ question-format section headers"
- **System Instruction:** Not mentioned
- **Issue:** Important requirement only in main prompt
- **Fix:** Add to system instruction under "Content Quality Requirements"

### 6. Citation Format Instructions (DUPLICATION)
**Location:** System Instruction (appears in multiple places)
- **Line 409-417:** Citation formatting rules (HTML structure)
- **Line 436-452:** Citations (CRITICAL FOR AEO) with patterns
- **Issue:** Some overlap, but different focus (formatting vs patterns)
- **Fix:** Keep both but ensure no contradiction (currently OK)

### 7. General Writing Guidelines (DUPLICATION)
**Location:** Main Prompt
- **Line 230-236:** "IMPORTANT GUIDELINES" section
- **Issue:** Overlaps with system instruction content quality requirements
- **Fix:** Remove generic guidelines from main prompt (system instruction covers this)

## Fixes Applied ✅

### High Priority Fixes (COMPLETED):
1. ✅ **Citation count consolidated:** Removed "8-12" from research quality standards, kept "12-15 citations" as single authoritative target
2. ✅ **Citation frequency resolved:** Kept "EVERY paragraph MUST include" in system instruction, removed conflicting "70%+" from main prompt
3. ✅ **Duplicate citation target removed:** Removed "Minimum 8-12 authoritative citations" from research quality standards

### Medium Priority Fixes (COMPLETED):
4. ✅ **Conversational tone:** Removed from main prompt, kept comprehensive version in system instruction
5. ✅ **Section header requirements:** Added to system instruction under "Content Quality Requirements"
6. ✅ **Generic guidelines:** Removed from main prompt, replaced with reference to system instruction

## Current State (MECE Compliant)

### System Instruction Contains (Authoritative):
- ✅ Research requirements (deep research, source types by industry)
- ✅ Output format (JSON structure)
- ✅ Content formatting rules (HTML, citations, lists)
- ✅ Writing style (conversational tone: 10+ phrases, active voice)
- ✅ Content quality requirements (E-E-A-T, data-driven, section variety)
- ✅ Section header requirements (2+ question-format headers)
- ✅ Citation requirements (EVERY paragraph, target 12-15 citations)

### Main Prompt Contains (Task-Specific):
- ✅ Topic focus
- ✅ Company context
- ✅ Article requirements (language, tone - no word count)
- ✅ Reference to system instruction for detailed requirements
- ✅ No duplication or contradiction

### Low Priority (Keep):
- Citation formatting appears in multiple places but serves different purposes (formatting vs patterns) - OK to keep

## MECE Principle Violations

**Mutually Exclusive:** 
- Citation count has 3 different targets (violates ME)
- Citation frequency has 2 different requirements (violates ME)

**Collectively Exhaustive:**
- Section header requirements missing from system instruction (violates CE)
- Some guidelines only in main prompt, not system instruction (violates CE)

## Proposed Structure (MECE Compliant)

**System Instruction Should Contain:**
- ✅ Research requirements (deep research, source types)
- ✅ Output format (JSON structure)
- ✅ Content formatting rules (HTML, citations, lists)
- ✅ Writing style (conversational tone, active voice)
- ✅ Content quality requirements (E-E-A-T, data-driven, section variety)
- ✅ Section header requirements (ADD THIS)
- ✅ Citation requirements (consolidated, single target)

**Main Prompt Should Contain:**
- ✅ Topic focus
- ✅ Company context
- ✅ Article requirements (language, tone - no word count)
- ✅ Reference to system instruction for detailed requirements
- ❌ Remove: Citation requirements (duplicate)
- ❌ Remove: Conversational tone (duplicate)
- ❌ Remove: Section headers (should be in system instruction)
- ❌ Remove: Generic guidelines (covered in system instruction)

