# Add these methods to your KhayalDatabase class

import datetime


def get_user_messages_today(self, user_id: int) -> list:
    """Get all messages for a user from today"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    # Get today's date
    today = datetime.now().date()
    
    cursor.execute('''
        SELECT 
            content,
            is_user,
            timestamp,
            mood
        FROM messages
        WHERE user_id = ?
        AND DATE(timestamp) = DATE(?)
        ORDER BY timestamp ASC
    ''', (user_id, today))
    
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return messages

def get_active_users_today(self) -> list:
    """Get all users who sent messages today"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    cursor.execute('''
        SELECT DISTINCT 
            u.id,
            u.phone_number
        FROM users u
        INNER JOIN messages m ON u.id = m.user_id
        WHERE DATE(m.timestamp) = DATE(?)
        AND m.is_user = 1
    ''', (today,))
    
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return users