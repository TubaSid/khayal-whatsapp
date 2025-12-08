# database.py
# Khayal Database Manager - Phase 2
# Stores conversations, mood data, and user patterns

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class KhayalDatabase:
    """Manage Khayal's conversation and mood database"""
    
    def __init__(self, db_path: str = "khayal.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.create_tables()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT UNIQUE NOT NULL,
                name TEXT,
                personality_mode TEXT DEFAULT 'bollywood',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_type TEXT NOT NULL,  -- 'user' or 'khayal'
                content TEXT NOT NULL,
                mood TEXT,  -- happy, sad, anxious, stressed, excited, etc.
                intensity INTEGER,  -- 1-10 scale
                themes TEXT,  -- JSON array of themes
                needs_support BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Mood patterns table (for tracking emotional trends)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mood_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                dominant_mood TEXT,
                mood_count INTEGER DEFAULT 1,
                average_intensity REAL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date, dominant_mood)
            )
        """)
        
        # Daily summaries table (for 10 PM summaries - Phase 5)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                summary TEXT,
                emotional_arc TEXT,  -- JSON of mood progression
                sent_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, date)
            )
        """)
        
        self.conn.commit()
        print("✅ Database tables created/verified")
    
    # ========================================
    # USER MANAGEMENT
    # ========================================
    
    def get_or_create_user(self, phone_number: str, name: str = None) -> int:
        """Get existing user or create new one, return user_id"""
        
        cursor = self.conn.cursor()
        
        # Try to get existing user
        cursor.execute(
            "SELECT id FROM users WHERE phone_number = ?",
            (phone_number,)
        )
        
        result = cursor.fetchone()
        
        if result:
            user_id = result['id']
            # Update last_active
            cursor.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            self.conn.commit()
            return user_id
        else:
            # Create new user
            cursor.execute(
                "INSERT INTO users (phone_number, name) VALUES (?, ?)",
                (phone_number, name)
            )
            self.conn.commit()
            return cursor.lastrowid
    
    # ========================================
    # MESSAGE STORAGE
    # ========================================
    
    def store_user_message(
        self,
        user_id: int,
        content: str,
        mood: str = None,
        intensity: int = None,
        themes: List[str] = None,
        needs_support: bool = False
    ) -> int:
        """Store a user message with mood data"""
        
        cursor = self.conn.cursor()
        
        themes_json = json.dumps(themes) if themes else None
        
        cursor.execute("""
            INSERT INTO messages 
            (user_id, message_type, content, mood, intensity, themes, needs_support)
            VALUES (?, 'user', ?, ?, ?, ?, ?)
        """, (user_id, content, mood, intensity, themes_json, needs_support))
        
        self.conn.commit()
        
        # Update mood patterns
        if mood:
            self._update_mood_pattern(user_id, mood, intensity)
        
        return cursor.lastrowid
    
    def store_khayal_message(
        self,
        user_id: int,
        content: str
    ) -> int:
        """Store Khayal's response"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO messages 
            (user_id, message_type, content)
            VALUES (?, 'khayal', ?)
        """, (user_id, content))
        
        self.conn.commit()
        return cursor.lastrowid
    
    # ========================================
    # CONVERSATION RETRIEVAL
    # ========================================
    
    def get_recent_messages(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation history"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                message_type,
                content,
                mood,
                intensity,
                themes,
                timestamp
            FROM messages
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            msg = dict(row)
            if msg['themes']:
                msg['themes'] = json.loads(msg['themes'])
            messages.append(msg)
        
        return list(reversed(messages))  # Return in chronological order
    
    def get_conversation_context(
        self,
        user_id: int,
        limit: int = 5
    ) -> str:
        """Get formatted conversation context for AI"""
        
        messages = self.get_recent_messages(user_id, limit)
        
        context_parts = []
        for msg in messages:
            role = "User" if msg['message_type'] == 'user' else "Khayal"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    # ========================================
    # MOOD ANALYSIS
    # ========================================
    
    def _update_mood_pattern(
        self,
        user_id: int,
        mood: str,
        intensity: int = None
    ):
        """Update mood patterns for the day"""
        
        cursor = self.conn.cursor()
        today = datetime.now().date()
        
        # Try to update existing pattern
        cursor.execute("""
            INSERT INTO mood_patterns (user_id, date, dominant_mood, mood_count, average_intensity)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(user_id, date, dominant_mood) 
            DO UPDATE SET 
                mood_count = mood_count + 1,
                average_intensity = (average_intensity * mood_count + ?) / (mood_count + 1)
        """, (user_id, today, mood, intensity or 5, intensity or 5))
        
        self.conn.commit()
    
    def get_mood_history(
        self,
        user_id: int,
        days: int = 7
    ) -> List[Dict]:
        """Get mood patterns for last N days"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                date,
                dominant_mood,
                mood_count,
                average_intensity
            FROM mood_patterns
            WHERE user_id = ?
            AND date >= date('now', '-' || ? || ' days')
            ORDER BY date DESC, mood_count DESC
        """, (user_id, days))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_today_moods(self, user_id: int) -> List[str]:
        """Get all moods detected today"""
        
        cursor = self.conn.cursor()
        today = datetime.now().date()
        
        cursor.execute("""
            SELECT DISTINCT mood
            FROM messages
            WHERE user_id = ?
            AND date(timestamp) = ?
            AND mood IS NOT NULL
        """, (user_id, today))
        
        return [row['mood'] for row in cursor.fetchall()]
    
    # ========================================
    # STATISTICS
    # ========================================
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        
        cursor = self.conn.cursor()
        
        # Total messages
        cursor.execute(
            "SELECT COUNT(*) as total FROM messages WHERE user_id = ? AND message_type = 'user'",
            (user_id,)
        )
        total_messages = cursor.fetchone()['total']
        
        # Most common mood
        cursor.execute("""
            SELECT mood, COUNT(*) as count
            FROM messages
            WHERE user_id = ? AND mood IS NOT NULL
            GROUP BY mood
            ORDER BY count DESC
            LIMIT 1
        """, (user_id,))
        
        common_mood = cursor.fetchone()
        
        # Average intensity
        cursor.execute("""
            SELECT AVG(intensity) as avg_intensity
            FROM messages
            WHERE user_id = ? AND intensity IS NOT NULL
        """, (user_id,))
        
        avg_intensity = cursor.fetchone()['avg_intensity']
        
        return {
            "total_messages": total_messages,
            "most_common_mood": common_mood['mood'] if common_mood else None,
            "average_intensity": round(avg_intensity, 1) if avg_intensity else None
        }
    
    # ========================================
    # DAILY SUMMARY (for Phase 5)
    # ========================================
    
    def get_messages_for_date(
        self,
        user_id: int,
        date: str = None
    ) -> List[Dict]:
        """Get all messages for a specific date"""
        
        if date is None:
            date = datetime.now().date()
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM messages
            WHERE user_id = ?
            AND date(timestamp) = ?
            ORDER BY timestamp ASC
        """, (user_id, date))
        
        messages = []
        for row in cursor.fetchall():
            msg = dict(row)
            if msg['themes']:
                msg['themes'] = json.loads(msg['themes'])
            messages.append(msg)
        
        return messages
    
    def store_daily_summary(
        self,
        user_id: int,
        date: str,
        summary: str,
        emotional_arc: Dict
    ):
        """Store the 10 PM daily summary"""
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO daily_summaries
            (user_id, date, summary, emotional_arc, sent_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, date, summary, json.dumps(emotional_arc)))
        
        self.conn.commit()
    
    # ========================================
    # CLEANUP
    # ========================================
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ========================================
# TESTING & DEMO
# ========================================

if __name__ == "__main__":
    print("="*60)
    print("🗄️  TESTING KHAYAL DATABASE")
    print("="*60)
    
    # Initialize database
    db = KhayalDatabase("khayal_test.db")
    
    # Create test user
    user_id = db.get_or_create_user("", "Test User")
    print(f"\n✅ User created/retrieved: ID = {user_id}")
    
    # Store some test messages
    print("\n📝 Storing test messages...")
    
    db.store_user_message(
        user_id=user_id,
        content="Yaar, aaj bahut stressed hoon",
        mood="anxious",
        intensity=7,
        themes=["work", "stress"],
        needs_support=True
    )
    
    db.store_khayal_message(
        user_id=user_id,
        content="Arrey, I hear you yaar. Work stress is real."
    )
    
    db.store_user_message(
        user_id=user_id,
        content="Thanks, that helped!",
        mood="grateful",
        intensity=3,
        themes=["gratitude"],
        needs_support=False
    )
    
    # Retrieve conversation
    print("\n📜 Recent conversation:")
    messages = db.get_recent_messages(user_id, limit=5)
    for msg in messages:
        role = "👤" if msg['message_type'] == 'user' else "🌙"
        mood_info = f" [{msg['mood']}:{msg['intensity']}]" if msg['mood'] else ""
        print(f"{role} {msg['content']}{mood_info}")
    
    # Get stats
    print("\n📊 User statistics:")
    stats = db.get_user_stats(user_id)
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Most common mood: {stats['most_common_mood']}")
    print(f"  Average intensity: {stats['average_intensity']}")
    
    # Get mood history
    print("\n📈 Mood history:")
    mood_history = db.get_mood_history(user_id, days=7)
    for pattern in mood_history:
        print(f"  {pattern['date']}: {pattern['dominant_mood']} (×{pattern['mood_count']}, avg: {pattern['average_intensity']:.1f})")
    
    print("\n" + "="*60)
    print("✅ Database testing complete!")
    print("="*60)
    
    db.close()