# Khayal Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WhatsApp Users                               │
│              (messages via WhatsApp Business API)                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    WhatsApp API      │
                    │   (Meta Platform)    │
                    └──────────────┬───────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │   POST /webhook          │
                    │  (Flask Route Handler)   │
                    └──────────────┬───────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────────┐
        │                          │                              │
        ▼                          ▼                              ▼
   ┌─────────────┐          ┌─────────────┐          ┌──────────────────┐
   │  Webhook    │          │  Database   │          │ WhatsApp Client  │
   │  Handler    │          │  (SQLite/   │          │  (API Wrapper)   │
   │             │          │  PostgreSQL)│          │                  │
   │ routes/     │          │             │          │ whatsapp/client  │
   │ webhook.py  │          │ database/   │          │                  │
   └──────┬──────┘          │ models.py   │          │ • send_message() │
          │                 │             │          │ • mark_as_read() │
          │                 └─────────────┘          └──────────────────┘
          │
          │ Process message through pipeline:
          │
    ┌─────▼────────────────────────────────────────────────────────────┐
    │                    MESSAGE PIPELINE                              │
    │                                                                  │
    │  1. Check Onboarding Status                                      │
    │     └─> onboarding/OnboardingManager                             │
    │                                                                  │
    │  2. Detect Crisis Signals                                        │
    │     └─> crisis_detector/CrisisDetector                           │
    │         ├─> Send crisis resources                               │
    │         └─> Log as crisis                                       │
    │                                                                  │
    │  3. Analyze Mood & Emotions                                      │
    │     └─> core/mood.py → MoodAnalyzer                             │
    │         ├─ Detect emotion                                       │
    │         ├─ Measure intensity (1-10)                             │
    │         └─ Identify themes                                      │
    │                                                                  │
    │  4. Detect Patterns (7-day analysis)                             │
    │     └─> semantic_memory/SemanticMemory                          │
    │         ├─ Recurring themes                                     │
    │         ├─ Mood trends                                          │
    │         └─ Support needs                                        │
    │                                                                  │
    │  5. Store Message                                                │
    │     └─> database/KhayalDatabase                                 │
    │         └─ Save to messages table                               │
    │                                                                  │
    │  6. Generate Response                                            │
    │     └─> Groq LLM (llama-3.3-70b)                                │
    │         ├─ System prompt: KHAYAL_SYSTEM_INSTRUCTION             │
    │         ├─ Mood data as context                                 │
    │         ├─ Recent message history                               │
    │         └─ Pattern insights                                     │
    │                                                                  │
    │  7. Send Response                                                │
    │     └─> whatsapp/WhatsAppClient.send_message()                 │
    │                                                                  │
    └────────────────────────────────────────────────────────────────┘


## Module Dependencies

```
main.py
  └─> khayal/app.py (Flask app factory)
      ├─> khayal/config.py (Configuration)
      │
      └─> khayal/routes/
          ├─> webhook.py
          │   ├─> khayal/whatsapp/client.py (WhatsApp API)
          │   ├─> khayal/database/models.py (Database)
          │   ├─> khayal/core/mood.py (Mood analysis)
          │   ├─> semantic_memory/ (Pattern detection)
          │   ├─> crisis_detector/ (Crisis detection)
          │   └─> onboarding/ (User setup)
          │
          ├─> health.py
          │   ├─> khayal/database/models.py
          │   └─> semantic_memory/
          │
          ├─> scheduler.py
          │   ├─> khayal/database/models.py
          │   └─> summary_generator/
          │
          └─> admin.py (static home page)
```

## Configuration Hierarchy

```
┌─────────────────────────────────────────┐
│     Environment Variables (.env)         │
│  PHONE_NUMBER_ID, GROQ_API_KEY, etc.    │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│    khayal/config.py                     │
│  • Config (base)                        │
│  • DevelopmentConfig (DEBUG=True)       │
│  • ProductionConfig (DEBUG=False)       │
│  • TestingConfig (isolated DB)          │
│  • get_config() → auto-selects          │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│   Usage in khayal/app.py                │
│                                         │
│   config = get_config()                 │
│   app.config.from_object(config)        │
└─────────────────────────────────────────┘
```

## Database Schema Relationships

```
┌─────────────────────┐
│      users          │
├─────────────────────┤
│ id (PK)             │
│ phone_number        │
│ name                │
│ created_at          │
│ last_active         │
└────────────┬────────┘
             │
             ├──────────────────────────┬─────────────────┐
             │                          │                 │
             ▼                          ▼                 ▼
    ┌─────────────────────┐  ┌──────────────────────┐
    │    messages         │  │ user_preferences     │
    ├─────────────────────┤  ├──────────────────────┤
    │ id (PK)             │  │ user_id (PK, FK)     │
    │ user_id (FK)        │  │ name                 │
    │ content (TEXT)      │  │ language_preference  │
    │ is_user             │  │ summary_time         │
    │ timestamp           │  │ summary_enabled      │
    │ mood                │  │ timezone             │
    │ intensity           │  │ onboarding_complete  │
    │ themes              │  │ onboarding_step      │
    │ needs_support       │  │ created_at           │
    └─────────────────────┘  └──────────────────────┘
         (indexes on:
          user_id, timestamp)
```

## Request/Response Flow

```
1. User sends message on WhatsApp
   │
   └─> 2. WhatsApp API → POST /webhook
        │
        └─> 3. Flask Router → webhook.py (handle_incoming_message)
             │
             ├─> 4a. Extract message data
             │       • message_id, from_number, message_type
             │
             ├─> 5a. Check onboarding
             │       ├─ IF NOT ONBOARDED → send onboarding message
             │       └─ IF ONBOARDED → continue
             │
             ├─> 5b. Check for crisis
             │       ├─ IF CRISIS → send resources + return
             │       └─ IF OK → continue
             │
             ├─> 6. Analyze mood
             │       • Call groq LLM
             │       • Get: mood, intensity, themes, needs_support
             │
             ├─> 7. Detect patterns
             │       • Query last 7 days of messages
             │       • Identify trends and recurring themes
             │
             ├─> 8. Store user message in database
             │       • INSERT into messages table
             │
             ├─> 9. Generate Khayal response
             │       • Build prompt with:
             │         - System instruction (personality)
             │         - Mood analysis
             │         - Recent history
             │         - Detected patterns
             │       • Call groq LLM → get response
             │
             ├─> 10. Store Khayal message in database
             │       • INSERT into messages table (is_user=false)
             │
             └─> 11. Send response to user
                     • POST to WhatsApp API
                     • Return 200 OK to webhook
```

## Deployment Architecture

```
GitHub Repository
│
├─ main.py
├─ khayal/
├─ requirements.txt
└─ .env (secrets in Render)
│
▼
Render Platform
│
├─ Detects: requirements.txt
├─ Runs: gunicorn -w 4 "khayal.app:create_app()"
├─ Port: $PORT environment variable
├─ Database: PostgreSQL (via DATABASE_URL)
│
▼
Running App (PORT 5000 or custom)
│
├─ /webhook (POST) ─────────┐
├─ /health (GET) ──────────┤── Live requests
├─ /stats/... (GET) ───────┤
└─ /trigger-summaries (POST)┘
│
▼
External Services
├─ WhatsApp API (Meta)
├─ Groq API (AI/LLM)
└─ PostgreSQL Database
```

## Error Handling & Fallbacks

```
┌─────────────────────────────────────┐
│     Error Occurs in Pipeline        │
└────────────────┬────────────────────┘
                 │
    ┌────────────┼────────────────────┐
    │            │                    │
    ▼            ▼                    ▼
Mood    Database  WhatsApp Send
Analysis Error    Error
    │            │                    │
    ▼            ▼                    ▼
Return    Log & Continue  Retry with
Default   (saved in crash Send generic
Mood Data log)            message

All errors:
• Logged with logger.error()
• User gets graceful response
• App continues running
• No crashes/downtime
```

## Performance Considerations

```
Message → Handler

1. FAST: Extract & validate (< 50ms)
2. MEDIUM: Database queries (< 500ms per query)
3. SLOW: Groq API calls (2-5 seconds typical)
4. ASYNC CANDIDATE: Summary generation

Total response time: ~5-10 seconds per message

Optimizations:
• Cache user preferences in memory
• Pre-load recent messages (limit 10)
• Use database connection pooling (PostgreSQL)
• Consider async tasks for summaries (Celery)
```

---

For more details, see:
- **README.md** - Project overview
- **DEVELOPER_GUIDE.md** - Development tips
- **RESTRUCTURING_GUIDE.md** - Migration notes
