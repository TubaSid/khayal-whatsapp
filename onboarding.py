# onboarding.py
# User Onboarding & Preferences System
# Professional first-time user experience

from typing import Dict, Optional
from datetime import datetime, time
import json
import re

class OnboardingManager:
    """Manage user onboarding and preferences"""
    
    def __init__(self, database):
        self.db = database
        self._create_preferences_table()
    
    def _create_preferences_table(self):
        """Create user preferences table"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                language_preference TEXT DEFAULT 'mixed',
                summary_time TEXT DEFAULT '22:00',
                summary_enabled BOOLEAN DEFAULT 1,
                timezone TEXT DEFAULT 'Asia/Kolkata',
                onboarding_completed BOOLEAN DEFAULT 0,
                onboarding_step INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        self.db.conn.commit()
    
    def is_new_user(self, user_id: int) -> bool:
        """Check if user is brand new"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM messages
            WHERE user_id = ?
        """, (user_id,))
        
        message_count = cursor.fetchone()['count']
        return message_count == 0
    
    def is_onboarding_complete(self, user_id: int) -> bool:
        """Check if user completed onboarding"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT onboarding_completed
            FROM user_preferences
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result is None:
            # No preferences record exists - user is new
            return False
        
        # Check the boolean value
        completed = result['onboarding_completed']
        
        # Handle both integer (0/1) and boolean
        return bool(completed) if completed is not None else False
    
    def get_onboarding_step(self, user_id: int) -> int:
        """Get current onboarding step"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT onboarding_step
            FROM user_preferences
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return result['onboarding_step']
        
        # Create preferences record
        cursor.execute("""
            INSERT INTO user_preferences (user_id, onboarding_step)
            VALUES (?, 0)
        """, (user_id,))
        self.db.conn.commit()
        
        return 0
    
    def set_onboarding_step(self, user_id: int, step: int):
        """Update onboarding step"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            UPDATE user_preferences
            SET onboarding_step = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (step, user_id))
        
        self.db.conn.commit()
    
    def complete_onboarding(self, user_id: int):
        """Mark onboarding as complete"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            UPDATE user_preferences
            SET onboarding_completed = 1,
                onboarding_step = -1,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
        
        self.db.conn.commit()
    
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
    
    def process_onboarding_response(
        self,
        user_id: int,
        current_step: int,
        user_response: str
    ) -> Dict:
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
        
        # Pattern 1: "9:30 PM" or "21:00"
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
        
        # Pattern 2: "9 PM" or "9PM"
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
        
        # Pattern 3: Just "9" or "21"
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
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM user_preferences
            WHERE user_id = ?
        """, (user_id,))
        
        if cursor.fetchone()['count'] == 0:
            cursor.execute(f"""
                INSERT INTO user_preferences (user_id, {key})
                VALUES (?, ?)
            """, (user_id, value))
        else:
            cursor.execute(f"""
                UPDATE user_preferences
                SET {key} = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (value, user_id))
        
        self.db.conn.commit()
    
    def get_preferences(self, user_id: int) -> Dict:
        """Get all user preferences"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM user_preferences
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return dict(result)
        
        return {
            "name": None,
            "language_preference": "mixed",
            "summary_time": "22:00",
            "summary_enabled": True,
            "timezone": "Asia/Kolkata",
            "onboarding_completed": False
        }


# TESTING
if __name__ == "__main__":
    from database import KhayalDatabase
    
    print("="*60)
    print("👋 TESTING ONBOARDING SYSTEM")
    print("="*60)
    
    db = KhayalDatabase("khayal_test.db")
    onboarding = OnboardingManager(db)
    
    test_phone = "919999999999"
    user_id = db.get_or_create_user(test_phone)
    
    print(f"\n✅ Created test user: {user_id}")
    print(f"Is new user: {onboarding.is_new_user(user_id)}")
    print(f"Onboarding complete: {onboarding.is_onboarding_complete(user_id)}")
    
    print("\n" + "─"*60)
    print("SIMULATING ONBOARDING FLOW")
    print("─"*60)
    
    step = onboarding.get_onboarding_step(user_id)
    welcome = onboarding.get_onboarding_message(step)
    print(f"\n🌙 Khayal:")
    print(welcome["message"])
    
    print(f"\n👤 User: Hi!")
    result = onboarding.process_onboarding_response(user_id, step, "Hi!")
    print(f"\n🌙 Khayal:")
    print(result["message"])
    
    print(f"\n👤 User: I'm Rahul")
    result = onboarding.process_onboarding_response(user_id, 1, "I'm Rahul")
    print(f"\n🌙 Khayal:")
    print(result["message"])
    
    print(f"\n👤 User: 9 PM please")
    result = onboarding.process_onboarding_response(user_id, 2, "9 PM please")
    print(f"\n🌙 Khayal:")
    print(result["message"])
    
    print(f"\n👤 User: Mixed")
    result = onboarding.process_onboarding_response(user_id, 3, "Mixed")
    print(f"\n🌙 Khayal:")
    print(result["message"])
    
    print(f"\n{'─'*60}")
    print("FINAL STATE")
    print(f"{'─'*60}")
    print(f"Onboarding complete: {onboarding.is_onboarding_complete(user_id)}")
    
    prefs = onboarding.get_preferences(user_id)
    print(f"\nUser Preferences:")
    print(f"  Name: {prefs['name']}")
    print(f"  Summary time: {prefs['summary_time']}")
    print(f"  Language: {prefs['language_preference']}")
    print(f"  Summary enabled: {prefs['summary_enabled']}")
    
    print("\n" + "="*60)
    print("✅ Onboarding system testing complete!")
    print("="*60)
    
    db.close()