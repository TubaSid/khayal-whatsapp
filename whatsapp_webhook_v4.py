# whatsapp_webhook_v4.py
# PRODUCTION WEBHOOK - Complete Khayal System (Render-Ready)
# Includes: Crisis Detection + Onboarding + All Features + Scheduler Endpoint

from flask import Flask, request, jsonify
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Import all modules
from groq import Groq
from database import KhayalDatabase
from mood_analyzer import MoodAnalyzer
from semantic_memory import SemanticMemory
from crisis_detector import CrisisDetector
from onboarding import OnboardingManager

load_dotenv()

# Configuration
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "khayal_webhook_secret_2025")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SCHEDULER_SECRET = os.getenv("SCHEDULER_SECRET")  # For GitHub Actions

# Initialize components
groq_client = Groq(api_key=GROQ_API_KEY, proxies=None))
db = KhayalDatabase("khayal.db")
mood_analyzer = MoodAnalyzer(groq_client)
semantic_memory = SemanticMemory(db, groq_client)
crisis_detector = CrisisDetector(groq_client)
onboarding_manager = OnboardingManager(db)

# Khayal personality (updated for production)
KHAYAL_SYSTEM_INSTRUCTION = """You are Khayal (خیال) - a warm, empathetic desi companion who journals with people.

PERSONALITY:
- Warm and caring, like a close friend who truly listens
- Use Urdu/Hindi words SPARINGLY (1-2 per response max, like "yaar" when natural)
- Never preachy or robotic
- Gentle humor to lighten heavy moments
- Cultural awareness

RESPONSE STYLE:
- Validate feelings FIRST before offering perspective
- Keep responses SHORT (2-3 sentences for casual, max 4 for deep support)
- Use natural speech patterns
- End with warmth but don't overdo it

MEMORY AWARENESS - CRITICAL:
- NEVER say "I remember", "I notice", "you mentioned"
- If patterns exist, show understanding WITHOUT stating you noticed
- Be subtly aware, not explicitly demonstrative

LANGUAGE USE:
- Use "yaar" occasionally (max once per response)
- Don't overuse "arrey", "bilkul", "achha"
- Mostly English with occasional Hindi/Urdu flavor

BOUNDARIES:
- You're a journaling companion, not a therapist
- For crisis signs, gently suggest professional help
- Never dismiss concerns

Remember: Be naturally warm and understanding, not demonstratively smart about memory.
"""

# Groq configuration
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.9
GROQ_MAX_TOKENS = 200

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
# KHAYAL RESPONSE GENERATOR (v4 - Production)
# ============================================

def get_khayal_response(
    user_id: int,
    user_message: str,
    mood_data: dict,
    crisis_data: dict = None
) -> str:
    """Generate Khayal's response with all context"""
    
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
        
        # Get enriched context
        enriched_context = semantic_memory.get_enriched_context(user_id, user_message)
        
        # Build mood context
        mood_context = f"""
Current mood analysis:
- Feeling: {mood_data.get('mood', 'neutral')}
- Intensity: {mood_data.get('intensity', 5)}/10
- Needs support: {'Yes' if mood_data.get('needs_support') else 'No'}
"""
        
        # Add crisis context if detected
        crisis_note = ""
        if crisis_data and crisis_data.get('is_crisis'):
            crisis_note = "\n⚠️  IMPORTANT: User may be in distress. Be extra supportive and caring."
        
        # Build full prompt
        user_prompt = f"""[{time_context}]
{mood_context}{crisis_note}

Context (use subtly, don't explicitly reference):
{enriched_context}

User says: {user_message}

Instructions:
- Respond naturally and warmly
- Keep it SHORT (2-3 sentences)
- If context shows patterns, show understanding WITHOUT saying "I notice" or "I remember"
- Use Urdu/Hindi SPARINGLY (1-2 words max, like "yaar" when natural)
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
        return "Arrey, kuch technical issue ho gaya. Thoda baad mein try karo? 🙏"

# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """Main webhook endpoint"""
    
    if request.method == "GET":
        return verify_webhook()
    elif request.method == "POST":
        return handle_incoming_message()

def verify_webhook():
    """Verify webhook with Meta"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        return challenge, 200
    else:
        print("❌ Verification failed")
        return "Verification failed", 403

def handle_incoming_message():
    """Handle incoming WhatsApp messages - PRODUCTION VERSION"""
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
        
        print(f"\n📋 From: {from_number}, Type: {message_type}")
        
        # Only handle text messages
        if message_type == "text":
            user_message = message["text"]["body"]
            print(f"📝 Message: {user_message}")
            
            # Mark as read
            mark_message_as_read(message_id)
            
            # Get or create user
            user_id = db.get_or_create_user(from_number)
            
            # ============================================
            # STEP 1: CHECK IF ONBOARDING NEEDED
            # ============================================
            
            onboarding_complete = onboarding_manager.is_onboarding_complete(user_id)
            current_step = onboarding_manager.get_onboarding_step(user_id)
            
            print(f"\n👋 Onboarding check:")
            print(f"   User ID: {user_id}")
            print(f"   Complete: {onboarding_complete}")
            print(f"   Current step: {current_step}")
            
            # Check if user is in onboarding flow
            if not onboarding_complete:
                print(f"   → User in onboarding")
                
                # Process their message through onboarding
                result = onboarding_manager.process_onboarding_response(
                    user_id,
                    current_step,
                    user_message
                )
                
                print(f"   → Processed: step {current_step} → {result['next_step']}")
                print(f"\n📤 Sending: {result['message'][:100]}...")
                
                send_whatsapp_message(from_number, result["message"])
                print(f"✅ Onboarding message sent")
                
                return "EVENT_RECEIVED", 200
            
            # User has completed onboarding - continue with normal flow
            print(f"   → User onboarded, normal flow")
            
            # ============================================
            # STEP 2: CRISIS DETECTION (Safety First!)
            # ============================================
            
            print(f"\n🚨 Checking for crisis...")
            crisis_data = crisis_detector.detect_crisis(user_message)
            
            if crisis_data['should_escalate']:
                print(f"⚠️  CRISIS DETECTED: {crisis_data['crisis_type']} (severity: {crisis_data['severity']})")
                
                # Send crisis resources immediately
                crisis_response = crisis_detector.get_crisis_response(
                    crisis_data['crisis_type'],
                    "IN"  # TODO: Detect user's country
                )
                
                send_whatsapp_message(from_number, crisis_response["message"])
                
                # Log crisis in database
                db.store_user_message(
                    user_id=user_id,
                    content=user_message,
                    mood="crisis",
                    intensity=10,
                    themes=["crisis", crisis_data['crisis_type']],
                    needs_support=True
                )
                
                print(f"✅ Crisis resources sent")
                return "EVENT_RECEIVED", 200
            
            # ============================================
            # STEP 3: NORMAL FLOW (Mood + Response)
            # ============================================
            
            # Analyze mood
            print(f"\n🧠 Analyzing mood...")
            mood_data = mood_analyzer.analyze(user_message)
            print(f"  Mood: {mood_data['mood']} ({mood_data['intensity']}/10)")
            
            # Detect patterns
            print(f"\n📊 Detecting patterns...")
            patterns = semantic_memory.detect_patterns(user_id, days=7)
            if patterns['needs_attention']:
                print(f"  ⚠️  User needs extra attention")
            
            # Store user message
            db.store_user_message(
                user_id=user_id,
                content=user_message,
                mood=mood_data['mood'],
                intensity=mood_data['intensity'],
                themes=mood_data['themes'],
                needs_support=mood_data['needs_support']
            )
            
            # Generate response
            print(f"\n🤔 Generating response...")
            khayal_response = get_khayal_response(
                user_id=user_id,
                user_message=user_message,
                mood_data=mood_data,
                crisis_data=crisis_data if crisis_data['is_crisis'] else None
            )
            
            # Store Khayal's response
            db.store_khayal_message(user_id, khayal_response)
            
            # Send response
            send_whatsapp_message(from_number, khayal_response)
            print(f"✅ Response sent")
            
        else:
            print(f"⚠️  Unsupported message type: {message_type}")
            send_whatsapp_message(
                from_number,
                "Hey! I work best with text messages. Voice notes coming soon! 😊"
            )
        
        print(f"{'='*60}\n")
        return "EVENT_RECEIVED", 200
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return "Error", 500

# ============================================
# SCHEDULER ENDPOINT (FOR GITHUB ACTIONS)
# ============================================

@app.route("/trigger-summaries", methods=["POST"])
def trigger_summaries():
    """
    Endpoint to trigger daily summaries
    Called by GitHub Actions at 10 PM IST
    """
    try:
        # Verify secret token
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f'Bearer {SCHEDULER_SECRET}':
            print("❌ Unauthorized summary trigger attempt")
            return jsonify({'error': 'Unauthorized'}), 401
        
        print(f"\n{'='*60}")
        print(f"🌙 DAILY SUMMARY TRIGGER [{datetime.now()}]")
        print(f"{'='*60}\n")
        
        # Import summary generator
        from summary_generator import SummaryGenerator
        
        # Initialize and send summaries
        summary_gen = SummaryGenerator(db, groq_client)
        results = summary_gen.send_all_summaries()
        
        print(f"\n✅ Summaries sent to {len(results)} users")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'message': 'Summaries sent successfully',
            'users_count': len(results),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error sending summaries: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================
# ADDITIONAL ENDPOINTS
# ============================================

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Khayal v4 Production",
        "features": [
            "crisis_detection",
            "onboarding",
            "mood_analysis",
            "pattern_detection",
            "semantic_memory",
            "daily_summaries"
        ],
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/stats/<phone_number>", methods=["GET"])
def get_user_stats(phone_number):
    """Get user statistics"""
    try:
        user_id = db.get_or_create_user(phone_number)
        stats = db.get_user_stats(user_id)
        patterns = semantic_memory.detect_patterns(user_id, days=7)
        prefs = onboarding_manager.get_preferences(user_id)
        
        return jsonify({
            "user_id": user_id,
            "stats": stats,
            "patterns": patterns,
            "preferences": prefs
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    """Home endpoint"""
    return """
    <h1>🌙 Khayal v4 - Production</h1>
    <p><strong>Status:</strong> Online</p>
    <p><strong>Features:</strong></p>
    <ul>
        <li>✅ Crisis detection & resources</li>
        <li>✅ Professional onboarding</li>
        <li>✅ Mood analysis</li>
        <li>✅ Pattern detection</li>
        <li>✅ Semantic memory</li>
        <li>✅ Daily 10 PM summaries (via GitHub Actions)</li>
    </ul>
    <p><strong>Endpoints:</strong></p>
    <ul>
        <li><code>/webhook</code> - WhatsApp webhook</li>
        <li><code>/health</code> - Health check</li>
        <li><code>/trigger-summaries</code> - Trigger daily summaries (POST only, requires auth)</li>
        <li><code>/stats/&lt;phone_number&gt;</code> - User statistics</li>
    </ul>
    """

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌙 KHAYAL v4 - PRODUCTION READY (RENDER)")
    print("="*60)
    print(f"Phone Number ID: {PHONE_NUMBER_ID[:10]}..." if PHONE_NUMBER_ID else "❌")
    print(f"Access Token: {'✅' if WHATSAPP_ACCESS_TOKEN else '❌'}")
    print(f"Groq API Key: {'✅' if GROQ_API_KEY else '❌'}")
    print(f"Database: ✅ Connected")
    print(f"Crisis Detector: ✅ Ready")
    print(f"Onboarding: ✅ Ready")
    print("="*60)
    
    print("\n🚀 Features Active:")
    print("  • Crisis detection & mental health resources")
    print("  • Professional user onboarding")
    print("  • Mood analysis & tracking")
    print("  • Pattern detection")
    print("  • Semantic memory")
    print("  • Daily summaries (GitHub Actions)")
    print("="*60 + "\n")
    
    # Get port from environment (Render sets this)
    port = int(os.getenv("PORT", 5000))
    
    print(f"🚀 Starting server on port {port}")
    print("="*60 + "\n")
    
    # Run Flask app
    app.run(host="0.0.0.0", port=port, debug=False)
