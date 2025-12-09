# database.py
# Production-Ready Database Handler - SQLite (local) + PostgreSQL (production)

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
    """Main database class - creates new connection for each operation"""
    
    def __init__(self, sqlite_path="khayal.db"):
        self.sqlite_path = sqlite_path
        self.use_postgres = USE_POSTGRES
        self.init_database()
    
    def get_connection(self):
        """Get fresh database connection - CRITICAL for production"""
        if self.use_postgres:
            return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn
    
    def init_database(self):
        """Initialize all tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                # PostgreSQL schema
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        phone_number VARCHAR(50) UNIQUE NOT NULL,
                        name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                        language_preference VARCHAR(20) DEFAULT 'mixed',
                        summary_time VARCHAR(10) DEFAULT '22:00',
                        summary_enabled BOOLEAN DEFAULT TRUE,
                        timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
                        onboarding_completed BOOLEAN DEFAULT FALSE,
                        onboarding_step INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(timestamp)')
                
            else:
                # SQLite schema
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        phone_number TEXT UNIQUE NOT NULL,
                        name TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_active DATETIME DEFAULT CURRENT_TIMESTAMP
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
                        language_preference TEXT DEFAULT 'mixed',
                        summary_time TEXT DEFAULT '22:00',
                        summary_enabled INTEGER DEFAULT 1,
                        timezone TEXT DEFAULT 'Asia/Kolkata',
                        onboarding_completed INTEGER DEFAULT 0,
                        onboarding_step INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')
            
            conn.commit()
            print(f"✅ Database initialized ({'PostgreSQL' if self.use_postgres else 'SQLite'})")
            
        except Exception as e:
            print(f"❌ Database init error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_or_create_user(self, phone_number: str) -> int:
        """Get or create user - with proper connection handling"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
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
                    conn.commit()
            else:
                cursor.execute('SELECT id FROM users WHERE phone_number = ?', (phone_number,))
                result = cursor.fetchone()
                
                if result:
                    user_id = result[0]
                else:
                    cursor.execute('INSERT INTO users (phone_number) VALUES (?)', (phone_number,))
                    user_id = cursor.lastrowid
                    conn.commit()
            
            return user_id
            
        except Exception as e:
            print(f"DB Error in get_or_create_user: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def store_user_message(self, user_id: int, content: str, mood: str = None,
                          intensity: int = None, themes: list = None, needs_support: bool = False):
        """Store user message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
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
            
            conn.commit()
            
        except Exception as e:
            print(f"DB Error in store_user_message: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def store_khayal_message(self, user_id: int, content: str):
        """Store Khayal's message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
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
            
            conn.commit()
            
        except Exception as e:
            print(f"DB Error in store_khayal_message: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_user_messages_today(self, user_id: int) -> list:
        """Get today's messages"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
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
            return messages
            
        except Exception as e:
            print(f"DB Error in get_user_messages_today: {e}")
            return []
        finally:
            conn.close()
    
    def get_active_users_today(self) -> list:
        """Get active users today"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
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
            return users
            
        except Exception as e:
            print(f"DB Error in get_active_users_today: {e}")
            return []
        finally:
            conn.close()
    
    def get_recent_messages(self, user_id: int, limit: int = 10) -> list:
        """Get recent messages for context"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                cursor.execute('''
                    SELECT content, is_user, timestamp, mood, themes
                    FROM messages
                    WHERE user_id = %s
                    ORDER BY timestamp DESC LIMIT %s
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT content, is_user, timestamp, mood, themes
                    FROM messages
                    WHERE user_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (user_id, limit))
            
            messages = [dict(row) for row in cursor.fetchall()]
            return list(reversed(messages))
            
        except Exception as e:
            print(f"DB Error in get_recent_messages: {e}")
            return []
        finally:
            conn.close()
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT DATE(timestamp)) as days_active
                    FROM messages
                    WHERE user_id = %s AND is_user = TRUE
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT DATE(timestamp)) as days_active
                    FROM messages
                    WHERE user_id = ? AND is_user = 1
                ''', (user_id,))
            
            stats = dict(cursor.fetchone())
            return stats
            
        except Exception as e:
            print(f"DB Error in get_user_stats: {e}")
            return {"total_messages": 0, "days_active": 0}
        finally:
            conn.close()
