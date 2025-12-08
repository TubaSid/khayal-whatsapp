# scheduler.py  
# Scheduler for 10 PM Daily Summaries - Phase 5
# Runs in background and sends summaries at 10 PM

import schedule
import time
import requests
from datetime import datetime, date
from typing import List
import os
from dotenv import load_dotenv

from groq import Groq
from database import KhayalDatabase
from summary_generator import DailySummaryGenerator

load_dotenv()

# WhatsApp configuration
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize components
db = KhayalDatabase("khayal.db")
groq_client = Groq(api_key=GROQ_API_KEY)
summary_generator = DailySummaryGenerator(db, groq_client)

def send_whatsapp_message(to_number: str, message_text: str) -> bool:
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
        print(f"✅ Summary sent to {to_number}")
        return True
    except Exception as e:
        print(f"❌ Error sending to {to_number}: {e}")
        return False

def get_active_users() -> List[tuple]:
    """Get all users who messaged today"""
    
    cursor = db.conn.cursor()
    today = date.today()
    
    # Get users who sent messages today
    cursor.execute("""
        SELECT DISTINCT u.id, u.phone_number, u.name
        FROM users u
        JOIN messages m ON u.id = m.user_id
        WHERE m.message_type = 'user'
        AND date(m.timestamp) = ?
    """, (today,))
    
    return cursor.fetchall()

def send_daily_summaries():
    """Main function to send summaries to all active users"""
    
    print("\n" + "="*60)
    print(f"🌙 SENDING DAILY SUMMARIES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    active_users = get_active_users()
    
    if not active_users:
        print("📭 No active users today. No summaries to send.")
        print("="*60 + "\n")
        return
    
    print(f"\n👥 Found {len(active_users)} active user(s) today\n")
    
    summaries_sent = 0
    summaries_skipped = 0
    
    for user_id, phone_number, name in active_users:
        print(f"{'─'*60}")
        print(f"Processing: {name or 'User'} ({phone_number})")
        print(f"{'─'*60}")
        
        # Generate summary
        result = summary_generator.generate_daily_summary(user_id)
        
        if result['should_send']:
            print(f"📝 Generated summary ({result['message_count']} messages)")
            print(f"Emotional arc: {result['emotional_arc'].get('trend', 'stable')}")
            
            # Send via WhatsApp
            success = send_whatsapp_message(phone_number, result['summary'])
            
            if success:
                # Save to database
                summary_generator.save_summary(
                    user_id=user_id,
                    summary_date=date.today(),
                    summary_text=result['summary'],
                    emotional_arc=result['emotional_arc']
                )
                summaries_sent += 1
                print("💾 Saved to database")
            else:
                summaries_skipped += 1
        else:
            print(f"⏭️  Skipped (only {result['message_count']} message(s) today)")
            summaries_skipped += 1
        
        print()
    
    print("="*60)
    print(f"✅ Summary job complete!")
    print(f"   Sent: {summaries_sent}")
    print(f"   Skipped: {summaries_skipped}")
    print("="*60 + "\n")

def test_summary_now():
    """Test function to send summary immediately (for testing)"""
    
    print("\n🧪 TEST MODE: Sending summaries NOW\n")
    send_daily_summaries()

# ========================================
# SCHEDULER CONFIGURATION
# ========================================

def start_scheduler():
    """Start the scheduler for 10 PM summaries"""
    
    print("\n" + "="*60)
    print("⏰ DAILY SUMMARY SCHEDULER STARTED")
    print("="*60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print("\n📋 Schedule:")
    print("  • Daily summaries: 10:00 PM")
    print("\n💡 Commands:")
    print("  • Ctrl+C to stop")
    print("="*60 + "\n")
    
    # Schedule daily summary at 10 PM
    schedule.every().day.at("22:00").do(send_daily_summaries)
    
    print("⏳ Waiting for scheduled time...\n")
    print("(Next summary: Today at 10:00 PM)\n")
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n⏹️  Scheduler stopped by user")
        print("="*60 + "\n")
        db.close()

# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode: send summaries immediately
        test_summary_now()
        db.close()
    else:
        # Normal mode: start scheduler
        start_scheduler()