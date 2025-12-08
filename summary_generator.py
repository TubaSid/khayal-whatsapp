# summary_generator.py
# Daily Summary Generator for Khayal

import os
from datetime import datetime, timedelta
from groq import Groq
import requests

class SummaryGenerator:
    """Generate and send daily emotional summaries"""
    
    def __init__(self, database, groq_client):
        self.db = database
        self.groq = groq_client
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    
    def generate_summary(self, user_id: int) -> str:
        """Generate daily summary for a user"""
        
        # Get today's messages
        messages = self.db.get_user_messages_today(user_id)
        
        if not messages:
            return None
        
        # Prepare conversation for summary
        conversation = "\n".join([
            f"{'User' if msg['is_user'] else 'Khayal'}: {msg['content']}"
            for msg in messages
        ])
        
        # Generate summary with Groq
        prompt = f"""You are Khayal, reviewing today's journal entries.

Today's conversation:
{conversation}

Create a warm, caring summary (2-3 sentences) that:
- Acknowledges their emotional journey today
- Highlights key moments or feelings
- Ends with gentle encouragement

Keep it natural and supportive, like a friend checking in.
Use "yaar" if it fits naturally (max once)."""

        try:
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are Khayal, a warm journaling companion."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=150
            )
            
            summary = response.choices[0].message.content
            
            # Add header
            full_message = f"🌙 *Din ka khulasa* (Your day in reflection)\n\n{summary}\n\n— Khayal"
            
            return full_message
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None
    
    def send_whatsapp_message(self, to_number: str, message: str) -> bool:
        """Send WhatsApp message"""
        url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending message to {to_number}: {e}")
            return False
    
    def send_all_summaries(self) -> list:
        """Send daily summaries to all active users"""
        
        results = []
        
        # Get all users who messaged today
        users = self.db.get_active_users_today()
        
        print(f"📊 Sending summaries to {len(users)} users...")
        
        for user in users:
            user_id = user['id']
            phone_number = user['phone_number']
            
            print(f"\n👤 Processing user {phone_number}...")
            
            # Generate summary
            summary = self.generate_summary(user_id)
            
            if summary:
                # Send via WhatsApp
                success = self.send_whatsapp_message(phone_number, summary)
                
                if success:
                    print(f"✅ Summary sent to {phone_number}")
                    results.append({
                        'user_id': user_id,
                        'phone_number': phone_number,
                        'status': 'sent'
                    })
                else:
                    print(f"❌ Failed to send to {phone_number}")
                    results.append({
                        'user_id': user_id,
                        'phone_number': phone_number,
                        'status': 'failed'
                    })
            else:
                print(f"⚠️  No summary generated for {phone_number}")
                results.append({
                    'user_id': user_id,
                    'phone_number': phone_number,
                    'status': 'no_messages'
                })
        
        return results