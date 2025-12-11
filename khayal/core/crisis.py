"""
Crisis Detection Module - Wrapper around crisis_detector.py
Detects mental health crises and provides appropriate resources
"""

import sys
import os
from pathlib import Path

# Import the original crisis detector
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from crisis_detector import CrisisDetector

__all__ = ["CrisisDetector"]
