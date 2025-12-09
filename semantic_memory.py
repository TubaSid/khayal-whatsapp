# semantic_memory.py
# Advanced Memory System for Khayal - Phase 3
# Pattern detection, trend analysis, and semantic search

import json
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from groq import Groq

class SemanticMemory:
    """Advanced memory system with pattern detection"""
    
    def __init__(self, database, groq_client: Groq):
        """
        Initialize semantic memory
        
        Args:
            database: KhayalDatabase instance
            groq_client: Groq client for embeddings/analysis
        """
        self.db = database
        self.client = groq_client
        self.model = "llama-3.3-70b-versatile"
    
    # ========================================
    # PATTERN DETECTION
    # ========================================
    
    def detect_patterns(self, user_id: int, days: int = 7) -> Dict:
        """
        Detect emotional and thematic patterns
        """
        
        # Get recent messages
        # 🚨 FIX 1: Use the public getter method
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        since_date_date = (datetime.now() - timedelta(days=days)).date()
        since_date_dt = datetime.now() - timedelta(days=days) # For PostgreSQL comparison
        
        try:
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT mood, intensity, themes, timestamp
                    FROM messages
                    WHERE user_id = %s
                    AND is_user = TRUE -- Corrected from message_type
                    AND timestamp >= %s -- Corrected date function for PG
                    AND mood IS NOT NULL
                    ORDER BY timestamp ASC
                """, (user_id, since_date_dt))
            else:
                cursor.execute("""
                    SELECT mood, intensity, themes, timestamp
                    FROM messages
                    WHERE user_id = ?
                    AND is_user = 1 -- Corrected from message_type
                    AND date(timestamp) >= ?
                    AND mood IS NOT NULL
                    ORDER BY timestamp ASC
                """, (user_id, since_date_date))
        
            messages = cursor.fetchall()
            
        except Exception as e:
            conn.rollback()
            print(f"DB Error in detect_patterns: {e}", file=sys.stderr)
            raise
        
        if not messages:
            return self._get_empty_pattern()
        
        # Analyze patterns
        moods = [msg['mood'] for msg in messages]
        intensities = [msg['intensity'] for msg in messages]
        all_themes = []
        
        for msg in messages:
            if msg['themes']:
                # Ensure the theme data is valid JSON before loading
                try:
                    themes = json.loads(msg['themes'])
                    all_themes.extend(themes)
                except (json.JSONDecodeError, TypeError):
                    print(f"Warning: Failed to decode themes for message: {msg['themes']}")
        
        # Dominant mood
        mood_counts = Counter(moods)
        dominant_mood = mood_counts.most_common(1)[0][0] if mood_counts else "neutral"
        
        # Recurring themes
        theme_counts = Counter(all_themes)
        recurring_themes = [theme for theme, count in theme_counts.most_common(3)]
        
        # Mood trend analysis
        mood_trend = self._analyze_trend(intensities)
        
        # Stress triggers (themes that appear with high-intensity negative moods)
        stress_triggers = self._find_stress_triggers(messages)
        
        # Needs attention?
        needs_attention = self._needs_attention(messages, intensities)
        
        # Generate pattern summary
        pattern_summary = self._generate_pattern_summary(
            dominant_mood,
            recurring_themes,
            mood_trend,
            stress_triggers,
            days
        )
        
        return {
            "recurring_themes": recurring_themes,
            "dominant_mood": dominant_mood,
            "mood_trend": mood_trend,
            "stress_triggers": stress_triggers,
            "needs_attention": needs_attention,
            "pattern_summary": pattern_summary,
            "total_messages": len(messages),
            "days_analyzed": days
        }
    
    def _analyze_trend(self, intensities: List[int]) -> str:
        """Analyze if mood intensity is improving, stable, or declining"""
        
        if len(intensities) < 3:
            return "stable"
        
        # Compare first half vs second half
        mid = len(intensities) // 2
        first_half = sum(intensities[:mid]) / mid
        second_half = sum(intensities[mid:]) / (len(intensities) - mid)
        
        diff = second_half - first_half
        
        if diff > 1.5:
            return "intensifying"  # Getting more intense
        elif diff < -1.5:
            return "improving"  # Getting better
        else:
            return "stable"
    
    def _find_stress_triggers(self, messages: List) -> List[str]:
        """Find themes that appear with high-intensity negative moods"""
        
        negative_moods = ["stressed", "anxious", "overwhelmed", "frustrated", "sad"]
        triggers = []
        
        for msg in messages:
            if msg['mood'] in negative_moods and msg['intensity'] >= 7:
                if msg['themes']:
                    try:
                        themes = json.loads(msg['themes'])
                        triggers.extend(themes)
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        # Return top 3 most common triggers
        trigger_counts = Counter(triggers)
        return [trigger for trigger, _ in trigger_counts.most_common(3)]
    
    def _needs_attention(self, messages: List, intensities: List[int]) -> bool:
        """Determine if user needs special attention"""
        
        # Check for:
        # 1. Multiple high-intensity negative messages
        # 2. Sustained negative mood
        # 3. Escalating pattern
        
        recent_messages = messages[-5:]  # Last 5 messages
        negative_moods = ["stressed", "anxious", "overwhelmed", "frustrated", "sad", "lonely"]
        
        # Count recent negative high-intensity messages
        high_negative_count = sum(
            1 for msg in recent_messages
            if msg['mood'] in negative_moods and msg['intensity'] is not None and msg['intensity'] >= 7
        )
        
        # Check if last 3+ messages are negative
        if len(recent_messages) >= 3:
            last_three_negative = sum(
                1 for msg in recent_messages[-3:]
                if msg['mood'] in negative_moods
            )
            if last_three_negative >= 2:
                return True
        
        # Check for high-intensity negative messages
        if high_negative_count >= 2:
            return True
        
        # Check average intensity of last 5
        if len(intensities) >= 5:
            recent_intensities = [i for i in intensities[-5:] if i is not None]
            if recent_intensities:
                recent_avg = sum(recent_intensities) / len(recent_intensities)
                if recent_avg >= 7:
                    return True
        
        return False
    
    def _generate_pattern_summary(
        self,
        dominant_mood: str,
        themes: List[str],
        trend: str,
        triggers: List[str],
        days: int
    ) -> str:
        """Generate human-readable pattern summary"""
        
        parts = []
        
        # Dominant mood
        parts.append(f"Over the last {days} days, you've mostly been feeling {dominant_mood}")
        
        # Themes
        if themes:
            themes_str = ", ".join(themes[:2])
            parts.append(f"with {themes_str} being on your mind")
        
        # Trend
        if trend == "improving":
            parts.append("Things seem to be getting better")
        elif trend == "intensifying":
            parts.append("and emotions have been intensifying")
        
        # Triggers
        if triggers:
            triggers_str = ", ".join(triggers[:2])
            parts.append(f"Stress often comes up around {triggers_str}")
        
        return ". ".join(parts) + "."
    
    def _get_empty_pattern(self) -> Dict:
        """Return empty pattern when no data"""
        return {
            "recurring_themes": [],
            "dominant_mood": "neutral",
            "mood_trend": "stable",
            "stress_triggers": [],
            "needs_attention": False,
            "pattern_summary": "Not enough data to detect patterns yet.",
            "total_messages": 0,
            "days_analyzed": 0
        }
    
    # ========================================
    # SEMANTIC SEARCH
    # ========================================
    
    def find_similar_conversations(
        self,
        query: str,
        user_id: int,
        limit: int = 3
    ) -> List[Dict]:
        """
        Find past conversations similar to current query
        """
        
        # Get all past user messages
        # 🚨 FIX 1: Use the public getter method
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT content, mood, intensity, themes, timestamp
                    FROM messages
                    WHERE user_id = %s
                    AND is_user = TRUE -- Corrected from message_type
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (user_id, limit * 10)) # Increased limit to 50
            else:
                cursor.execute("""
                    SELECT content, mood, intensity, themes, timestamp
                    FROM messages
                    WHERE user_id = ?
                    AND is_user = 1 -- Corrected from message_type
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit * 10))
        
            past_messages = [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            conn.rollback()
            print(f"DB Error in find_similar_conversations: {e}", file=sys.stderr)
            raise

        if not past_messages:
            return []
        
        # Use LLM to find semantic similarity
        similar = self._find_semantic_matches(query, past_messages, limit)
        
        return similar
    
    def _find_semantic_matches(
        self,
        query: str,
        messages: List[Dict],
        limit: int
    ) -> List[Dict]:
        """Use LLM to find semantically similar messages"""
        
        # Create a prompt for the LLM to identify similar messages
        messages_text = "\n".join([
            f"{i}. {msg['content']} (mood: {msg['mood']}, themes: {msg['themes']})"
            for i, msg in enumerate(messages[:20])  # Limit to 20 for token efficiency
        ])
        
        prompt = f"""Given this current message: "{query}"

Find the {limit} most semantically similar past messages from this list:

{messages_text}

Return ONLY a JSON array of message indices (0-based), ordered by similarity.
Example: [3, 7, 12]

Consider:
- Similar topics/themes
- Similar emotional content
- Related situations

Return ONLY the JSON array, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a semantic similarity expert. Return only JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            indices = json.loads(result_text.strip())
            
            # Return the actual messages
            similar_messages = []
            for idx in indices[:limit]:
                if 0 <= idx < len(messages):
                    similar_messages.append(messages[idx])
            
            return similar_messages
            
        except Exception as e:
            print(f"❌ Semantic search error: {e}")
            return []
    
    # ========================================
    # CONTEXT ENRICHMENT
    # ========================================
    
    def get_enriched_context(
        self,
        user_id: int,
        current_message: str
    ) -> str:
        """
        Get enriched context including patterns and similar conversations
        
        Returns:
            Formatted context string for LLM
        """
        
        context_parts = []
        
        # Recent conversation (self.db.get_recent_messages already handles connection)
        recent = self.db.get_recent_messages(user_id, limit=3)
        if recent:
            context_parts.append("Recent conversation:")
            for msg in recent:
                # 🚨 FIX 4: Corrected role assignment from message_type to is_user
                role = "User" if (self.db.use_postgres and msg.get('is_user', True) is True) or (not self.db.use_postgres and msg.get('is_user', 1) == 1) else "Khayal"
                content = msg.get('content', '...')
                context_parts.append(f"  {role}: {content}")
        
        # Patterns
        patterns = self.detect_patterns(user_id, days=7)
        if patterns['total_messages'] > 0:
            context_parts.append(f"\nPatterns (last 7 days):")
            context_parts.append(f"  {patterns['pattern_summary']}")
            
            if patterns['needs_attention']:
                context_parts.append("  ⚠️  User may need extra support")
        
        # Similar past conversations
        similar = self.find_similar_conversations(current_message, user_id, limit=2)
        if similar:
            context_parts.append("\nRelated past conversations:")
            for msg in similar:
                # timestamp is available but commented out for brevity
                content = msg.get('content', '...')
                mood = msg.get('mood', 'unknown')
                context_parts.append(f"  - \"{content}\" ({mood})")
        
        return "\n".join(context_parts)
    
    # ========================================
    # MOOD TREND ANALYSIS
    # ========================================
    
    def get_mood_trend_chart(self, user_id: int, days: int = 7) -> Dict:
        """Get mood trend data for visualization"""
        
        # 🚨 FIX 1: Use the public getter method
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        since_date_date = (datetime.now() - timedelta(days=days)).date()
        since_date_dt = datetime.now() - timedelta(days=days) # For PostgreSQL comparison
        
        try:
            if self.db.use_postgres:
                cursor.execute("""
                    SELECT DATE(timestamp) as date, AVG(intensity) as avg_intensity, mood
                    FROM messages
                    WHERE user_id = %s
                    AND is_user = TRUE -- Corrected from message_type
                    AND timestamp >= %s -- Corrected date function for PG
                    AND mood IS NOT NULL
                    GROUP BY DATE(timestamp)
                    ORDER BY DATE(timestamp) ASC
                """, (user_id, since_date_dt))
            else:
                cursor.execute("""
                    SELECT date(timestamp) as date, AVG(intensity) as avg_intensity, mood
                    FROM messages
                    WHERE user_id = ?
                    AND is_user = 1 -- Corrected from message_type
                    AND date(timestamp) >= ?
                    AND mood IS NOT NULL
                    GROUP BY date(timestamp)
                    ORDER BY date(timestamp) ASC
                """, (user_id, since_date_date))
        
            trend_data = [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            conn.rollback()
            print(f"DB Error in get_mood_trend_chart: {e}", file=sys.stderr)
            raise
        
        return {
            "trend_data": trend_data,
            "days": days,
            "data_points": len(trend_data)
        }


# ========================================
# TESTING & DEMO
# ========================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from database import KhayalDatabase
    
    load_dotenv()
    
    print("="*60)
    print("🧠 TESTING SEMANTIC MEMORY & PATTERNS")
    print("="*60)
    
    # Initialize
    db = KhayalDatabase("khayal.db")
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    memory = SemanticMemory(db, groq_client)
    
    # Get test user (use your actual phone number)
    test_phone = "919876543210"  # Replace with your WhatsApp number
    user_id = db.get_or_create_user(test_phone)
    
    print(f"\n📊 Analyzing patterns for user {user_id}...")
    
    # Detect patterns
    patterns = memory.detect_patterns(user_id, days=7)
    
    print(f"\n{'─'*60}")
    print("PATTERN ANALYSIS")
    print(f"{'─'*60}")
    print(f"Messages analyzed: {patterns['total_messages']}")
    print(f"Dominant mood: {patterns['dominant_mood']}")
    print(f"Mood trend: {patterns['mood_trend']}")
    print(f"Recurring themes: {', '.join(patterns['recurring_themes']) if patterns['recurring_themes'] else 'None'}")
    print(f"Stress triggers: {', '.join(patterns['stress_triggers']) if patterns['stress_triggers'] else 'None'}")
    print(f"Needs attention: {'⚠️  YES' if patterns['needs_attention'] else '✅ No'}")
    print(f"\n📝 Summary:\n{patterns['pattern_summary']}")
    
    # Test semantic search
    if patterns['total_messages'] > 0:
        print(f"\n{'─'*60}")
        print("SEMANTIC SEARCH TEST")
        print(f"{'─'*60}")
        
        test_query = "feeling stressed about work"
        print(f"Query: \"{test_query}\"")
        
        similar = memory.find_similar_conversations(test_query, user_id, limit=3)
        
        if similar:
            print(f"\nFound {len(similar)} similar conversations:")
            for i, msg in enumerate(similar, 1):
                print(f"\n{i}. \"{msg['content']}\"")
                print(f"   Mood: {msg['mood']}, Intensity: {msg['intensity']}")
        else:
            print("\nNo similar conversations found")
    
    # Get enriched context
    print(f"\n{'─'*60}")
    print("ENRICHED CONTEXT")
    print(f"{'─'*60}")
    
    current_msg = "I'm worried about tomorrow"
    enriched = memory.get_enriched_context(user_id, current_msg)
    print(f"\nCurrent message: \"{current_msg}\"")
    print(f"\nContext for AI:\n{enriched}")
    
    # Mood trend
    print(f"\n{'─'*60}")
    print("MOOD TREND")
    print(f"{'─'*60}")
    
    trend = memory.get_mood_trend_chart(user_id, days=7)
    print(f"\nData points: {trend['data_points']}")
    
    if trend['trend_data']:
        for point in trend['trend_data']:
            date = point['date']
            avg = point['avg_intensity']
            print(f"{date}: {avg:.1f}/10")
    
    print("\n" + "="*60)
    print("✅ Semantic memory testing complete!")
    print("="*60)
    
    # 🚨 FIX 5: db.close() does not exist, remove the call
    # db.close()
