# whatsapp_webhook_v2.py
# Enhanced WhatsApp Webhook with Mood Analysis - Phase 2

"""
NEW FEATURES IN PHASE 2:
✅ Mood detection for every message
✅ Database storage with mood data
✅ Conversation context in responses
✅ Smart response strategy
✅ Emotional pattern tracking
"""

from flask import Flask, request, jsonify
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Import our new modules
from groq import Groq
from database import KhayalDatabase
from mood_analyzer import MoodAnalyzer

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

# Khayal personality
KHAYAL_SYSTEM_INSTRUCTION = """You are Khayal (خیال) - a warm, empathetic desi companion who journals with people.

Your name means "thought," "care," and "concern" in Urdu/Hindi. You embody these meanings.

PERSONALITY:
- Warm and caring, like a close friend
- Use light Urdu/Hindi naturally (yaar, arrey, bilkul, achha, dekho)
- Never preachy or robotic
- Gentle humor to lighten heavy moments
- Cultural awareness (Bollywood, desi family dynamics, chai culture)

RESPONSE STYLE:
- Validate feelings FIRST before offering perspective
- 2-4 sentences for casual messages
- 4-6 sentences when deep support is needed
- Use natural desi speech patterns
- End with warmth

BOUNDARIES:
- You're a journaling companion, not a therapist
- For crisis signs, gently suggest professional help
- Never dismiss concerns with toxic positivity

Remember: Make people feel heard, understood, and cared for.
"""

# Groq configuration
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.9
GROQ_MAX_TOKENS = 300

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
# KHAYAL RESPONSE GENERATOR (Enhanced)
# ============================================

def get_khayal_response(
    user_message: str,
    mood_data: dict,
    conversation_context: str = ""
) -> str:
    """
    Generate Khayal's response with mood awareness
    
    Args:
        user_message: The user's current message
        mood_data: Mood analysis results
        conversation_context: Recent conversation history
    
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
        
        # Build enhanced prompt with mood awareness
        mood_context = f"""
Current mood analysis:
- Feeling: {mood_data.get('mood', 'neutral')}
- Intensity: {mood_data.get('intensity', 5)}/10
- Needs support: {'Yes' if mood_data.get('needs_support') else 'No'}
- Themes: {', '.join(mood_data.get('themes', []))}
"""
        
        # Build conversation context
        context_section = ""
        if conversation_context:
            context_section = f"\nRecent conversation:\n{conversation_context}\n"
        
        user_prompt = f"""[{time_context}]
{mood_context}
{context_section}
User says: {user_message}

Respond with appropriate emotional awareness. If they need support, validate first. If celebrating, match their energy."""
        
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
    print(f"Mode: {mode}")
    print(f"Token received: {token}")
    print(f"Expected token: {WEBHOOK_VERIFY_TOKEN}")
    
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        print(f"{'='*60}\n")
        return challenge, 200
    else:
        print("❌ Verification failed - token mismatch")
        print(f"{'='*60}\n")
        return "Verification failed", 403

def handle_incoming_message():
    """Handle incoming WhatsApp messages with mood analysis"""
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
            
            # PHASE 2: Analyze mood
            print(f"\n🧠 Analyzing mood...")
            mood_data = mood_analyzer.analyze(user_message)
            print(f"  Mood: {mood_data['mood']}")
            print(f"  Intensity: {mood_data['intensity']}/10")
            print(f"  Themes: {', '.join(mood_data['themes'])}")
            print(f"  Needs support: {'Yes' if mood_data['needs_support'] else 'No'}")
            
            # Get conversation context
            conversation_context = db.get_conversation_context(user_id, limit=3)
            
            # Store user message with mood data
            db.store_user_message(
                user_id=user_id,
                content=user_message,
                mood=mood_data['mood'],
                intensity=mood_data['intensity'],
                themes=mood_data['themes'],
                needs_support=mood_data['needs_support']
            )
            
            # Decide response strategy
            immediate_response = mood_analyzer.should_respond_immediately(mood_data)
            strategy = "Respond immediately" if immediate_response else "Can save for summary"
            print(f"  Strategy: {strategy}")
            
            # For Phase 2, always respond immediately
            # In Phase 5, we'll implement 10 PM summaries
            print(f"\n🤔 Generating response...")
            khayal_response = get_khayal_response(
                user_message=user_message,
                mood_data=mood_data,
                conversation_context=conversation_context
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
        "service": "Khayal WhatsApp Webhook v2",
        "features": ["mood_analysis", "database", "conversation_context"],
        "timestamp": datetime.now().isoformat()
    }), 200

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
    <h1>🌙 Khayal WhatsApp Webhook v2</h1>
    <p><strong>Phase 2 Features:</strong></p>
    <ul>
        <li>✅ Mood analysis for every message</li>
        <li>✅ Database storage with emotional data</li>
        <li>✅ Conversation context awareness</li>
        <li>✅ Smart response strategy</li>
        <li>✅ Emotional pattern tracking</li>
    </ul>
    <p><strong>Endpoints:</strong></p>
    <ul>
        <li>/webhook - WhatsApp webhook</li>
        <li>/health - Health check</li>
        <li>/stats/&lt;phone_number&gt; - User statistics</li>
    </ul>
    """

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌙 KHAYAL WHATSAPP WEBHOOK v2 (PHASE 2)")
    print("="*60)
    print(f"Phone Number ID: {PHONE_NUMBER_ID[:10]}..." if PHONE_NUMBER_ID else "❌ Not configured")
    print(f"Access Token: {'✅ Configured' if WHATSAPP_ACCESS_TOKEN else '❌ Not configured'}")
    print(f"Verify Token: {'✅ Configured' if WEBHOOK_VERIFY_TOKEN else '❌ Not configured'}")
    print(f"Groq API Key: {'✅ Configured' if GROQ_API_KEY else '❌ Not configured'}")
    print(f"Database: ✅ Connected (khayal.db)")
    print(f"Mood Analyzer: ✅ Ready")
    print("="*60)
    
    if not all([PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, GROQ_API_KEY]):
        print("\n⚠️  WARNING: Missing required credentials!")
        print("Check your .env file")
        print("\n")
    
    print("\n🚀 Starting server on http://localhost:5000")
    print("📱 Webhook URL: http://localhost:5000/webhook")
    print("\n💡 New in Phase 2:")
    print("  • Mood detection for every message")
    print("  • Emotional pattern tracking")
    print("  • Conversation context in responses")
    print("  • Database storage with mood data")
    print("="*60 + "\n")
    
    # Run Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)