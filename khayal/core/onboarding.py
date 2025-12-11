"""
Onboarding Module - Wrapper around onboarding.py
Manages user onboarding workflow
"""

import sys
import os
from pathlib import Path

# Import the original onboarding manager
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from onboarding import OnboardingManager

__all__ = ["OnboardingManager"]
