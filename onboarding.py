# onboarding.py
# User Onboarding & Preferences System (FIXED FOR POSTGRESQL)

from typing import Dict, Optional
from datetime import datetime, time
import json
import re
import os

# Detect if we're using PostgreSQL
USE_POSTGRES = os.getenv('DATABASE_URL') is not None

class OnboardingManager:
    """Manage user onboarding and preferences"""
    
    def __init__(self, database):
        self.db = database
        self.use_postgres = USE_POSTGRES
        self._create_preferences_table()
    
    def _get_placeholder(self):
        """Get SQL placeholder based on database type"""
        return '%s' if self.use_postgres else '?'
    
    def _create_preferences_table(self):
        """Create user preferences table"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if self.use_postgres:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id),
                    name VARCHAR(255),
                    language_preference VARCHAR(20) DEFAULT 'mixed',
                    summary_time VARCHAR(10) DEFAULT '22:00',
                    summary_enabled BOOLEAN DEFAULT TRUE,
                    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
                    onboarding_complete BOOLEAN DEFAULT FALSE,
                    onboarding_step INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    language_preference TEXT DEFAULT 'mixed',
                    summary_time TEXT DEFAULT '22:00',
                    summary_enabled INTEGER DEFAULT 1,
                    timezone TEXT DEFAULT 'Asia/Kolkata',
                    onboarding_complete INTEGER DEFAULT 0,
                    onboarding_step INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
        
        conn.commit()
        conn.close()
    
    def is_new_user(self, user_id: int) -> bool:
        """Check if user is brand new"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        ph = self._get_placeholder()
        cursor.execute(f"""
            SELECT COUNT(*) as count
            FROM messages
            WHERE user_id = {ph}
        """, (user_id,))
        
        result = cursor.fetchone()
        message_count = result['count'] if self.use_postgres else result[0]
        conn.close()
        return message_count == 0
    
    def is_onboarding_complete(self, user_id: int) -> bool:
        """Check if user completed onboarding"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        ph = self._get_placeholder()
        cursor.execute(f"""
            SELECT onboarding_complete, onboarding_step
            FROM user_preferences
            WHERE user_id = {ph}
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result is None:
            return False
        
        # Check both onboarding_complete flag AND step = -1
        completed = result['onboarding_complete'] if self.use_postgres else result[0]
        step = result['onboarding_step'] if self.use_postgres else result[1]
        
        # Double-check: complete flag should be True AND step should be -1
        return bool(completed) and step == -1
    
    def get_onboarding_step(self, user_id: int) -> int:
        """Get current onboarding step"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        ph = self._get_placeholder()
        cursor.execute(f"""
            SELECT onboarding_step, onboarding_complete
            FROM user_preferences
            WHERE user_id = {ph}
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            # If onboarding is complete, always return -1
            complete = result['onboarding_complete'] if self.use_postgres else result[1]
            if complete:
                conn.close()
                return -1
            
            # Otherwise return the step
            step = result['onboarding_step'] if self.use_postgres else result[0]
            conn.close()
            return step
        
        # Create preferences record only if doesn't exist
        try:
            cursor.execute(f"""
                INSERT INTO user_preferences (user_id, onboarding_step, onboarding_complete)
                VALUES ({ph}, 0, {'FALSE' if self.use_postgres else '0'})
            """, (user_id,))
            conn.commit()
        except:
            # Already exists, ignore
            pass
        
        conn.close()
        return 0
    
    def set_onboarding_step(self, user_id: int, step: int):
        """Update onboarding step"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        ph = self._get_placeholder()
        cursor.execute(f"""
            UPDATE user_preferences
            SET onboarding_step = {ph}
            WHERE user_id = {ph}
        """, (step, user_id))
        
        conn.commit()
        conn.close()
    
    def complete_onboarding(self, user_id: int):
        """Mark onboarding as complete"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        ph = self._get_placeholder()
        if self.use_postgres:
            cursor.execute(f"""
                UPDATE user_preferences
                SET onboarding_complete = TRUE,
                    onboarding_step = -1
                WHERE user_id = {ph}
            """, (user_id,))
        else:
            cursor.execute(f"""
                UPDATE user_preferences
                SET onboarding_complete = 1,
                    onboarding_step = -1
                WHERE user_id = {ph}
            """, (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_onboarding_message(self, step: int) -> Dict:
        """Get onboarding message for specific step"""
        
        messages = {
            0: {
                "message": """Hey! I'm Khayal 🌙

Think of me as your journaling companion - someone who listens, remembers, and cares.

Share how you're feeling anytime, and I'll be here.

Every night at 10 PM, I'll send you a warm summary of your day to help you reflect.

Sound good? 😊

(Reply with anything to continue)""",
                "next_step": 1,
                "expects_input": True
            },
            
            1: {
                "message": """Great! I'm excited to get to know you.

What should I call you? 

(Your first name or nickname is perfect)""",
                "next_step": 2,
                "expects_input": True
            },
            
            2: {
                "message": """Nice to meet you, {name}! 

I'll send you a daily summary at 10 PM by default. Does that time work for you?

Reply:
• "Yes" to keep 10 PM
• Or tell me your preferred time (like "9 PM" or "11:30 PM")""",
                "next_step": 3,
                "expects_input": True
            },
            
            3: {
                "message": """Perfect! ✅

One more thing - how would you like me to talk?

Reply with:
• "English" - mostly English
• "Urdu/Hindi" - mostly Hindi/Urdu
• "Mixed" - natural mix (recommended)

(You can always change this later by saying "settings")""",
                "next_step": 4,
                "expects_input": True
            },
            
            4: {
                "message": """All set! 🎉

From now on:
• Message me anytime about how you're feeling
• I'll listen and respond with care
• Every night at {time}, I'll send a summary of your day
• Say "settings" anytime to change preferences
• Say "help" if you need guidance

Privacy note: Your messages are stored privately and never shared. You can delete everything anytime by saying "delete my data".

So... kya haal hai? How are you feeling today? 😊""",
                "next_step": -1,
                "expects_input": False
            }
        }
        
        return messages.get(step, messages[0])
    
    def process_onboarding_response(self, user_id: int, current_step: int, user_response: str) -> Dict:
        """Process user's response during onboarding"""
        
        response_lower = user_response.lower().strip()
        
        if current_step == 0:
            self.set_onboarding_step(user_id, 1)
            return {
                "message": self.get_onboarding_message(1)["message"],
                "next_step": 1,
                "complete": False
            }
        
        elif current_step == 1:
            name = user_response.strip()[:50]
            self.set_preference(user_id, "name", name)
            self.set_onboarding_step(user_id, 2)
            msg = self.get_onboarding_message(2)["message"].format(name=name)
            
            return {
                "message": msg,
                "next_step": 2,
                "complete": False
            }
        
        elif current_step == 2:
            summary_time = self._parse_time_preference(response_lower)
            self.set_preference(user_id, "summary_time", summary_time)
            self.set_onboarding_step(user_id, 3)
            
            return {
                "message": self.get_onboarding_message(3)["message"],
                "next_step": 3,
                "complete": False
            }
        
        elif current_step == 3:
            if "english" in response_lower:
                lang = "english"
            elif "hindi" in response_lower or "urdu" in response_lower:
                lang = "hindi"
            else:
                lang = "mixed"
            
            self.set_preference(user_id, "language_preference", lang)
            self.complete_onboarding(user_id)
            
            prefs = self.get_preferences(user_id)
            time_str = prefs.get('summary_time', '22:00')
            
            hour, minute = time_str.split(':')
            if minute == '00':
                time_display = f"{int(hour) % 12 or 12} {'PM' if int(hour) >= 12 else 'AM'}"
            else:
                time_display = f"{int(hour) % 12 or 12}:{minute} {'PM' if int(hour) >= 12 else 'AM'}"
            
            msg = self.get_onboarding_message(4)["message"].format(time=time_display)
            
            return {
                "message": msg,
                "next_step": -1,
                "complete": True
            }
        
        return {
            "message": "Sorry, something went wrong. Let's start over! What's your name?",
            "next_step": 1,
            "complete": False
        }
    
    def _parse_time_preference(self, time_str: str) -> str:
        """Parse user's time preference into HH:MM format"""
        
        time_str = time_str.lower().strip()
        
        if "yes" in time_str or "ok" in time_str or "fine" in time_str:
            return "22:00"
        
        match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            period = match.group(3)
            
            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
        
        match = re.search(r'(\d{1,2})\s*(am|pm)', time_str)
        if match:
            hour = int(match.group(1))
            period = match.group(2)
            
            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            if 0 <= hour <= 23:
                return f"{hour:02d}:00"
        
        match = re.search(r'^\d{1,2}$', time_str)
        if match:
            hour = int(match.group(0))
            
            if 1 <= hour <= 11:
                hour += 12
            
            if 0 <= hour <= 23:
                return f"{hour:02d}:00"
        
        return "22:00"
    
    def set_preference(self, user_id: int, key: str, value: any):
        """Set a specific preference"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        ph = self._get_placeholder()
        
        cursor.execute(f"""
            SELECT COUNT(*) as count
            FROM user_preferences
            WHERE user_id = {ph}
        """, (user_id,))
        
        result = cursor.fetchone()
        count = result['count'] if self.use_postgres else result[0]
        
        if count == 0:
            cursor.execute(f"""
                INSERT INTO user_preferences (user_id, {key})
                VALUES ({ph}, {ph})
            """, (user_id, value))
        else:
            cursor.execute(f"""
                UPDATE user_preferences
                SET {key} = {ph}
                WHERE user_id = {ph}
            """, (value, user_id))
        
        conn.commit()
        conn.close()
    
    def get_preferences(self, user_id: int) -> Dict:
        """Get all user preferences"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        ph = self._get_placeholder()
        cursor.execute(f"""
            SELECT *
            FROM user_preferences
            WHERE user_id = {ph}
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return dict(result)
        
        return {
            "name": None,
            "language_preference": "mixed",
            "summary_time": "22:00",
            "summary_enabled": True,
            "timezone": "Asia/Kolkata",
            "onboarding_complete": False
        }