"""Health check and stats endpoints"""

from flask import Blueprint, jsonify
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database import KhayalDatabase
from semantic_memory import SemanticMemory
from onboarding import OnboardingManager
from khayal.config import get_config

config_class = get_config()
config = config_class()

health_bp = Blueprint('health', __name__)

db = KhayalDatabase(config.SQLITE_PATH if not config.USE_POSTGRES else None)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Khayal v4 Production",
        "features": [
            "crisis_detection",
            "onboarding",
            "mood_analysis",
            "pattern_detection",
            "semantic_memory",
            "daily_summaries"
        ],
        "timestamp": datetime.now().isoformat()
    }), 200


@health_bp.route("/stats/<phone_number>", methods=["GET"])
def get_user_stats(phone_number):
    """Get user statistics"""
    try:
        from groq import Groq
        
        groq_client = Groq(api_key=config.GROQ_API_KEY)
        semantic_memory = SemanticMemory(db, groq_client)
        onboarding_manager = OnboardingManager(db)
        
        user_id = db.get_or_create_user(phone_number)
        stats = db.get_user_stats(user_id)
        patterns = semantic_memory.detect_patterns(user_id, days=7)
        prefs = onboarding_manager.get_preferences(user_id)
        
        return jsonify({
            "user_id": user_id,
            "stats": stats,
            "patterns": patterns,
            "preferences": prefs
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
