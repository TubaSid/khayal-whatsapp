# database.py
# Universal Database Handler for Khayal - SQLite (local) + PostgreSQL (production)

import os
from datetime import datetime, timedelta

# Detect environment
DATABASE_URL = os.getenv('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    print("🐘 Using PostgreSQL (Production)")
else:
    import sqlite3
    print("📁 Using SQLite (Local)")

class KhayalDatabase:
    """Main database class for Khayal"""
    
    def __init__(self, sqlite_path="khayal.db"):
        self.sqlite_path = sqlite_path
        self.use_postgres = USE_POSTGRES
        
        # 🚨 FIX 1: Establish and assign the persistent connection to 'self.conn'
        if self.use_postgres:
            self.conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            self.conn = conn
            
        # Initialize tables using the persistent connection
        self.init_database() 
    
    # 🚨 NOTE: get_connection is no longer needed but kept for potential future use, 
    # though methods will now use self.conn directly.
    def get_connection(self):
        """Returns the persistent database connection."""
        return self.conn
    
    def init_database(self):
        """Initialize tables using the persistent connection."""
        # Use self.conn directly
        cursor = self.conn.cursor() 
        
        if self.use_postgres:
            # PostgreSQL
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    phone_number VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    content TEXT NOT NULL,
                    is_user BOOLEAN DEFAULT TRUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    mood VARCHAR(50),
                    intensity INTEGER,
                    themes TEXT,
                    needs_support BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id),
                    name VARCHAR(255),
                    language VARCHAR(10) DEFAULT 'en',
                    onboarding_complete BOOLEAN DEFAULT FALSE,
                    onboarding_step INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(timestamp)')
            
        else:
            # SQLite
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT UNIQUE NOT NULL,
                    name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    content TEXT NOT NULL,
                    is_user INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    mood TEXT,
                    intensity INTEGER,
                    themes TEXT,
                    needs_support INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    language TEXT DEFAULT 'en',
                    onboarding_complete INTEGER DEFAULT 0,
                    onboarding_step INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
        
        self.conn.commit()
        # 🚨 FIX 2: REMOVE conn.close()
        print(f"✅ Database ready ({'PostgreSQL' if self.use_postgres else 'SQLite'})")
    
    def get_or_create_user(self, phone_number: str) -> int:
        """Get or create user"""
        # 🚨 FIX 3: Use self.conn directly
        cursor = self.conn.cursor()
        
        if self.use_postgres:
            cursor.execute('SELECT id FROM users WHERE phone_number = %s', (phone_number,))
            result = cursor.fetchone()
            if result:
                user_id = result['id']
            else:
                cursor.execute(
                    'INSERT INTO users (phone_number) VALUES (%s) RETURNING id',
                    (phone_number,)
                )
                user_id = cursor.fetchone()['id']
                self.conn.commit()
        else:
            cursor.execute('SELECT id FROM users WHERE phone_number = ?', (phone_number,))
            result = cursor.fetchone()
            if result:
                user_id = result[0]
            else:
                cursor.execute('INSERT INTO users (phone_number) VALUES (?)', (phone_number,))
                user_id = cursor.lastrowid
                self.conn.commit()
        
        # 🚨 FIX 4: REMOVE conn.close()
        return user_id
    
    def store_user_message(self, user_id: int, content: str, mood: str = None,
                           intensity: int = None, themes: list = None, needs_support: bool = False):
        """Store user message"""
        # 🚨 FIX 5: Use self.conn directly
        cursor = self.conn.cursor()
        
        themes_str = ','.join(themes) if themes else None
        
        if self.use_postgres:
            cursor.execute('''
                INSERT INTO messages (user_id, content, is_user, mood, intensity, themes, needs_support)
                VALUES (%s, %s, TRUE, %s, %s, %s, %s)
            ''', (user_id, content, mood, intensity, themes_str, needs_support))
        else:
            cursor.execute('''
                INSERT INTO messages (user_id, content, is_user, mood, intensity, themes, needs_support)
                VALUES (?, ?, 1, ?, ?, ?, ?)
            ''', (user_id, content, mood, intensity, themes_str, 1 if needs_support else 0))
        
        self.conn.commit()
        # 🚨 FIX 6: REMOVE conn.close()
    
    def store_khayal_message(self, user_id: int, content: str):
        """Store Khayal's message"""
        # 🚨 FIX 7: Use self.conn directly
        cursor = self.conn.cursor()
        
        if self.use_postgres:
            cursor.execute('''
                INSERT INTO messages (user_id, content, is_user)
                VALUES (%s, %s, FALSE)
            ''', (user_id, content))
        else:
            cursor.execute('''
                INSERT INTO messages (user_id, content, is_user)
                VALUES (?, ?, 0)
            ''', (user_id, content))
        
        self.conn.commit()
        # 🚨 FIX 8: REMOVE conn.close()
    
    def get_user_messages_today(self, user_id: int) -> list:
        """Get today's messages"""
        # 🚨 FIX 9: Use self.conn directly
        cursor = self.conn.cursor()
        
        if self.use_postgres:
            cursor.execute('''
                SELECT content, is_user, timestamp, mood
                FROM messages
                WHERE user_id = %s AND DATE(timestamp) = CURRENT_DATE
                ORDER BY timestamp ASC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT content, is_user, timestamp, mood
                FROM messages
                WHERE user_id = ? AND DATE(timestamp) = DATE('now')
                ORDER BY timestamp ASC
            ''', (user_id,))
        
        messages = [dict(row) for row in cursor.fetchall()]
        # 🚨 FIX 10: REMOVE conn.close()
        return messages
    
    def get_active_users_today(self) -> list:
        """Get active users today"""
        # 🚨 FIX 11: Use self.conn directly
        cursor = self.conn.cursor()
        
        if self.use_postgres:
            cursor.execute('''
                SELECT DISTINCT u.id, u.phone_number
                FROM users u
                JOIN messages m ON u.id = m.user_id
                WHERE DATE(m.timestamp) = CURRENT_DATE AND m.is_user = TRUE
            ''')
        else:
            cursor.execute('''
                SELECT DISTINCT u.id, u.phone_number
                FROM users u
                JOIN messages m ON u.id = m.user_id
                WHERE DATE(m.timestamp) = DATE('now') AND m.is_user = 1
            ''')
        
        users = [dict(row) for row in cursor.fetchall()]
        # 🚨 FIX 12: REMOVE conn.close()
        return users
    
    def get_recent_messages(self, user_id: int, limit: int = 10) -> list:
        """Get recent messages"""
        # 🚨 FIX 13: Use self.conn directly
        cursor = self.conn.cursor()
        
        if self.use_postgres:
            cursor.execute('''
                SELECT content, is_user, timestamp, mood
                FROM messages
                WHERE user_id = %s
                ORDER BY timestamp DESC LIMIT %s
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT content, is_user, timestamp, mood
                FROM messages
                WHERE user_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, limit))
        
        messages = [dict(row) for row in cursor.fetchall()]
        # 🚨 FIX 14: REMOVE conn.close()
        return list(reversed(messages))
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user stats"""
        # 🚨 FIX 15: Use self.conn directly
        cursor = self.conn.cursor()
        
        if self.use_postgres:
            cursor.execute('''
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT DATE(timestamp)) as days
                FROM messages
                WHERE user_id = %s AND is_user = TRUE
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT DATE(timestamp)) as days
                FROM messages
                WHERE user_id = ? AND is_user = 1
            ''', (user_id,))
        
        stats = dict(cursor.fetchone())
        # 🚨 FIX 16: REMOVE conn.close()
        return stats

# End of database.py