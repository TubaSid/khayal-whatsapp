# Khayal Codebase Restructuring Guide

## Overview

The codebase has been restructured from a flat file organization into a professional Python package architecture. This makes the code more maintainable, testable, and scalable.

## New Structure

```
khayal-whatsapp/
├── khayal/                          # Main package
│   ├── __init__.py                  # Package initialization
│   ├── app.py                       # Flask app factory
│   ├── config.py                    # Configuration management
│   ├── core/                        # Business logic
│   │   ├── __init__.py
│   │   ├── mood.py                  # Mood analysis (from mood_analyzer.py)
│   │   ├── memory.py                # Semantic memory (from semantic_memory.py)
│   │   ├── crisis.py                # Crisis detection (from crisis_detector.py)
│   │   └── onboarding.py            # Onboarding (from onboarding.py)
│   ├── database/                    # Data layer
│   │   ├── __init__.py
│   │   └── models.py                # Database models (from database.py)
│   ├── whatsapp/                    # WhatsApp integration
│   │   └── __init__.py              # WhatsApp client
│   ├── utils/                       # Utilities
│   │   ├── __init__.py
│   │   ├── constants.py             # System prompts & constants
│   │   └── logger.py                # Logging
│   └── routes/                      # API endpoints
│       ├── __init__.py
│       ├── webhook.py               # /webhook endpoint
│       ├── scheduler.py             # /trigger-summaries endpoint
│       ├── health.py                # /health & /stats endpoints
│       └── admin.py                 # Home & admin endpoints
├── main.py                          # Entry point (replaces whatsapp_webhook_v4.py)
├── requirements.txt
├── .env.example
└── README.md
```

## Key Improvements

### 1. **Modular Architecture**
- **Before:** All code mixed in a single file (`whatsapp_webhook_v4.py`)
- **After:** Code organized into logical layers and modules

### 2. **Configuration Management** (`khayal/config.py`)
- Centralized environment variable loading
- Support for multiple environments (development, production, testing)
- Easy configuration switching

### 3. **Flask App Factory** (`khayal/app.py`)
- Follows Flask best practices
- Makes testing and deployment easier
- Allows running multiple app instances

### 4. **Blueprints for Routes** (`khayal/routes/`)
- Each endpoint group in its own file
- `/webhook` - Message handling
- `/health` - Health checks and stats
- `/scheduler` - Summary triggers
- `/admin` - Home and admin endpoints

### 5. **WhatsApp Client Abstraction** (`khayal/whatsapp/`)
- Encapsulates WhatsApp API communication
- Makes it easy to swap implementations
- Better error handling

### 6. **Utilities and Constants** (`khayal/utils/`)
- System prompts in one place
- Logging configuration
- Easy to share constants across modules

## Running the Application

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your values

# Run the app
python main.py
```

### Production (Render)
The `main.py` file is automatically detected and run by Render. The configuration automatically switches to ProductionConfig based on the FLASK_ENV environment variable.

### With Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "khayal.app:create_app()"
```

## Migration Notes

### Backwards Compatibility
The restructuring maintains full backwards compatibility:
- Original files still exist in the root directory
- New structure imports from them for now
- Gradual migration allows testing

### Database
- SQLite for local development (uses `khayal.db`)
- PostgreSQL for production (when DATABASE_URL is set)

### Environment Variables
No changes needed. All existing `.env` variables are still used:
```
PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN
WEBHOOK_VERIFY_TOKEN
GROQ_API_KEY
SCHEDULER_SECRET
PORT
DATABASE_URL (optional)
```

## Testing

The new structure makes unit testing easier:

```python
# Example test
from khayal import create_app
from khayal.config import TestingConfig

def test_webhook():
    app = create_app(TestingConfig)
    client = app.test_client()
    
    response = client.get('/health')
    assert response.status_code == 200
```

## Next Steps

### To Complete the Migration:
1. Move crisis detection to `khayal/core/crisis.py`
2. Move semantic memory to `khayal/core/memory.py`
3. Move onboarding to `khayal/core/onboarding.py`
4. Add unit tests in `tests/` directory
5. Update CI/CD pipeline to use `main.py`

### Future Improvements:
- Add database migrations (Alembic)
- Add API documentation (Swagger/OpenAPI)
- Implement caching layer
- Add monitoring and telemetry
- Create CLI tools for management

## File Mappings

| Old Location | New Location | Notes |
|---|---|---|
| `whatsapp_webhook_v4.py` | `main.py` + `khayal/routes/webhook.py` | Entry point + webhook handler |
| `database.py` | `khayal/database/models.py` | Database layer |
| `mood_analyzer.py` | `khayal/core/mood.py` | Mood analysis |
| `semantic_memory.py` | `khayal/core/memory.py` | Memory system |
| `crisis_detector.py` | `khayal/core/crisis.py` | Crisis detection |
| `onboarding.py` | `khayal/core/onboarding.py` | User onboarding |
| `scheduler.py` | `khayal/routes/scheduler.py` | Summary scheduler |
| `summary_generator.py` | Moved to routes | Summary generation |

## Questions?

Refer to the `.github/copilot-instructions.md` for AI agent guidance on this codebase.
