"""
Approach Selector for Legal Article Generation.

Routes between two generation strategies:
- Approach A (Direct Paraphrasing): Cite specific decisions, heavily paraphrase content
- Approach B (Context Synthesis): Synthesize across all decisions into thematic sections

Both approaches receive the same enriched legal context from Stage 1 but produce
articles with fundamentally different structures.
"""

import logging
from enum import Enum
from typing import Dict, Any

logger = logging.getLogger(__name__)


class GenerationApproach(str, Enum):
    """Legal article generation approach for A/B testing."""
    DIRECT_PARAPHRASE = "approach_a"
    CONTEXT_SYNTHESIS = "approach_b"


# Approach A: Direct Paraphrasing instruction block
APPROACH_A_INSTRUCTIONS = """
=== APPROACH: DIRECT PARAPHRASING ===
For each section that references a court decision:
1. Cite the decision as: (Gericht, Az. Aktenzeichen)
2. Explain the legal principle in YOUR OWN words
3. NEVER copy more than 5 consecutive words from the Leitsatz or Volltext
4. Use a concrete real-world example to illustrate the principle
5. Short direct quotes (max 1 sentence) MUST be in quotation marks with citation

COPYRIGHT RULES:
- All Beck-Online content is copyrighted — you MUST reformulate
- Direct quotes longer than one sentence are FORBIDDEN
- Rephrase the court's reasoning, do not reproduce it
"""

# Approach B: Context Synthesis instruction block
APPROACH_B_INSTRUCTIONS = """
=== APPROACH: BROADER CONTEXT SYNTHESIS ===
Instead of structuring sections around individual court decisions:
1. Identify 4-6 THEMES from the research (e.g., Voraussetzungen, Rechtsfolgen, Praxistipps)
2. Each section covers a THEME, not a single case
3. Weave 2-3 court decisions into each thematic section
4. Build an overarching narrative: what is the current state of the law?
5. Cite decisions inline as (Gericht, Az. Aktenzeichen) — do NOT dedicate entire sections to single decisions
6. Use commentary insights to provide doctrinal context
7. The article should read like a Zeitschrift overview, not a case reporter

STRUCTURE GUIDANCE:
- Section 1: Introduction to the legal landscape (statutory basis)
- Sections 2-4: Thematic deep-dives with cross-referenced decisions
- Section 5: Practical implications / what readers should do
- Section 6: Outlook / current trends in case law
"""


def get_approach_instructions(approach: str) -> str:
    """
    Get the generation instructions for the selected approach.

    Args:
        approach: 'approach_a' or 'approach_b'

    Returns:
        Instruction string to inject into the generation prompt
    """
    if approach == GenerationApproach.CONTEXT_SYNTHESIS.value:
        logger.info("Using Approach B: Context Synthesis")
        return APPROACH_B_INSTRUCTIONS
    else:
        logger.info("Using Approach A: Direct Paraphrasing")
        return APPROACH_A_INSTRUCTIONS


def get_approach_metadata(approach: str) -> Dict[str, Any]:
    """
    Get metadata about the selected approach for article output.

    Args:
        approach: 'approach_a' or 'approach_b'

    Returns:
        Dict with approach metadata to include in article output
    """
    if approach == GenerationApproach.CONTEXT_SYNTHESIS.value:
        return {
            "generation_approach": "approach_b",
            "approach_name": "Context Synthesis",
            "approach_description": "Thematic sections synthesizing multiple court decisions",
        }
    else:
        return {
            "generation_approach": "approach_a",
            "approach_name": "Direct Paraphrasing",
            "approach_description": "Decision-anchored sections with heavy paraphrasing",
        }
