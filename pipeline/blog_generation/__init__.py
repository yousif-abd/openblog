"""All 10 workflow stages (0-9)."""

# #region agent log
try: import traceback, os; log_path = '/Users/federicodeponte/openblog/.cursor/debug.log'; os.makedirs(os.path.dirname(log_path), exist_ok=True) if os.path.dirname(log_path) else None; log_file = open(log_path, 'a'); log_file.write(f'{{"sessionId":"debug-session","runId":"import-trace","hypothesisId":"D","location":"blog_generation/__init__.py:3","message":"Starting blog_generation imports","data":{{"timestamp":{__import__("time").time()}}},"timestamp":{int(__import__("time").time()*1000)}}}\n'); log_file.close()
except: pass
# #endregion
from .stage_00_data_fetch import DataFetchStage
from .stage_01_prompt_build import PromptBuildStage
from .stage_02_gemini_call import GeminiCallStage
from .stage_03_quality_refinement import QualityRefinementStage
from .stage_04_citations import CitationsStage
from .stage_05_internal_links import InternalLinksStage
# Stages 6-8 consolidated: ToC and Metadata into Stage 2, FAQ/PAA validation into Stage 3
# #region agent log
try: import traceback, os; log_path = '/Users/federicodeponte/openblog/.cursor/debug.log'; os.makedirs(os.path.dirname(log_path), exist_ok=True) if os.path.dirname(log_path) else None; log_file = open(log_path, 'a'); log_file.write(f'{{"sessionId":"debug-session","runId":"import-trace","hypothesisId":"D","location":"blog_generation/__init__.py:11","message":"About to import stage_06_image","data":{{"timestamp":{__import__("time").time()}}},"timestamp":{int(__import__("time").time()*1000)}}}\n'); log_file.close()
except: pass
# #endregion
from .stage_06_image import ImageStage
# #region agent log
try: import traceback, os; log_path = '/Users/federicodeponte/openblog/.cursor/debug.log'; os.makedirs(os.path.dirname(log_path), exist_ok=True) if os.path.dirname(log_path) else None; log_file = open(log_path, 'a'); log_file.write(f'{{"sessionId":"debug-session","runId":"import-trace","hypothesisId":"D","location":"blog_generation/__init__.py:13","message":"About to import stage_09_storage","data":{{"timestamp":{__import__("time").time()}}},"timestamp":{int(__import__("time").time()*1000)}}}\n'); log_file.close()
except: pass
# #endregion
from .stage_07_similarity_check import HybridSimilarityCheckStage
from .stage_08_cleanup import CleanupStage
from .stage_09_storage import StorageStage
# Stage 13 (Review Iteration) removed - use /refresh endpoint instead

__all__ = [
    "DataFetchStage",
    "PromptBuildStage",
    "GeminiCallStage",
    "QualityRefinementStage",
    "CitationsStage",
    "InternalLinksStage",
    # Stages 6-8 consolidated: ToC and Metadata into Stage 2, FAQ/PAA validation into Stage 3
    "ImageStage",
    "CleanupStage",
    "StorageStage",
    "HybridSimilarityCheckStage",
    # Stage 13 (Review Iteration) removed - use /refresh endpoint instead
]

