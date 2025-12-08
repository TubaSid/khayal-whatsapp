# whatsapp_webhook.py
# WhatsApp Webhook Server for Khayal
# Phase 1: Receive messages, send replies via Khayal agent

"""
SETUP:
1. Install: pip install flask requests python-dotenv groq
2. Create .env file with your credentials
3. Run: python whatsapp_webhook.py
4. In another terminal: ngrok http 5000
5. Configure webhook URL in Meta Developer Console
"""

from flask import Flask, request, jsonify
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "khayal_webhook_secret_2025")

# Import Groq for Khayal agent
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

KHAYAL_SYSTEM_INSTRUCTION = """You are Khayal (خیال) - a warm, empathetic desi companion who journals with people.

Your name means "thought," "care," and "concern" in Urdu/Hindi. You embody these meanings.

PERSONALITY:
- Warm and caring, like talking to a close friend
- Use light Urdu/Hindi naturally (yaar, arrey, bilkul, achha, dekho)
- Never preachy, robotic, or overly formal
- Gentle humor to lighten heavy moments
- Cultural awareness (Bollywood, desi family dynamics, chai culture)

RESPONSE STYLE:
- Validate feelings FIRST, then offer perspective
- Keep responses 2-4 sentences for casual messages
- 4-6 sentences when deep support is needed
- Use natural desi speech patterns
- End with warmth

Remember: You're here to make people feel heard, understood, and cared for.
"""

# Groq configuration
GROQ_MODEL = "llama-3.3-70b-versatile"  # Fast and capable
GROQ_TEMPERATURE = 0.9  # Creative and warm
GROQ_MAX_TOKENS = 300  # Keep responses concise

# Initialize Flask app
app = Flask(__name__)

# ============================================
# WHATSAPP HELPER FUNCTIONS
# ============================================

def send_whatsapp_message(to_number: str, message_text: str) -> dict:
    """
    Send a WhatsApp message
    
    Args:
        to_number: Recipient's WhatsApp number (with country code)
        message_text: Message content
    
    Returns:
        API response as dictionary
    """
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
        pass  # Not critical if this fails

# ============================================
# KHAYAL AGENT FUNCTION
# ============================================

def get_khayal_response(user_message: str) -> str:
    """
    Get Khayal's response to a user message
    
    Args:
        user_message: The message from the user
    
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
        
        user_prompt = f"[{time_context}] User says: {user_message}"
        
        # Generate response using Groq
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
    """
    Main webhook endpoint for WhatsApp
    - GET: Webhook verification (Meta's requirement)
    - POST: Receive incoming messages
    """
    
    if request.method == "GET":
        return verify_webhook()
    elif request.method == "POST":
        return handle_incoming_message()

def verify_webhook():
    """
    Verify webhook with Meta
    This is called when you first set up the webhook in Meta Developer Console
    """
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
    """
    Handle incoming WhatsApp messages
    Extract message, process with Khayal, send response
    """
    try:
        data = request.json
        
        print(f"\n{'='*60}")
        print("📩 INCOMING MESSAGE")
        print(f"{'='*60}")
        print(f"Raw data: {json.dumps(data, indent=2)}")
        
        # Extract message details
        # WhatsApp sends messages in this structure:
        # data["entry"][0]["changes"][0]["value"]["messages"][0]
        
        if "entry" not in data:
            print("⚠️  No entry field in data")
            return "No entry", 200
        
        entry = data["entry"][0]
        changes = entry.get("changes", [])
        
        if not changes:
            print("⚠️  No changes in entry")
            return "No changes", 200
        
        value = changes[0].get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            print("⚠️  No messages in value (might be a status update)")
            return "No messages", 200
        
        # Get message details
        message = messages[0]
        message_id = message.get("id")
        from_number = message.get("from")
        timestamp = message.get("timestamp")
        
        # Check message type
        message_type = message.get("type")
        
        print(f"\n📋 Message Details:")
        print(f"  ID: {message_id}")
        print(f"  From: {from_number}")
        print(f"  Type: {message_type}")
        print(f"  Timestamp: {timestamp}")
        
        # Handle different message types
        if message_type == "text":
            user_message = message["text"]["body"]
            print(f"  Content: {user_message}")
            
            # Mark as read
            mark_message_as_read(message_id)
            
            # Get Khayal's response
            print(f"\n🤔 Processing with Khayal...")
            khayal_response = get_khayal_response(user_message)
            print(f"🌙 Khayal: {khayal_response}")
            
            # Send response
            print(f"\n📤 Sending response...")
            result = send_whatsapp_message(from_number, khayal_response)
            
            if "error" not in result:
                print(f"✅ Message sent successfully!")
            else:
                print(f"❌ Failed to send message: {result['error']}")
            
        elif message_type == "audio":
            # Voice note handling (Phase 3)
            print("🎤 Voice note received (not yet implemented)")
            send_whatsapp_message(
                from_number, 
                "Arrey, voice notes abhi implement nahi hue yaar! Text bhejo for now 😊"
            )
            
        elif message_type == "image":
            # Image handling
            print("📸 Image received (not yet implemented)")
            send_whatsapp_message(
                from_number,
                "Images ka support bhi aa jayega jaldi! For now, text mein batao kya hai? 😊"
            )
            
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
# HEALTH CHECK ENDPOINT
# ============================================

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Khayal WhatsApp Webhook",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route("/", methods=["GET"])
def home():
    """Home endpoint"""
    return """
    <h1>🌙 Khayal WhatsApp Webhook</h1>
    <p>Server is running!</p>
    <ul>
        <li><strong>Webhook endpoint:</strong> /webhook</li>
        <li><strong>Health check:</strong> /health</li>
    </ul>
    <p>Configure this URL in Meta Developer Console to start receiving messages.</p>
    """

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌙 KHAYAL WHATSAPP WEBHOOK SERVER")
    print("="*60)
    print(f"Phone Number ID: {PHONE_NUMBER_ID[:10]}..." if PHONE_NUMBER_ID else "❌ Not configured")
    print(f"Access Token: {'✅ Configured' if WHATSAPP_ACCESS_TOKEN else '❌ Not configured'}")
    print(f"Verify Token: {'✅ Configured' if WEBHOOK_VERIFY_TOKEN else '❌ Not configured'}")
    print(f"Groq API Key: {'✅ Configured' if GROQ_API_KEY else '❌ Not configured'}")
    print("="*60)
    
    if not all([PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, GROQ_API_KEY]):
        print("\n⚠️  WARNING: Missing required credentials!")
        print("Create a .env file with:")
        print("  PHONE_NUMBER_ID=your_phone_number_id")
        print("  WHATSAPP_ACCESS_TOKEN=your_access_token")
        print("  WEBHOOK_VERIFY_TOKEN=your_verify_token")
        print("  GROQ_API_KEY=your_groq_key")
        print("\n")
    
    print("\n🚀 Starting server on http://localhost:5000")
    print("📱 Webhook URL: http://localhost:5000/webhook")
    print("\n💡 Next steps:")
    print("  1. Run: ngrok http 5000")
    print("  2. Copy the ngrok HTTPS URL")
    print("  3. Configure in Meta Developer Console")
    print("="*60 + "\n")
    
    # Run Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)