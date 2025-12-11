# Khayal v4 Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SYSTEMS                         │
├─────────────────────────────────────────────────────────────┤
│  WhatsApp API        Groq LLM API       Database (PostgreSQL │
│      ↓                   ↓              or SQLite)           │
│      └───────┬───────────┴────────────────┬────────────────┘
│              │                            │
└──────────────┼────────────────────────────┼─────────────────┘
               │                            │
        ┌──────▼────────────────────────────▼───────┐
        │       Flask Application (khayal/)        │
        └──────────────────────────────────────────┘
               │
        ┌──────▼──────────────────────────────┐
        │         Routes Layer                │
        │  (khayal/routes/*.py)              │
        ├────────────────────────────────────┤
        │ ┌─webhook.py─┐  Handles incoming  │
        │ │ POST /webhook  WhatsApp messages │
        │ └──────┬──────┘                    │
        │ ┌─health.py──┐  Health checks &   │
        │ │ GET /health    Statistics       │
        │ └──────┬──────┘                    │
        │ ┌─scheduler.py  Scheduled tasks   │
        │ │ POST /trigger-summaries         │
        │ └──────┬──────┘                    │
        │ ┌─admin.py───┐  Home page & admin │
        │ │ GET /      │                     │
        │ └────────────┘                    │
        └──────────┬───────────────────────┘
                   │
        ┌──────────▼──────────────────────────────────────┐
        │        Core Business Logic Layer              │
        │    (khayal/core/*.py)                         │
        ├──────────────────────────────────────────────┤
        │                                              │
        │ ┌─────────────────────────────────────────┐ │
        │ │  CrisisDetector (crisis.py)            │ │
        │ │  - Keyword analysis                    │ │
        │ │  - LLM-based detection                 │ │
        │ │  - Severity classification             │ │
        │ └─────────────────────────────────────────┘ │
        │                                              │
        │ ┌─────────────────────────────────────────┐ │
        │ │  MoodAnalyzer (mood.py)                │ │
        │ │  - Extract mood from text              │ │
        │ │  - Store mood history                  │ │
        │ └─────────────────────────────────────────┘ │
        │                                              │
        │ ┌─────────────────────────────────────────┐ │
        │ │  SemanticMemory (memory.py)            │ │
        │ │  - Pattern detection                   │ │
        │ │  - User context enrichment             │ │
        │ │  - Embeddings generation               │ │
        │ └─────────────────────────────────────────┘ │
        │                                              │
        │ ┌─────────────────────────────────────────┐ │
        │ │  OnboardingManager (onboarding.py)     │ │
        │ │  - User profile setup                  │ │
        │ │  - Onboarding flow                     │ │
        │ └─────────────────────────────────────────┘ │
        │                                              │
        └──────────┬───────────────────────────────────┘
                   │
        ┌──────────▼──────────────────────────┐
        │      Data Layer                    │
        │  (khayal/database/models.py)      │
        ├──────────────────────────────────┤
        │  KhayalDatabase                  │
        │  - User profiles                 │
        │  - Conversations                 │
        │  - Mood history                  │
        │  - Patterns                      │
        │  - Crisis incidents              │
        └──────────┬───────────────────────┘
                   │
        ┌──────────▼──────────────────────────┐
        │  Utilities & Helpers               │
        │  (khayal/utils/)                  │
        ├──────────────────────────────────┤
        │ - constants.py: System prompts   │
        │ - logger.py: Logging setup       │
        └──────────────────────────────────┘
        
        ┌────────────────────────────────────┐
        │  External Services                 │
        │  (khayal/whatsapp/client.py)      │
        ├────────────────────────────────────┤
        │  WhatsAppClient                    │
        │  - Send messages                   │
        │  - Mark as read                    │
        └────────────────────────────────────┘
        
        ┌────────────────────────────────────┐
        │  Configuration                     │
        │  (khayal/config.py)               │
        ├────────────────────────────────────┤
        │  Config classes:                   │
        │  - Base Config                     │
        │  - DevelopmentConfig               │
        │  - ProductionConfig                │
        │  - get_config() factory            │
        └────────────────────────────────────┘
```

## Data Flow - Processing a User Message

```
User sends message on WhatsApp
         │
         ▼
   Webhook received
   POST /webhook
         │
         ▼
   ┌─────────────────────────────────┐
   │ Parse WhatsApp payload          │
   │ Extract: from, message_id, text │
   └─────────┬───────────────────────┘
             │
             ▼
   ┌─────────────────────────────────┐
   │ Get user profile from database  │
   └─────────┬───────────────────────┘
             │
             ▼
   ┌─────────────────────────────────┐
   │ CrisisDetector.detect_crisis()  │
   │ Check if message indicates      │
   │ mental health crisis            │
   └─────────┬───────────────────────┘
             │
         ┌───┴────┬──────────┐
         │        │          │
        Yes       No      Check severity
         │        │          │
         │        ▼          ▼
         │   Check if      [Continue normal
         │   onboarding    flow]
         │        │
         │        ├─Not started
         │        │    │
         │        │    ▼
         │        │  OnboardingManager
         │        │  .start_onboarding()
         │        │    │
         │        │    ▼
         │        │  Send onboarding
         │        │  response
         │        │
         │        └─In progress
         │             │
         │             ▼
         │          Continue onboarding
         │          workflow
         │             │
         │             ▼
         │          Send next onboarding
         │          step
         │
         ├─Crisis detected
         │    │
         │    ▼
         │  Generate crisis
         │  resources response
         │  (send hotline numbers,
         │   encouragement)
         │
         └─Severity: Critical
              │
              ▼
           Alert admin
           Send escalation
           resources
               │
               ▼
            Send response
            to user
         
         ▼
   ┌──────────────────────────────┐
   │ MoodAnalyzer.analyze()       │
   │ Extract mood from message    │
   └──────────┬───────────────────┘
              │
              ▼
   ┌──────────────────────────────┐
   │ SemanticMemory.query()       │
   │ Find relevant past context   │
   │ (user patterns, history)     │
   └──────────┬───────────────────┘
              │
              ▼
   ┌──────────────────────────────┐
   │ Build LLM prompt             │
   │ - System instruction         │
   │ - User profile              │
   │ - Mood context              │
   │ - Memory/patterns           │
   │ - User message              │
   └──────────┬───────────────────┘
              │
              ▼
   ┌──────────────────────────────┐
   │ Call Groq LLM                │
   │ Generate empathetic response │
   └──────────┬───────────────────┘
              │
              ▼
   ┌──────────────────────────────┐
   │ Save in database:            │
   │ - User message               │
   │ - Mood data                  │
   │ - Khayal response            │
   │ - Interaction timestamp      │
   └──────────┬───────────────────┘
              │
              ▼
   ┌──────────────────────────────┐
   │ WhatsAppClient.send_message()│
   │ Send response to user        │
   └──────────┬───────────────────┘
              │
              ▼
   Message delivered to WhatsApp
```

## Module Dependencies

```
main.py
  └─ khayal/
      ├─ config.py
      ├─ app.py (uses config.py, routes/)
      │
      ├─ routes/
      │   ├─ webhook.py (uses core/, database/, whatsapp/, utils/)
      │   ├─ health.py (uses database/)
      │   ├─ scheduler.py (uses core/, database/, whatsapp/)
      │   └─ admin.py (standalone)
      │
      ├─ core/ (Business Logic)
      │   ├─ crisis.py (imports crisis_detector.py)
      │   ├─ mood.py (imports mood_analyzer.py)
      │   ├─ memory.py (imports semantic_memory.py, database)
      │   └─ onboarding.py (imports onboarding.py)
      │
      ├─ database/
      │   └─ models.py (imports database.py)
      │
      ├─ whatsapp/
      │   └─ client.py (standalone)
      │
      └─ utils/
          ├─ constants.py (standalone)
          └─ logger.py (standalone)
```

## Request Flow - Webhook Processing

```
Request comes in
     │
     ▼
Flask routing
     │
     ▼
webhook.py @app.route('/webhook', methods=['POST'])
     │
     ├─ GET request → verify webhook
     │   └─ Return challenge token
     │
     └─ POST request → handle message
        │
        ├─ Parse JSON
        ├─ Extract phone number, message text, user profile
        │
        ├─ 1. Crisis Detection
        │   └─ If crisis → send resources
        │
        ├─ 2. Onboarding Check
        │   ├─ If not started → start onboarding
        │   └─ If in progress → continue workflow
        │
        ├─ 3. Mood Analysis
        │   └─ Store mood data
        │
        ├─ 4. Memory & Context
        │   ├─ Retrieve user history
        │   └─ Find relevant patterns
        │
        ├─ 5. LLM Response Generation
        │   ├─ Build prompt with context
        │   └─ Call Groq API
        │
        ├─ 6. Save to Database
        │   ├─ Store user message
        │   ├─ Store Khayal response
        │   └─ Update user stats
        │
        └─ 7. Send Response
            └─ WhatsAppClient.send_message()
```

## Database Schema (Logical View)

```
Users
├─ user_id (PK)
├─ phone_number (unique)
├─ name
├─ profile_data (JSON)
├─ onboarding_status
└─ created_at

Conversations
├─ message_id (PK)
├─ user_id (FK)
├─ sender (user/khayal)
├─ text
├─ timestamp
└─ metadata (JSON)

Moods
├─ mood_id (PK)
├─ user_id (FK)
├─ mood_label
├─ confidence
├─ timestamp
└─ context

Patterns
├─ pattern_id (PK)
├─ user_id (FK)
├─ pattern_description
├─ frequency
├─ last_detected
└─ metadata (JSON)

CrisisIncidents
├─ incident_id (PK)
├─ user_id (FK)
├─ severity_level
├─ message_text
├─ resources_sent
├─ timestamp
└─ notes
```

## Configuration Management

```
Environment Variables (.env)
     │
     ▼
config.py
     │
     ├─ Config (base)
     │   ├─ WhatsApp settings
     │   ├─ Groq settings
     │   ├─ Database settings
     │   └─ Server settings
     │
     ├─ DevelopmentConfig(Config)
     │   └─ Override for development
     │
     ├─ ProductionConfig(Config)
     │   └─ Override for production
     │
     └─ get_config()
         └─ Returns appropriate class
```

## Deployment Architecture (Render)

```
GitHub Repository (main branch)
     │
     ▼
Render.com
     │
     ├─ Detects: render.yaml
     ├─ Installs: pip install -r requirements.txt
     ├─ Runs: python main.py
     │
     ▼
Flask App (Port 5000)
     │
     ├─ Receives WhatsApp webhooks
     ├─ Processes messages
     ├─ Connects to PostgreSQL (if DATABASE_URL set)
     └─ Sends responses back to WhatsApp
```

---

**Version**: 4.0.0  
**Last Updated**: December 2025  
**Architecture**: Clean, Modular, Production-Ready 🚀
