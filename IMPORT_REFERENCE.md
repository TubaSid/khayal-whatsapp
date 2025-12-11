# Development Reference - Import Guide

## ✨ Quick Import Reference

Use these imports in your code when working with Khayal components.

## Core Business Logic

### Crisis Detection
```python
from khayal.core import CrisisDetector
from groq import Groq

groq_client = Groq(api_key="your-key")
crisis_detector = CrisisDetector(groq_client)

result = crisis_detector.detect_crisis("I want to hurt myself")
# Returns: {"is_crisis": True, "severity": "critical", ...}
```

### Mood Analysis
```python
from khayal.core import MoodAnalyzer
from groq import Groq

groq_client = Groq(api_key="your-key")
mood_analyzer = MoodAnalyzer(groq_client)

mood = mood_analyzer.analyze_mood("I'm feeling really happy today")
# Returns: {"mood": "happy", "confidence": 0.95, ...}
```

### Semantic Memory
```python
from khayal.core import SemanticMemory
from khayal.database import KhayalDatabase
from groq import Groq

db = KhayalDatabase()
groq_client = Groq(api_key="your-key")
memory = SemanticMemory(db, groq_client)

user_context = memory.get_user_context(user_id=123)
# Returns: {"patterns": [...], "recent_moods": [...], ...}
```

### User Onboarding
```python
from khayal.core import OnboardingManager
from khayal.database import KhayalDatabase

db = KhayalDatabase()
onboarding = OnboardingManager(db)

status = onboarding.get_user_onboarding_status(user_id=123)
# Returns: "completed", "in_progress", or "not_started"

if status == "not_started":
    response = onboarding.start_onboarding(user_id=123)
```

## Database Layer

### Access Database
```python
from khayal.database import KhayalDatabase

db = KhayalDatabase()
# Uses SQLite by default

# Or with PostgreSQL (if DATABASE_URL set)
db = KhayalDatabase()  # Automatically uses PostgreSQL if configured
```

### Database Operations
```python
from khayal.database import KhayalDatabase

db = KhayalDatabase()

# Save user
db.save_user(phone_number="1234567890", name="John")

# Get user
user = db.get_user(user_id=123)

# Save message
db.save_message(user_id=123, message="Hi", sender="user")

# Get mood history
moods = db.get_moods(user_id=123)

# Save mood
db.save_mood(user_id=123, mood="happy", confidence=0.9)
```

## External Integrations

### WhatsApp Client
```python
from khayal.whatsapp import WhatsAppClient

client = WhatsAppClient(
    phone_number_id="your-id",
    access_token="your-token"
)

# Send message
response = client.send_message(
    to_number="1234567890",
    message_text="Hi there!"
)
# Returns: {"message_id": "wamid.123", ...}

# Mark message as read
response = client.mark_message_read(message_id="wamid.123")
```

## Utilities

### System Prompts & Constants
```python
from khayal.utils import (
    KHAYAL_SYSTEM_INSTRUCTION,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    GROQ_MAX_TOKENS,
    CRISIS_KEYWORDS,
    MESSAGES,
)

# Use in LLM calls
print(f"Model: {GROQ_MODEL}")  # "llama-3.3-70b-versatile"
print(f"Temperature: {GROQ_TEMPERATURE}")  # 0.9
print(f"System: {KHAYAL_SYSTEM_INSTRUCTION}")  # Full system prompt

# Check for crisis keywords
if any(keyword in message.lower() for keyword in CRISIS_KEYWORDS):
    send_crisis_response()

# Use response messages
print(MESSAGES["onboarding_start"])  # "Hey! 👋 Welcome to Khayal..."
```

### Logging
```python
from khayal.utils import setup_logger

# Create logger for your module
logger = setup_logger(__name__)
# Or with file output
logger = setup_logger(__name__, log_file="debug.log")

# Use logger
logger.info("Processing message from user")
logger.error("Failed to call Groq API")
logger.debug("User profile: %s", user_data)
```

## Configuration

### Get Configuration
```python
from khayal.config import get_config, Config, DevelopmentConfig, ProductionConfig

# Automatic (environment-based)
config = get_config()

# Specific config class
config = DevelopmentConfig()
config = ProductionConfig()

# Access config values
print(config.PHONE_NUMBER_ID)
print(config.GROQ_API_KEY)
print(config.GROQ_MODEL)
print(config.USE_POSTGRES)
print(config.PORT)
print(config.DEBUG)
```

## Flask Application

### Create App
```python
from khayal import create_app
from khayal.config import DevelopmentConfig

# Auto config (environment-based)
app = create_app()

# Specific config
app = create_app(DevelopmentConfig)

# Use in routes
with app.app_context():
    # Do something
    pass

# Test client
with app.test_client() as client:
    response = client.get("/health")
    print(response.json)
```

### Create Custom Blueprint
```python
from flask import Blueprint, jsonify
from khayal.utils import setup_logger

logger = setup_logger(__name__)

# Create blueprint
analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/analytics/overview")
def get_overview():
    logger.info("Fetching analytics overview")
    return jsonify({
        "users": 100,
        "messages": 5000,
        "avg_mood": 7.2
    })

# Register in app
# (Add to khayal/app.py or routes/__init__.py)
```

## Common Patterns

### In Route Handlers
```python
from flask import Blueprint, request, jsonify
from khayal.core import CrisisDetector, MoodAnalyzer
from khayal.database import KhayalDatabase
from khayal.utils import setup_logger
from groq import Groq

logger = setup_logger(__name__)
db = KhayalDatabase()
groq = Groq(api_key="key")
crisis = CrisisDetector(groq)
mood_analyzer = MoodAnalyzer(groq)

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    try:
        # Parse request
        data = request.json
        message = data["message"]
        user_id = data["user_id"]
        
        # Process
        crisis_result = crisis.detect_crisis(message)
        mood_result = mood_analyzer.analyze_mood(message)
        
        # Save
        db.save_message(user_id, message)
        db.save_mood(user_id, mood_result["mood"])
        
        logger.info(f"Processed message from user {user_id}")
        
        return jsonify({"success": True}), 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500
```

### In Tests
```python
import pytest
from khayal import create_app
from khayal.config import Config

class TestConfig(Config):
    TESTING = True
    USE_POSTGRES = False  # Use SQLite for tests
    SQLITE_PATH = ":memory:"  # In-memory database

@pytest.fixture
def app():
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"
```

## Module Organization Reference

```
khayal/
├── core/           # Business logic
│   ├── crisis.py        → CrisisDetector
│   ├── mood.py          → MoodAnalyzer
│   ├── memory.py        → SemanticMemory
│   └── onboarding.py    → OnboardingManager
├── database/       # Data persistence
│   └── models.py        → KhayalDatabase
├── routes/         # API endpoints
│   ├── webhook.py       → POST /webhook
│   ├── health.py        → GET /health, /stats
│   ├── scheduler.py     → POST /trigger-summaries
│   └── admin.py         → GET /
├── whatsapp/       # External APIs
│   └── client.py        → WhatsAppClient
├── utils/          # Shared utilities
│   ├── constants.py     → Constants, prompts
│   └── logger.py        → Logging setup
├── app.py          # App factory
└── config.py       # Configuration

main.py             # Entry point
```

## Troubleshooting Imports

### If you get "ModuleNotFoundError"
```python
# Make sure you're importing FROM THE PACKAGE, not the old files

# ❌ Wrong (old style)
from crisis_detector import CrisisDetector

# ✅ Correct (new style)
from khayal.core import CrisisDetector
```

### If you need to use original modules
```python
# The original files are still there (backward compatibility)
# Import directly if needed:
import sys
sys.path.insert(0, ".")
from crisis_detector import CrisisDetector  # Old style

# But prefer the new way:
from khayal.core import CrisisDetector  # New style
```

### Common Import Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'khayal'` | Not in project directory | `cd khayal-whatsapp` first |
| `ImportError: cannot import name 'CrisisDetector'` | Wrong import path | Use `from khayal.core import...` |
| `KeyError` accessing config | Config not loaded | Use `from khayal.config import get_config` |
| `Database error` | SQLite file not writable | Check permissions or use PostgreSQL |

## Next Steps

1. Choose an import based on what you need
2. Copy-paste the code snippet
3. Customize for your use case
4. Test with `python main.py`

---

**Tip**: Bookmark this page for quick reference while developing!
