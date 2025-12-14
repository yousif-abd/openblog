# Prompt Structure Research - Section Ordering Best Practices

**Date:** December 14, 2025  
**Purpose:** Research on optimal prompt section ordering before restructuring Stage 2 prompt

---

## 🔍 Research Findings

### Industry Standard: Context → Task → Output

**Most Common Structure (Industry Best Practice):**
1. **Context** - Background information, situation, role
2. **Task** - Specific action or objective
3. **Output** - Desired format/structure

**Why it's the standard:**
- ✅ Provides background first (AI understands scenario)
- ✅ Then defines what to do (clear directive)
- ✅ Finally specifies how to format (output expectations)
- ✅ Logical flow: Understand → Act → Format
- ✅ Recommended by OpenAI, Google, and major AI platforms
- ✅ Works well for most use cases

**Sources:**
- OpenAI prompt engineering best practices
- Google Gemini API documentation
- TechTarget, Atlassian, and other authoritative sources
- Industry consensus across major platforms

---

### Alternative Approach: Output → Task → Input

**User's Mentioned Approach:**
1. **Output** - Desired format/structure FIRST
2. **Task** - Specific action or objective
3. **Input** - Context and background

**Why it might be better:**
- ✅ Sets expectations early (AI knows format from start)
- ✅ Helps AI structure thinking around output format
- ✅ Reduces ambiguity about what's expected
- ✅ AI can filter/process input based on output requirements

**Research Support:**
- Some practitioners advocate this sequence
- Particularly effective for complex, structured outputs
- Guides AI's focus towards end goal from outset

---

### START Framework

**Structure:**
1. **S**ituation (Context)
2. **T**ask
3. **A**ttention points (audience, tone, style)
4. **R**ole
5. **T**ype of output

**Note:** Still puts output last, but emphasizes attention points (style/formatting rules) before output.

---

### SPOCK Framework

**Structure:**
1. **S**pecificity
2. **P**ersona (Role)
3. **O**utput (Format)
4. **C**ontext
5. **K**nowledge

**Note:** Puts Output (#3) relatively early, before Context (#4).

---

## 📊 Current Stage 2 Prompt Structure

**Current Order:**
1. Role/Context ("You are an expert...")
2. HTML Structure Rules
3. Format Rules
4. Citation Rules
5. Conversational Tone
6. Writing Style Requirements
7. E-E-A-T Requirements
8. Paragraph Content Requirement
9. Brand Protection Rules
10. Sources Field Rules
11. Punctuation Rules
12. **OUTPUT FORMAT (JSON Structure)** ← Currently #12!
13. Important Output Rules (PAA/FAQ separation)
14. HTML Validation Checklist
15. Lists Requirements
16. Section Variety Requirements
17. Main Prompt (Task/Input)

**Problem:** Output format is buried deep (#12), after many formatting rules.

---

## 💡 Recommended Restructure

### Option 1: Output → Task → Input (User's Suggestion)

**New Order:**
1. **OUTPUT FORMAT (JSON Structure)** ← Move to #1
2. Important Output Rules (PAA/FAQ separation)
3. **Role** ("You are an expert...")
4. **Task** (Main prompt - what to write about)
5. HTML Structure Rules
6. Format Rules
7. Citation Rules
8. Conversational Tone
9. Writing Style Requirements
10. E-E-A-T Requirements
11. Paragraph Content Requirement
12. Brand Protection Rules
13. Sources Field Rules
14. Punctuation Rules
15. HTML Validation Checklist
16. Lists Requirements
17. Section Variety Requirements

**Pros:**
- ✅ AI knows output format immediately
- ✅ Can structure all thinking around JSON format
- ✅ Reduces confusion about what's expected
- ✅ Formatting rules become "how to fill the JSON" rather than abstract rules

**Cons:**
- ⚠️ Might feel backwards (output before context)
- ⚠️ Need to reference JSON structure in later rules

---

### Option 2: Hybrid - Output Early, Then Context → Task

**New Order:**
1. **Role** ("You are an expert...")
2. **OUTPUT FORMAT (JSON Structure)** ← Move to #2
3. Important Output Rules (PAA/FAQ separation)
4. HTML Structure Rules (how to format JSON fields)
5. Format Rules
6. Citation Rules
7. Conversational Tone
8. Writing Style Requirements
9. E-E-A-T Requirements
10. Paragraph Content Requirement
11. Brand Protection Rules
12. Sources Field Rules
13. Punctuation Rules
14. HTML Validation Checklist
15. Lists Requirements
16. Section Variety Requirements
17. **Task** (Main prompt - what to write about)

**Pros:**
- ✅ Keeps role first (establishes identity)
- ✅ Output format early (#2) but not first
- ✅ All formatting rules reference the JSON structure
- ✅ Task comes last (what to write about)

**Cons:**
- ⚠️ Still not "Output → Task → Input" order

---

### Option 3: Output → Rules → Task (Most Logical)

**New Order:**
1. **OUTPUT FORMAT (JSON Structure)** ← #1
2. Important Output Rules (PAA/FAQ separation)
3. **Role** ("You are an expert...")
4. HTML Structure Rules (how to format JSON fields)
5. Format Rules
6. Citation Rules
7. Conversational Tone
8. Writing Style Requirements
9. E-E-A-T Requirements
10. Paragraph Content Requirement
11. Brand Protection Rules
12. Sources Field Rules
13. Punctuation Rules
14. HTML Validation Checklist
15. Lists Requirements
16. Section Variety Requirements
17. **Task** (Main prompt - what to write about)

**Pros:**
- ✅ Output format FIRST (knows what to produce)
- ✅ All rules reference the JSON structure
- ✅ Task comes last (what to write about)
- ✅ Logical flow: Format → Rules → Content

**Cons:**
- ⚠️ Role comes after output format (might feel odd)

---

## 🎯 Industry Standard vs. Alternative

### Industry Standard: Context → Task → Output

**Why it's standard:**
- ✅ Logical flow: Understand → Act → Format
- ✅ AI processes information sequentially
- ✅ Works well for most use cases
- ✅ Recommended by major AI platforms

**Structure:**
```
1. Role/Context ("You are an expert...")
2. Task ("Write about cloud security...")
3. Output Format (JSON structure)
4. Rules (how to format)
```

### Alternative: Output → Rules → Task

**When it might be better:**
- ✅ Complex structured outputs (JSON, XML, tables)
- ✅ When output format is critical
- ✅ When rules reference output structure
- ✅ Reduces ambiguity about format

**Structure:**
```
1. Output Format (JSON structure)
2. Rules (how to format JSON fields)
3. Role/Context ("You are an expert...")
4. Task ("Write about cloud security...")
```

## 💡 Recommendation for Our Use Case

**Hybrid Approach: Follow Industry Standard with Output Early**

**Reasoning:**
1. **Industry Standard** - Context → Task → Output is proven
2. **But** - For structured JSON outputs, output format should come early (#2-3, not #12)
3. **Best of Both** - Keep logical flow but prioritize output format visibility

**Recommended Structure:**
```
1. Role/Context ("You are an expert...")
2. OUTPUT FORMAT (JSON Structure) ← Move from #12 to #2
3. Important Output Rules (PAA/FAQ separation)
4. Task (Main prompt - what to write about)
5. HTML Structure Rules (how to format JSON fields)
6. Format Rules
7. Citation Rules
... (rest of rules)
```

**Why this works:**
- ✅ Follows industry standard (Context → Task → Output)
- ✅ Output format is early (#2) but not first
- ✅ All rules can reference JSON structure
- ✅ Task comes after format is understood
- ✅ Maintains logical flow

---

## 📝 Key Insights

1. **Output-first approaches** are gaining traction for structured outputs
2. **JSON/structured outputs** benefit especially from format-first prompts
3. **Current structure** buries output format too deep (#12 of 17)
4. **Moving output format to #1 or #2** would significantly improve clarity

---

## ⚠️ Considerations

- **System Instruction vs Main Prompt:** Our prompt has two parts (system instruction + main prompt)
- **Gemini API:** System instruction is separate parameter, so order matters less for API
- **But:** For clarity and AI comprehension, output format should still come early

---

## 🔄 Next Steps

1. ✅ Research complete
2. ⏳ Wait for user decision on which approach
3. ⏳ Restructure prompt accordingly
4. ⏳ Test to verify improvement

