# Quick Start - Khayal Development

## First Time Setup

1. **Clone and navigate to project**
   ```bash
   cd khayal-whatsapp
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the app**
   ```bash
   python main.py
   ```

## Project Structure Quick Reference

```
khayal-whatsapp/
├── khayal/
│   ├── core/              # Business logic (imports from original files)
│   │   ├── crisis.py      # Crisis detection
│   │   ├── mood.py        # Mood analysis
│   │   ├── memory.py      # Semantic memory
│   │   └── onboarding.py  # User onboarding
│   ├── database/          # Data layer
│   │   └── models.py      # KhayalDatabase class
│   ├── routes/            # API endpoints (Flask blueprints)
│   │   ├── webhook.py     # /webhook endpoint
│   │   ├── health.py      # /health endpoint
│   │   ├── scheduler.py   # /trigger-summaries endpoint
│   │   └── admin.py       # / (home) endpoint
│   ├── whatsapp/          # WhatsApp API wrapper
│   │   └── client.py      # WhatsAppClient class
│   ├── utils/             # Utilities
│   │   ├── constants.py   # System prompts, config constants
│   │   └── logger.py      # Logging utilities
│   ├── app.py             # Flask app factory
│   └── config.py          # Configuration management
├── main.py                # Entry point (python main.py)
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
└── README.md             # Project README
```

## Common Tasks

### Adding a New Route

1. Create a new file in `khayal/routes/` (e.g., `analytics.py`)
2. Create a Blueprint:
   ```python
   from flask import Blueprint
   
   analytics_bp = Blueprint('analytics', __name__)
   
   @analytics_bp.route("/analytics")
   def get_analytics():
       return {"data": "..."}
   ```

3. Register in `khayal/app.py`:
   ```python
   from .routes import analytics
   app.register_blueprint(analytics.analytics_bp)
   ```

### Adding a New Core Module

1. Create file in `khayal/core/` (e.g., `sentiment.py`)
2. Add class/functions for business logic
3. Export in `khayal/core/__init__.py`:
   ```python
   from .sentiment import SentimentAnalyzer
   __all__ = [..., "SentimentAnalyzer"]
   ```

### Using Core Components

```python
# Import from the package
from khayal.core import CrisisDetector, MoodAnalyzer
from khayal.database import KhayalDatabase
from khayal.utils import KHAYAL_SYSTEM_INSTRUCTION, setup_logger
from groq import Groq

# Initialize
groq_client = Groq(api_key="your-key")
crisis_detector = CrisisDetector(groq_client)
db = KhayalDatabase()

# Use
result = crisis_detector.detect_crisis("I want to hurt myself")
db.save_message(user_id, message_text)
```

### Using Configuration

```python
from khayal.config import get_config

config = get_config()
print(config.GROQ_API_KEY)
print(config.USE_POSTGRES)
print(config.PORT)
```

### Logging

```python
from khayal.utils import setup_logger

logger = setup_logger(__name__)  # In module
logger.info("Message sent successfully")
logger.error("Failed to connect to database")
```

## Testing Locally

### Test a Webhook Message

```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "1234567890",
            "id": "wamid.123",
            "text": {"body": "Hi Khayal!"}
          }],
          "contacts": [{
            "profile": {"name": "Test User"},
            "wa_id": "1234567890"
          }]
        }
      }]
    }]
  }'
```

### Test Health Endpoint

```bash
curl http://localhost:5000/health
```

## Environment Variables Reference

| Variable | Purpose | Required |
|----------|---------|----------|
| `PHONE_NUMBER_ID` | WhatsApp phone ID | ✅ Yes |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp API token | ✅ Yes |
| `GROQ_API_KEY` | Groq AI API key | ✅ Yes |
| `WEBHOOK_VERIFY_TOKEN` | Webhook validation token | ⚠️ Optional (default provided) |
| `SCHEDULER_SECRET` | Secret for scheduler endpoint | ✅ Yes (for summaries) |
| `DATABASE_URL` | PostgreSQL connection string | ⚠️ Optional (uses SQLite if not set) |
| `PORT` | Server port | ⚠️ Optional (default: 5000) |

## Debugging

### View logs while running
```bash
python main.py  # Logs appear here
```

### Enable debug mode
Edit `main.py` to change `config.DEBUG = True`

### Use the Flask debugger
```python
from khayal.config import DevelopmentConfig
config = DevelopmentConfig()
config.DEBUG = True
```

## File Organization Tips

- **Business Logic**: `khayal/core/`
- **Data Access**: `khayal/database/`
- **API Handlers**: `khayal/routes/`
- **External APIs**: `khayal/whatsapp/`
- **Shared Utilities**: `khayal/utils/`
- **Configuration**: `khayal/config.py`

## Useful Commands

```bash
# Run app
python main.py

# Run with specific config
FLASK_ENV=development python main.py

# Install new package
pip install <package-name>
pip freeze > requirements.txt  # Update requirements

# Run tests (when added)
pytest

# Format code
black khayal/

# Check style
pylint khayal/
```

## Deployment to Render

1. Push changes to main branch
2. Render automatically detects and deploys
3. Watch logs in Render dashboard
4. App available at your Render URL

## Troubleshooting

**App won't start**
- Check `.env` file has all required variables
- Run `python main.py` to see exact error

**WhatsApp webhook not receiving messages**
- Verify webhook URL in WhatsApp Business Account
- Check `WEBHOOK_VERIFY_TOKEN` matches

**Database errors**
- For SQLite: ensure `khayal.db` is writable
- For PostgreSQL: verify `DATABASE_URL` is correct

**API timeouts**
- Check Groq API key is valid
- Verify WhatsApp API credentials

## Next Steps

1. Read `MIGRATION_GUIDE.md` for detailed structure info
2. Check individual module docstrings for usage
3. Review `whatsapp_webhook_v4.py` to understand original logic
4. Gradually migrate helper functions to appropriate modules

---

**Need help?** Check the module docstrings or raise an issue!
