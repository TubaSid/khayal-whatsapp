"""Webhook endpoint for WhatsApp messages"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from groq import Groq
import os

# Import modules (maintaining backwards compatibility)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database import KhayalDatabase
from mood_analyzer import MoodAnalyzer
from semantic_memory import SemanticMemory
from crisis_detector import CrisisDetector
from onboarding import OnboardingManager
from khayal.whatsapp import WhatsAppClient
from khayal.config import get_config
from khayal.utils.constants import KHAYAL_SYSTEM_INSTRUCTION

config_class = get_config()
config = config_class()

webhook_bp = Blueprint('webhook', __name__)

# Initialize components
groq_client = Groq(api_key=config.GROQ_API_KEY)
db = KhayalDatabase(config.SQLITE_PATH if not config.USE_POSTGRES else None)
mood_analyzer = MoodAnalyzer(groq_client)
semantic_memory = SemanticMemory(db, groq_client)
crisis_detector = CrisisDetector(groq_client)
onboarding_manager = OnboardingManager(db)
whatsapp_client = WhatsAppClient(config.PHONE_NUMBER_ID, config.WHATSAPP_ACCESS_TOKEN)


def get_khayal_response(user_id: int, user_message: str, mood_data: dict, crisis_data: dict = None) -> str:
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
            model=config.GROQ_MODEL,
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
            temperature=config.GROQ_TEMPERATURE,
            max_tokens=config.GROQ_MAX_TOKENS
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return "Arrey, kuch technical issue ho gaya. Thoda baad mein try karo? 🙏"


@webhook_bp.route("/webhook", methods=["GET", "POST"])
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
    
    if mode == "subscribe" and token == config.WEBHOOK_VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        return challenge, 200
    else:
        print("❌ Verification failed")
        return "Verification failed", 403


def handle_incoming_message():
    """Handle incoming WhatsApp messages"""
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
            whatsapp_client.mark_as_read(message_id)
            
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
            
            if not onboarding_complete:
                print(f"   → User in onboarding")
                
                result = onboarding_manager.process_onboarding_response(
                    user_id,
                    current_step,
                    user_message
                )
                
                print(f"   → Processed: step {current_step} → {result['next_step']}")
                print(f"\n📤 Sending: {result['message'][:100]}...")
                
                whatsapp_client.send_message(from_number, result["message"])
                print(f"✅ Onboarding message sent")
                
                return "EVENT_RECEIVED", 200
            
            print(f"   → User onboarded, normal flow")
            
            # ============================================
            # STEP 2: CRISIS DETECTION
            # ============================================
            
            print(f"\n🚨 Checking for crisis...")
            crisis_data = crisis_detector.detect_crisis(user_message)
            
            if crisis_data['should_escalate']:
                print(f"⚠️  CRISIS DETECTED: {crisis_data['crisis_type']}")
                
                crisis_response = crisis_detector.get_crisis_response(
                    crisis_data['crisis_type'],
                    "IN"
                )
                
                whatsapp_client.send_message(from_number, crisis_response["message"])
                
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
            # STEP 3: NORMAL FLOW
            # ============================================
            
            print(f"\n🧠 Analyzing mood...")
            mood_data = mood_analyzer.analyze(user_message)
            print(f"  Mood: {mood_data['mood']} ({mood_data['intensity']}/10)")
            
            print(f"\n📊 Detecting patterns...")
            patterns = semantic_memory.detect_patterns(user_id, days=7)
            if patterns['needs_attention']:
                print(f"  ⚠️  User needs extra attention")
            
            db.store_user_message(
                user_id=user_id,
                content=user_message,
                mood=mood_data['mood'],
                intensity=mood_data['intensity'],
                themes=mood_data['themes'],
                needs_support=mood_data['needs_support']
            )
            
            print(f"\n🤔 Generating response...")
            khayal_response = get_khayal_response(
                user_id=user_id,
                user_message=user_message,
                mood_data=mood_data,
                crisis_data=crisis_data if crisis_data['is_crisis'] else None
            )
            
            db.store_khayal_message(user_id, khayal_response)
            
            whatsapp_client.send_message(from_number, khayal_response)
            print(f"✅ Response sent")
            
        else:
            print(f"⚠️  Unsupported message type: {message_type}")
            whatsapp_client.send_message(
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
