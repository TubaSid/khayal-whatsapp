"""
Configuration management for Khayal
Loads environment variables and provides app configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask
    DEBUG = False
    TESTING = False
    
    # WhatsApp
    PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "khayal_webhook_secret_2025")
    
    # Groq AI
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE = 0.9
    GROQ_MAX_TOKENS = 200
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    SQLITE_PATH = "khayal.db"
    USE_POSTGRES = DATABASE_URL is not None
    
    # Scheduler
    SCHEDULER_SECRET = os.getenv("SCHEDULER_SECRET")
    
    # Server
    PORT = int(os.getenv("PORT", 5000))
    HOST = "0.0.0.0"


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration (Render)"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLITE_PATH = "khayal_test.db"


def get_config():
    """Get appropriate config based on environment"""
    env = os.getenv("FLASK_ENV", "production").lower()
    
    if env == "development":
        return DevelopmentConfig
    elif env == "testing":
        return TestingConfig
    else:
        return ProductionConfig
