# whatsapp_webhook_v3.py
# Enhanced WhatsApp Webhook with Advanced Memory - Phase 3

"""
NEW FEATURES IN PHASE 3:
✅ Pattern detection (recurring themes, trends)
✅ Semantic search (find similar past conversations)
✅ Enriched context (patterns + similar conversations)
✅ Trend analysis (mood progression)
✅ Attention flags (needs extra support?)
"""

from flask import Flask, request, jsonify
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Import modules
from groq import Groq
from database import KhayalDatabase
from mood_analyzer import MoodAnalyzer
from semantic_memory import SemanticMemory

# Load environment variables
load_dotenv()

# Configuration
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "khayal_webhook_secret_2025")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize components
groq_client = Groq(api_key=GROQ_API_KEY)
db = KhayalDatabase("khayal.db")
mood_analyzer = MoodAnalyzer(groq_client)
semantic_memory = SemanticMemory(db, groq_client)  # NEW!

# Khayal personality
KHAYAL_SYSTEM_INSTRUCTION = """You are Khayal (خیال) - a warm, empathetic desi companion who journals with people.

Your name means "thought," "care," and "concern" in Urdu/Hindi. You embody these meanings.

PERSONALITY:
- Warm and caring, like a close friend who truly listens
- Use Urdu/Hindi words SPARINGLY and only when they fit naturally (1-2 words per response maximum)
- Never preachy or robotic
- Gentle humor to lighten heavy moments
- Cultural awareness (Bollywood, desi family dynamics, chai culture)

RESPONSE STYLE:
- Validate feelings FIRST before offering perspective
- Keep responses SHORT and conversational (2-3 sentences for casual, 3-4 for support)
- Use natural speech patterns
- End with warmth but don't overdo it

MEMORY AWARENESS - CRITICAL RULES:
- NEVER explicitly say "I remember", "you mentioned", "I notice", "I've noticed", "earlier you said"
- NEVER reference that you're tracking patterns or remembering things
- If patterns exist, show understanding through your response WITHOUT stating you noticed anything
- Example: Instead of "I notice work has been stressing you" → "Work's been heavy lately, huh?"
- Example: Instead of "You mentioned being grateful earlier" → Just respond warmly to their current state
- Be subtly aware, not explicitly memory-demonstrative

LANGUAGE USE:
- Use "yaar" occasionally for friendliness (max once per response)
- Avoid overusing "arrey", "bilkul", "achha" - use them rarely and only when very natural
- Mostly use English with occasional Hindi/Urdu flavor
- Don't force desi words into every sentence

BOUNDARIES:
- You're a journaling companion, not a therapist
- For crisis signs, gently suggest professional help
- Never dismiss concerns with toxic positivity

Remember: Be naturally warm and understanding, not demonstratively smart about memory.
"""

# Groq configuration
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.9
GROQ_MAX_TOKENS = 200  # Keep responses concise and natural

# Initialize Flask app
app = Flask(__name__)

# ============================================
# WHATSAPP HELPER FUNCTIONS
# ============================================

def send_whatsapp_message(to_number: str, message_text: str) -> dict:
    """Send a WhatsApp message"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending message: {e}")
        return {"error": str(e)}

def mark_message_as_read(message_id: str):
    """Mark a message as read"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    
    try:
        requests.post(url, headers=headers, json=data)
    except:
        pass

# ============================================
# KHAYAL RESPONSE GENERATOR (v3 - Enhanced)
# ============================================

def get_khayal_response(
    user_id: int,
    user_message: str,
    mood_data: dict
) -> str:
    """
    Generate Khayal's response with advanced memory awareness
    
    Args:
        user_id: User ID
        user_message: The user's current message
        mood_data: Mood analysis results
    
    Returns:
        Khayal's response as a string
    """
    try:
        # Add time context
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_context = "subah hai"
        elif 12 <= current_hour < 17:
            time_context = "dopahar hai"
        elif 17 <= current_hour < 21:
            time_context = "shaam hai"
        else:
            time_context = "raat hai"
        
        # Get enriched context (NEW IN PHASE 3!)
        enriched_context = semantic_memory.get_enriched_context(user_id, user_message)
        
        # Build mood context
        mood_context = f"""
Current mood analysis:
- Feeling: {mood_data.get('mood', 'neutral')}
- Intensity: {mood_data.get('intensity', 5)}/10
- Needs support: {'Yes' if mood_data.get('needs_support') else 'No'}
- Themes: {', '.join(mood_data.get('themes', []))}
"""
        
        # Build full prompt
        user_prompt = f"""[{time_context}]
{mood_context}

Context (use subtly, don't explicitly reference):
{enriched_context}

User says: {user_message}

Instructions:
- Respond naturally and warmly
- Keep it SHORT (2-3 sentences for casual, max 4 for deep support)
- If context shows patterns, show understanding WITHOUT saying "I notice" or "I remember"
- Use Urdu/Hindi SPARINGLY (1-2 words max, like "yaar" when natural)
- Don't overuse "arrey", "bilkul", "achha"
- Be conversational, not demonstrative about your memory
- Validate feelings first"""
        
        # Generate response
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": KHAYAL_SYSTEM_INSTRUCTION
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=GROQ_TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return "Arrey, kuch technical issue ho gaya yaar. Thoda baad mein try karo? 🙏"

# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """Main webhook endpoint for WhatsApp"""
    
    if request.method == "GET":
        return verify_webhook()
    elif request.method == "POST":
        return handle_incoming_message()

def verify_webhook():
    """Verify webhook with Meta"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    print(f"\n{'='*60}")
    print("🔍 WEBHOOK VERIFICATION REQUEST")
    print(f"{'='*60}")
    
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        print(f"{'='*60}\n")
        return challenge, 200
    else:
        print("❌ Verification failed")
        print(f"{'='*60}\n")
        return "Verification failed", 403

def handle_incoming_message():
    """Handle incoming WhatsApp messages with advanced memory"""
    try:
        data = request.json
        
        print(f"\n{'='*60}")
        print("📩 INCOMING MESSAGE")
        print(f"{'='*60}")
        
        # Extract message details
        if "entry" not in data:
            return "No entry", 200
        
        entry = data["entry"][0]
        changes = entry.get("changes", [])
        
        if not changes:
            return "No changes", 200
        
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return "No messages", 200
        
        # Get message details
        message = messages[0]
        message_id = message.get("id")
        from_number = message.get("from")
        message_type = message.get("type")
        
        print(f"\n📋 Message Details:")
        print(f"  From: {from_number}")
        print(f"  Type: {message_type}")
        
        # Only handle text messages for now
        if message_type == "text":
            user_message = message["text"]["body"]
            print(f"  Content: {user_message}")
            
            # Mark as read
            mark_message_as_read(message_id)
            
            # Get or create user
            user_id = db.get_or_create_user(from_number)
            print(f"  User ID: {user_id}")
            
            # Analyze mood
            print(f"\n🧠 Analyzing mood...")
            mood_data = mood_analyzer.analyze(user_message)
            print(f"  Mood: {mood_data['mood']}")
            print(f"  Intensity: {mood_data['intensity']}/10")
            print(f"  Themes: {', '.join(mood_data['themes'])}")
            print(f"  Needs support: {'Yes' if mood_data['needs_support'] else 'No'}")
            
            # Detect patterns (NEW IN PHASE 3!)
            print(f"\n📊 Detecting patterns...")
            patterns = semantic_memory.detect_patterns(user_id, days=7)
            print(f"  Messages this week: {patterns['total_messages']}")
            print(f"  Dominant mood: {patterns['dominant_mood']}")
            print(f"  Mood trend: {patterns['mood_trend']}")
            if patterns['recurring_themes']:
                print(f"  Recurring themes: {', '.join(patterns['recurring_themes'])}")
            if patterns['stress_triggers']:
                print(f"  Stress triggers: {', '.join(patterns['stress_triggers'])}")
            if patterns['needs_attention']:
                print(f"  ⚠️  USER NEEDS EXTRA ATTENTION")
            
            # Store user message with mood data
            db.store_user_message(
                user_id=user_id,
                content=user_message,
                mood=mood_data['mood'],
                intensity=mood_data['intensity'],
                themes=mood_data['themes'],
                needs_support=mood_data['needs_support']
            )
            
            # Generate response with enriched context
            print(f"\n🤔 Generating response with memory awareness...")
            khayal_response = get_khayal_response(
                user_id=user_id,
                user_message=user_message,
                mood_data=mood_data
            )
            print(f"🌙 Khayal: {khayal_response}")
            
            # Store Khayal's response
            db.store_khayal_message(user_id, khayal_response)
            
            # Send response
            print(f"\n📤 Sending response...")
            result = send_whatsapp_message(from_number, khayal_response)
            
            if "error" not in result:
                print(f"✅ Message sent successfully!")
            else:
                print(f"❌ Failed to send: {result['error']}")
            
        else:
            print(f"⚠️  Unsupported message type: {message_type}")
            send_whatsapp_message(
                from_number,
                "Hmm, yeh message type abhi support nahi hai. Text bhejo na yaar! 😊"
            )
        
        print(f"{'='*60}\n")
        return "EVENT_RECEIVED", 200
        
    except Exception as e:
        print(f"\n❌ ERROR handling message:")
        print(f"  {type(e).__name__}: {str(e)}")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return "Error", 500

# ============================================
# ADDITIONAL ENDPOINTS
# ============================================

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Khayal WhatsApp Webhook v3",
        "features": [
            "mood_analysis",
            "database",
            "semantic_memory",
            "pattern_detection",
            "trend_analysis"
        ],
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/patterns/<phone_number>", methods=["GET"])
def get_patterns(phone_number):
    """Get user patterns and trends"""
    try:
        user_id = db.get_or_create_user(phone_number)
        patterns = semantic_memory.detect_patterns(user_id, days=7)
        trend = semantic_memory.get_mood_trend_chart(user_id, days=7)
        
        return jsonify({
            "user_id": user_id,
            "patterns": patterns,
            "trend": trend
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stats/<phone_number>", methods=["GET"])
def get_user_stats(phone_number):
    """Get user statistics"""
    try:
        user_id = db.get_or_create_user(phone_number)
        stats = db.get_user_stats(user_id)
        mood_history = db.get_mood_history(user_id, days=7)
        
        return jsonify({
            "user_id": user_id,
            "stats": stats,
            "mood_history": mood_history
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    """Home endpoint"""
    return """
    <h1>🌙 Khayal WhatsApp Webhook v3</h1>
    <p><strong>Phase 3 Features:</strong></p>
    <ul>
        <li>✅ Advanced pattern detection</li>
        <li>✅ Semantic memory search</li>
        <li>✅ Mood trend analysis</li>
        <li>✅ Enriched context awareness</li>
        <li>✅ Attention flagging system</li>
    </ul>
    <p><strong>Endpoints:</strong></p>
    <ul>
        <li>/webhook - WhatsApp webhook</li>
        <li>/health - Health check</li>
        <li>/stats/&lt;phone_number&gt; - User statistics</li>
        <li>/patterns/&lt;phone_number&gt; - Pattern analysis</li>
    </ul>
    """

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌙 KHAYAL WHATSAPP WEBHOOK v3 (PHASE 3)")
    print("="*60)
    print(f"Phone Number ID: {PHONE_NUMBER_ID[:10]}..." if PHONE_NUMBER_ID else "❌ Not configured")
    print(f"Access Token: {'✅ Configured' if WHATSAPP_ACCESS_TOKEN else '❌ Not configured'}")
    print(f"Verify Token: {'✅ Configured' if WEBHOOK_VERIFY_TOKEN else '❌ Not configured'}")
    print(f"Groq API Key: {'✅ Configured' if GROQ_API_KEY else '❌ Not configured'}")
    print(f"Database: ✅ Connected")
    print(f"Mood Analyzer: ✅ Ready")
    print(f"Semantic Memory: ✅ Ready")
    print("="*60)
    
    print("\n💡 NEW IN PHASE 3:")
    print("  • Pattern detection across conversations")
    print("  • Semantic search for similar topics")
    print("  • Mood trend tracking")
    print("  • Enriched context in responses")
    print("  • Attention flagging for users needing support")
    print("="*60 + "\n")
    
    print("🚀 Starting server on http://localhost:5000")
    print("="*60 + "\n")
    
    # Run Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)