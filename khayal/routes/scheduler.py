"""Scheduler endpoint for daily summaries"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database import KhayalDatabase
from summary_generator import SummaryGenerator
from khayal.config import get_config
from groq import Groq

config_class = get_config()
config = config_class()

scheduler_bp = Blueprint('scheduler', __name__)

db = KhayalDatabase(config.SQLITE_PATH if not config.USE_POSTGRES else None)


@scheduler_bp.route("/trigger-summaries", methods=["POST"])
def trigger_summaries():
    """
    Endpoint to trigger daily summaries
    Called by GitHub Actions at 10 PM IST
    """
    try:
        # Verify secret token
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f'Bearer {config.SCHEDULER_SECRET}':
            print("❌ Unauthorized summary trigger attempt")
            return jsonify({'error': 'Unauthorized'}), 401
        
        print(f"\n{'='*60}")
        print(f"🌙 DAILY SUMMARY TRIGGER [{datetime.now()}]")
        print(f"{'='*60}\n")
        
        # Initialize summary generator
        groq_client = Groq(api_key=config.GROQ_API_KEY)
        summary_gen = SummaryGenerator(db, groq_client)
        results = summary_gen.send_all_summaries()
        
        print(f"\n✅ Summaries sent to {len(results)} users")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'message': 'Summaries sent successfully',
            'users_count': len(results),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error sending summaries: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
