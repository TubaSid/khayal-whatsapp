# Khayal v4 - Restructured Codebase Guide

## Overview

Your codebase has been restructured from a monolithic `whatsapp_webhook_v4.py` into a professional Python package with proper separation of concerns. The new structure is:

```
khayal/
├── core/              # Business logic (crisis detection, mood analysis, memory, onboarding)
├── database/          # Data layer (models, ORM interactions)
├── routes/            # Flask blueprints (webhook, health, scheduler, admin)
├── utils/             # Constants, logging, helpers
├── whatsapp/          # WhatsApp API client wrapper
├── app.py             # Flask app factory
└── config.py          # Configuration management
```

## File Migration Map

| Old File | New Location | Purpose |
|----------|--------------|---------|
| `whatsapp_webhook_v4.py` | `main.py` + `khayal/app.py` + `khayal/routes/` | Entry point, app factory, and route handlers |
| `crisis_detector.py` | `khayal/core/crisis.py` | Crisis detection logic |
| `mood_analyzer.py` | `khayal/core/mood.py` | Mood analysis logic |
| `semantic_memory.py` | `khayal/core/memory.py` | Memory management |
| `onboarding.py` | `khayal/core/onboarding.py` | User onboarding |
| `database.py` | `khayal/database/models.py` | Database models and ORM |
| Constants/System Prompts | `khayal/utils/constants.py` | Centralized constants |

## Running the Application

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the application
python main.py
```

### Production (Render)
The app is automatically deployed when you push to the main branch. The `render.yaml` file handles the configuration.

## Project Structure

### 1. **khayal/config.py**
Manages all configuration (API keys, database settings, server config).
- `Config`: Base configuration
- `DevelopmentConfig`: Dev-specific settings
- `ProductionConfig`: Render-ready settings
- `get_config()`: Returns appropriate config class based on environment

### 2. **khayal/app.py**
Flask application factory using the factory pattern.
- `create_app(config_class)`: Creates and configures Flask app
- Registers all blueprints
- Can be used in different contexts (testing, production, etc.)

### 3. **khayal/core/** - Business Logic
- `crisis.py`: Crisis detection using LLM + keyword matching
- `mood.py`: Mood analysis from user messages
- `memory.py`: Semantic memory for user patterns
- `onboarding.py`: Professional user onboarding workflow

Each module wraps the original implementation for backward compatibility.

### 4. **khayal/database/models.py**
- `KhayalDatabase`: Main database class
- Supports SQLite (default) and PostgreSQL (production)
- Manages user profiles, conversations, moods, patterns

### 5. **khayal/whatsapp/client.py**
- `WhatsAppClient`: WhatsApp Graph API wrapper
- `send_message()`: Send text messages
- `mark_message_read()`: Mark messages as read

### 6. **khayal/routes/** - API Endpoints
- `webhook.py` (`/webhook`): Main WhatsApp message handler
- `health.py` (`/health`, `/stats`): Health checks and statistics
- `scheduler.py` (`/trigger-summaries`): Daily summary trigger
- `admin.py` (`/`): Home and admin page

### 7. **khayal/utils/** - Utilities
- `constants.py`: System prompts, Groq config, API constants
- `logger.py`: Centralized logging setup

## Key Changes from Old Structure

### ✅ Benefits of Restructuring

1. **Modularity**: Each module has a single responsibility
2. **Testability**: Individual components can be tested in isolation
3. **Maintainability**: Clear imports and dependencies
4. **Scalability**: Easy to add new features or modules
5. **Configuration Management**: Centralized config for different environments
6. **Factory Pattern**: Flask app can be created for testing or different contexts

### ⚠️ Backward Compatibility

Original module files (`crisis_detector.py`, `mood_analyzer.py`, etc.) are still present. New core modules wrap these for compatibility. You can gradually migrate them.

## Usage Examples

### In Code: Import from Package
```python
# Instead of:
# from mood_analyzer import MoodAnalyzer

# Use:
from khayal.core import MoodAnalyzer
from khayal.database import KhayalDatabase
from khayal.whatsapp import WhatsAppClient
from khayal.utils import KHAYAL_SYSTEM_INSTRUCTION, setup_logger
```

### Creating App for Testing
```python
from khayal import create_app
from khayal.config import DevelopmentConfig

app = create_app(DevelopmentConfig)
with app.test_client() as client:
    response = client.get('/health')
    print(response.json)
```

### Environment-Based Configuration
```python
# config.py handles this automatically
from khayal.config import get_config

config = get_config()  # Returns appropriate config based on environment
print(config.GROQ_API_KEY)
print(config.USE_POSTGRES)  # True if DATABASE_URL is set
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```
# WhatsApp
PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_token

# Groq AI
GROQ_API_KEY=your_groq_key

# Webhook verification
WEBHOOK_VERIFY_TOKEN=khayal_webhook_secret_2025

# Scheduler
SCHEDULER_SECRET=your_scheduler_secret

# Database (optional, uses SQLite if not provided)
DATABASE_URL=postgresql://user:pass@localhost/khayal_db

# Server
PORT=5000
```

## API Endpoints

### Main Webhook
```
POST /webhook
- Receives WhatsApp messages
- Runs crisis detection, mood analysis, onboarding
- Returns response to send back to user
```

### Health Check
```
GET /health
- Returns service status and feature list
```

### Statistics
```
GET /stats/<phone_number>
- Returns user stats (moods, patterns, etc.)
```

### Trigger Summaries
```
POST /trigger-summaries
- Header: X-Scheduler-Secret
- Generates and sends daily summaries
- Used by GitHub Actions scheduler
```

### Home
```
GET /
- Shows service status and available endpoints
```

## Next Steps for Complete Migration

1. **Gradual Module Migration**: Move logic from old files to `khayal/core/` modules
2. **Add Tests**: Create `tests/` directory with unit tests for each module
3. **Add Error Handling**: Implement proper exception handling in routes
4. **Add Logging**: Use `khayal.utils.logger` throughout for better debugging
5. **Database Abstraction**: Create a service layer in `khayal/services/` if needed
6. **API Documentation**: Add OpenAPI/Swagger documentation

## Debugging

Enable debug logging by setting:
```python
from khayal.utils import setup_logger
logger = setup_logger(__name__, log_file="debug.log")
```

## Deployment

The app is configured for **Render**:
1. Push to `main` branch
2. Render automatically deploys using `render.yaml`
3. Check logs in Render dashboard

## Questions?

Refer to specific module docstrings or this guide for more details.

---

**Khayal v4** - Built with care for mental health support 🌙
