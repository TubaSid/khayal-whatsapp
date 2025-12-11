"""Admin endpoints"""

from flask import Blueprint

admin_bp = Blueprint('admin', __name__)


@admin_bp.route("/", methods=["GET"])
def home():
    """Home endpoint"""
    return """
    <h1>🌙 Khayal v4 - Production</h1>
    <p><strong>Status:</strong> Online</p>
    <p><strong>Features:</strong></p>
    <ul>
        <li>✅ Crisis detection & resources</li>
        <li>✅ Professional onboarding</li>
        <li>✅ Mood analysis</li>
        <li>✅ Pattern detection</li>
        <li>✅ Semantic memory</li>
        <li>✅ Daily 10 PM summaries (via GitHub Actions)</li>
    </ul>
    <p><strong>Endpoints:</strong></p>
    <ul>
        <li><code>/webhook</code> - WhatsApp webhook</li>
        <li><code>/health</code> - Health check</li>
        <li><code>/trigger-summaries</code> - Trigger daily summaries (POST only, requires auth)</li>
        <li><code>/stats/&lt;phone_number&gt;</code> - User statistics</li>
    </ul>
    """
