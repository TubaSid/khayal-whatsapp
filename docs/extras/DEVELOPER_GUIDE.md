# Quick Start Guide for Khayal Developers

## Project Structure at a Glance

```
khayal/
├── app.py                      ← Flask app factory
├── config.py                   ← Environment & settings
├── core/                       ← Business logic
│   └── mood.py                ← Mood analysis
├── database/
│   └── models.py              ← Database operations
├── whatsapp/
│   └── __init__.py            ← WhatsApp API client
├── utils/
│   ├── constants.py           ← System prompts
│   └── logger.py              ← Logging setup
└── routes/
    ├── webhook.py             ← Message handling
    ├── health.py              ← Status endpoints
    ├── scheduler.py           ← Summary scheduler
    └── admin.py               ← Home page

main.py                        ← Entry point
```

## Common Tasks

### Add a New Endpoint

1. Create a new file in `khayal/routes/` (e.g., `khayal/routes/new_feature.py`)
2. Create a Blueprint:
```python
from flask import Blueprint

new_bp = Blueprint('new_feature', __name__)

@new_bp.route("/my-endpoint", methods=["GET"])
def my_handler():
    return {"status": "ok"}, 200
```

3. Register in `khayal/app.py`:
```python
from .routes.new_feature import new_bp
app.register_blueprint(new_bp)
```

### Use Database in a Route

```python
from khayal.database import KhayalDatabase

db = KhayalDatabase()
user_id = db.get_or_create_user(phone_number)
stats = db.get_user_stats(user_id)
```

### Access Configuration

```python
from khayal.config import get_config

config_class = get_config()
config = config_class()

print(config.GROQ_API_KEY)
print(config.WHATSAPP_ACCESS_TOKEN)
```

### Send a WhatsApp Message

```python
from khayal.whatsapp import WhatsAppClient
from khayal.config import get_config

config = get_config()
client = WhatsAppClient(config.PHONE_NUMBER_ID, config.WHATSAPP_ACCESS_TOKEN)

response = client.send_message("+1234567890", "Hello!")
```

### Add a System Constant

In `khayal/utils/constants.py`:
```python
MY_CONSTANT = "some_value"
```

Then import:
```python
from khayal.utils.constants import MY_CONSTANT
```

## Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run the app
python main.py

# 4. Test webhook locally with ngrok
ngrok http 5000
# Update WhatsApp webhook URL to: https://your-ngrok-url.ngrok.io/webhook
```

## Debugging Tips

### See detailed logs
Add this to your code:
```python
from khayal.utils.logger import get_logger
logger = get_logger(__name__)

logger.info("Something happened")
logger.error("An error occurred")
```

### Test a specific endpoint
```bash
# Health check
curl http://localhost:5000/health

# Get user stats
curl http://localhost:5000/stats/+1234567890

# Trigger summaries (needs auth)
curl -X POST http://localhost:5000/trigger-summaries \
  -H "Authorization: Bearer your_secret_token"
```

### Debug database issues
```python
from khayal.database import KhayalDatabase

db = KhayalDatabase()
messages = db.get_recent_messages(user_id, limit=5)
for msg in messages:
    print(msg)
```

## Code Style & Standards

- **Python**: Follow PEP 8 (use Black or autopep8)
- **Naming**: Use `snake_case` for functions/variables, `CamelCase` for classes
- **Docstrings**: Use triple quotes for all functions
- **Type hints**: Add return type annotations
- **Logging**: Use logger instead of print() in production code

Example:
```python
def process_message(user_id: int, content: str) -> dict:
    """Process incoming user message and return analysis.
    
    Args:
        user_id: Unique user identifier
        content: Message text content
    
    Returns:
        Dictionary with mood and analysis results
    """
    logger.info(f"Processing message from user {user_id}")
    
    try:
        mood_data = analyze_mood(content)
        return {"success": True, "mood": mood_data}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"success": False, "error": str(e)}
```

## File Organization Rules

- **One responsibility per file**: Don't mix database code with routing
- **Keep routes lean**: Move complex logic to core modules
- **Central constants**: System prompts and config in utils/
- **Database queries**: Only in database/models.py
- **API calls**: Only in whatsapp/ or core modules

## Testing (When Implemented)

```python
# tests/test_mood.py
from khayal import create_app
from khayal.config import TestingConfig

def test_mood_analyzer():
    app = create_app(TestingConfig)
    client = app.test_client()
    
    response = client.get('/health')
    assert response.status_code == 200
```

## Common Mistakes to Avoid

1. [NOT] **Don't import at module level from whatsapp_webhook_v4.py**
   - [OK] Use the structured imports: `from khayal.database import KhayalDatabase`

2. [NOT] **Don't hardcode configuration values**
   - [OK] Use `from khayal.config import get_config`

3. [NOT] **Don't use print() for logging in routes**
   - [OK] Use `from khayal.utils.logger import get_logger`

4. [NOT] **Don't put database queries in route handlers**
   - [OK] Create helper functions in core/ modules

5. [NOT] **Don't modify database.py directly**
   - [OK] Use `khayal.database.models` instead

## Getting Help

- Check `RESTRUCTURING_GUIDE.md` for migration details
- Read `.github/copilot-instructions.md` for AI agent guidance
- Review existing route files for examples
- Check the main README for architecture overview

## Next Steps

1. [OK] Move crisis detection to `khayal/core/crisis.py`
2. [OK] Move semantic memory to `khayal/core/memory.py`  
3. [OK] Move onboarding to `khayal/core/onboarding.py`
4. [TODO] Add unit tests
5. [TODO] Add API documentation (Swagger)
6. [TODO] Implement database migrations

---

**Happy coding!**
