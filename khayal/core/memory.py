"""
Semantic Memory Module - Wrapper around semantic_memory.py
Manages user memory, patterns, and semantic understanding
"""

import sys
import os
from pathlib import Path

# Import the original semantic memory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from semantic_memory import SemanticMemory

__all__ = ["SemanticMemory"]
