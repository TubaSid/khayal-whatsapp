# 🌙 Khayal - WhatsApp Companion for Emotional Support

A warm, empathetic WhatsApp bot that journals with people, provides emotional support, and detects mental health crises with cultural sensitivity.

---

## 📚 **IMPORTANT: Restructured Architecture (v4.0.0)**

**This codebase has been restructured into a professional, modular Python package!**

### 👉 **Start Here:**
- **[START_HERE.md](START_HERE.md)** - Quick overview (5 min)
- **[QUICKSTART.md](QUICKSTART.md)** - Setup guide (5 min)
- **[IMPORT_REFERENCE.md](IMPORT_REFERENCE.md)** - Code examples (3 min)
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Complete guide index

### 🎯 **Quick Links by Role:**
- **Project Manager**: [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)
- **Developer**: [QUICKSTART.md](QUICKSTART.md) → [IMPORT_REFERENCE.md](IMPORT_REFERENCE.md)
- **Architect**: [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)
- **QA/Testing**: [QUICKSTART.md](QUICKSTART.md) → [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)

### 📊 **What Changed:**
See [BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md) for detailed comparison.

---

## Features

- **Crisis Detection**: Identifies mental health emergencies and provides immediate resources
- **Mood Analysis**: Understands emotional state and tracks patterns over time
- **Semantic Memory**: Maintains context about user's thoughts, feelings, and concerns
- **Onboarding**: Professional user setup with preferences and timezone
- **Daily Summaries**: Generates personalized summaries at 10 PM (via GitHub Actions)
- **Desi Companion**: Uses cultural nuances (Urdu/Hindi) naturally and sparingly

## Architecture

The codebase is organized into a clean, modular Python package structure:

```
khayal/
├── app.py                    # Flask app factory
├── config.py                 # Configuration management
├── core/                     # Business logic
│   ├── mood.py              # Mood analysis
│   ├── memory.py            # Semantic memory & patterns
│   ├── crisis.py            # Crisis detection
│   └── onboarding.py        # User onboarding
├── database/                # Data layer
│   └── models.py            # Database operations
├── whatsapp/                # WhatsApp integration
│   └── client.py            # WhatsApp API wrapper
├── utils/                   # Utilities
│   ├── constants.py         # System prompts & constants
│   └── logger.py            # Logging configuration
└── routes/                  # API endpoints
    ├── webhook.py           # Message handling
    ├── health.py            # Health checks
    ├── scheduler.py         # Summary triggers
    └── admin.py             # Admin endpoints
```

See [RESTRUCTURING_GUIDE.md](RESTRUCTURING_GUIDE.md) for detailed migration notes.

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (optional, for production)
- Render account (for hosting)
- WhatsApp Business API access
- Groq API key

### Local Setup

```bash
# Clone repository
git clone https://github.com/TubaSid/khayal-whatsapp.git
cd khayal-whatsapp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Run the app
python main.py
```

The app will start on `http://localhost:5000`

## Configuration

### Environment Variables

```env
# WhatsApp
PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WEBHOOK_VERIFY_TOKEN=your_webhook_token

# AI
GROQ_API_KEY=your_groq_api_key

# Scheduler
SCHEDULER_SECRET=your_scheduler_secret

# Server
PORT=5000
FLASK_ENV=production

# Database (optional - uses SQLite if not set)
DATABASE_URL=postgresql://user:password@host:port/dbname
```

### Multiple Environments

The app automatically selects configuration based on `FLASK_ENV`:
- `development` → DevelopmentConfig (DEBUG=True)
- `testing` → TestingConfig (isolated database)
- `production` → ProductionConfig (DEBUG=False)

## API Endpoints

### Webhook
- **POST** `/webhook` - Receives WhatsApp messages
- **GET** `/webhook` - Verifies webhook with Meta

### Health & Monitoring
- **GET** `/health` - Health check and feature status
- **GET** `/stats/<phone_number>` - User statistics and patterns

### Scheduler
- **POST** `/trigger-summaries` - Triggers daily summaries (requires Bearer token)

### Admin
- **GET** `/` - Home page with service info

## Workflow: Message Handling

When a user sends a message, this happens in sequence:

```
1. Webhook receives message
   ↓
2. Check if user needs onboarding
   ├─ NO → Continue to step 3
   └─ YES → Send next onboarding step
   ↓
3. Check for crisis signals
   ├─ YES → Send crisis resources + log as crisis
   └─ NO → Continue to step 4
   ↓
4. Analyze mood & emotions
   ↓
5. Detect patterns in user's recent messages
   ↓
6. Generate warm, contextual response
   ↓
7. Send response to user
```

## Development

### Running Tests
```bash
# (To be implemented with pytest)
pytest tests/
```

### Code Structure

Each module follows this pattern:
- **Input validation** - Check data types and required fields
- **Business logic** - Process the core functionality
- **Error handling** - Graceful degradation with fallbacks
- **Logging** - Track important events and errors

### Key Classes

- `WhatsAppClient` - Handles message sending and webhook verification
- `MoodAnalyzer` - Analyzes emotional content of messages
- `SemanticMemory` - Stores and retrieves user context
- `CrisisDetector` - Identifies crisis signals and provides resources
- `OnboardingManager` - Manages user setup and preferences
- `KhayalDatabase` - Database abstraction (SQLite/PostgreSQL)

## Deployment

### Render
The app is production-ready for Render:

1. Push to GitHub
2. Connect repository to Render
3. Set environment variables in Render dashboard
4. Deploy - Render automatically runs `main.py` with Gunicorn

### GitHub Actions (Scheduler)
Daily summaries trigger via GitHub Actions:

```yaml
# .github/workflows/daily-summaries.yml
name: Daily Summaries
on:
  schedule:
    - cron: '22 16 * * *'  # 10 PM IST

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger summaries
        run: |
          curl -X POST https://your-app.onrender.com/trigger-summaries \
            -H "Authorization: Bearer ${{ secrets.SCHEDULER_SECRET }}"
```

## Personality & Tone

Khayal is:
- **Warm and caring** - Like a close friend who truly listens
- **Culturally aware** - Uses Hindi/Urdu words sparingly and naturally
- **Concise** - Keeps responses short (2-3 sentences)
- **Non-judgmental** - Validates feelings before offering perspective
- **Humble** - Never demonstratively "showing off" memory or patterns

Key guidelines:
- Say "yaar" occasionally (max once per response)
- Use "I notice" or "I remember" NEVER
- Show understanding subtly through context
- Never be preachy or robotic

## Database Schema

### users
- `id` - Unique user ID
- `phone_number` - WhatsApp phone number
- `name` - User's name (from onboarding)
- `created_at` - Account creation timestamp
- `last_active` - Last message timestamp

### messages
- `id` - Message ID
- `user_id` - Reference to users table
- `content` - Message text
- `is_user` - Whether message is from user (true) or Khayal (false)
- `timestamp` - When message was sent
- `mood` - Detected emotion
- `intensity` - Emotion intensity (1-10)
- `themes` - Topics mentioned (comma-separated)
- `needs_support` - Whether user needs immediate support

### user_preferences
- `user_id` - Reference to users table
- `language_preference` - Language mix preference
- `summary_time` - Preferred summary time (HH:MM)
- `summary_enabled` - Whether summaries are enabled
- `timezone` - User's timezone
- `onboarding_complete` - Whether onboarding is finished
- `onboarding_step` - Current onboarding step

## Troubleshooting

### "❌ Error sending message"
- Check WhatsApp Access Token is valid
- Verify phone number format (with country code)
- Ensure WhatsApp Business API has permission

### "❌ JSON parsing error" (Mood analyzer)
- Check Groq API key is valid
- Verify internet connection to Groq API
- Check message isn't empty

### Database connection errors
- Verify DATABASE_URL is correct (if using PostgreSQL)
- Check SQLite file permissions (for local development)
- Ensure database tables are initialized

## Support & Contributions

- **Report bugs** - Create an issue on GitHub
- **Suggest features** - Discussions section on GitHub
- **Contribute** - Fork, make changes, submit PR

### Code Guidelines
- Follow PEP 8 style guide
- Add docstrings to functions
- Include type hints for clarity
- Write descriptive commit messages

## License

(Add your license here)

## Contact

- GitHub: [@TubaSid](https://github.com/TubaSid)
- Email: (add email if public)

---

**Made with ❤️ for mental health support and emotional wellbeing**
