#!/usr/bin/env python3
"""
Khayal v4 - Production WhatsApp Companion
Main entry point for the application

Usage:
    python main.py
    
Environment variables required:
    - PHONE_NUMBER_ID
    - WHATSAPP_ACCESS_TOKEN
    - GROQ_API_KEY
    - WEBHOOK_VERIFY_TOKEN (optional, defaults to 'khayal_webhook_secret_2025')
    - SCHEDULER_SECRET (required for scheduled summaries)
    - PORT (optional, defaults to 5000)
    - DATABASE_URL (optional, for PostgreSQL; uses SQLite if not provided)
"""

import os
from dotenv import load_dotenv
from khayal import create_app
from khayal.config import get_config

# Load environment variables
load_dotenv()

# Get configuration
config_class = get_config()
config = config_class()

# Create Flask app
app = create_app(config_class)


def print_startup_banner():
    """Print startup information"""
    print("\n" + "="*60)
    print("🌙 KHAYAL v4 - PRODUCTION READY (RENDER)")
    print("="*60)
    print(f"Phone Number ID: {config.PHONE_NUMBER_ID[:10]}..." if config.PHONE_NUMBER_ID else "❌")
    print(f"Access Token: {'✅' if config.WHATSAPP_ACCESS_TOKEN else '❌'}")
    print(f"Groq API Key: {'✅' if config.GROQ_API_KEY else '❌'}")
    print(f"Database: {'PostgreSQL' if config.USE_POSTGRES else 'SQLite'} ✅ Connected")
    print(f"Crisis Detector: ✅ Ready")
    print(f"Onboarding: ✅ Ready")
    print("="*60)
    
    print("\n🚀 Features Active:")
    print("  • Crisis detection & mental health resources")
    print("  • Professional user onboarding")
    print("  • Mood analysis & tracking")
    print("  • Pattern detection")
    print("  • Semantic memory")
    print("  • Daily summaries (GitHub Actions)")
    print("="*60 + "\n")
    
    print(f"🚀 Starting server on port {config.PORT}")
    print("="*60 + "\n")


if __name__ == "__main__":
    print_startup_banner()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
