# summary_generator.py
# Daily Summary Generator for Khayal - Phase 5
# Creates warm, reflective summaries of the user's day

import json
from typing import Dict, List
from datetime import datetime, date
from groq import Groq

class DailySummaryGenerator:
    """Generate daily summaries of emotional journey"""
    
    def __init__(self, database, groq_client: Groq):
        """
        Initialize summary generator
        
        Args:
            database: KhayalDatabase instance
            groq_client: Groq client for summary generation
        """
        self.db = database
        self.client = groq_client
        self.model = "llama-3.3-70b-versatile"
    
    def generate_daily_summary(
        self,
        user_id: int,
        summary_date: date = None
    ) -> Dict:
        """
        Generate daily summary for a user
        
        Args:
            user_id: User ID
            summary_date: Date to summarize (default: today)
        
        Returns:
            {
                "summary": str,  # The summary text
                "emotional_arc": dict,  # Morning → Evening progression
                "message_count": int,
                "should_send": bool  # Whether there's enough data to send
            }
        """
        
        if summary_date is None:
            summary_date = date.today()
        
        # Get all messages from the day
        messages = self.db.get_messages_for_date(user_id, summary_date)
        
        # Filter only user messages
        user_messages = [msg for msg in messages if msg['message_type'] == 'user']
        
        # Need at least 2 messages to create meaningful summary
        if len(user_messages) < 2:
            return {
                "summary": None,
                "emotional_arc": {},
                "message_count": len(user_messages),
                "should_send": False
            }
        
        # Analyze emotional arc
        emotional_arc = self._analyze_emotional_arc(user_messages)
        
        # Generate summary
        summary_text = self._generate_summary_text(user_messages, emotional_arc)
        
        return {
            "summary": summary_text,
            "emotional_arc": emotional_arc,
            "message_count": len(user_messages),
            "should_send": True
        }
    
    def _analyze_emotional_arc(self, messages: List[Dict]) -> Dict:
        """
        Analyze how emotions progressed through the day
        
        Returns:
            {
                "morning": {"mood": str, "intensity": int},
                "afternoon": {"mood": str, "intensity": int},
                "evening": {"mood": str, "intensity": int},
                "trend": str,  # improving/stable/declining
                "key_moments": List[str]
            }
        """
        
        # Divide day into periods
        morning_msgs = []  # 5 AM - 12 PM
        afternoon_msgs = []  # 12 PM - 5 PM
        evening_msgs = []  # 5 PM - 10 PM
        
        for msg in messages:
            timestamp = datetime.fromisoformat(msg['timestamp'])
            hour = timestamp.hour
            
            if 5 <= hour < 12:
                morning_msgs.append(msg)
            elif 12 <= hour < 17:
                afternoon_msgs.append(msg)
            elif 17 <= hour < 22:
                evening_msgs.append(msg)
        
        # Get dominant mood for each period
        morning_mood = self._get_period_mood(morning_msgs)
        afternoon_mood = self._get_period_mood(afternoon_msgs)
        evening_mood = self._get_period_mood(evening_msgs)
        
        # Determine trend
        moods_present = [m for m in [morning_mood, afternoon_mood, evening_mood] if m]
        
        if len(moods_present) >= 2:
            first_intensity = moods_present[0].get('intensity', 5)
            last_intensity = moods_present[-1].get('intensity', 5)
            
            if last_intensity > first_intensity + 1:
                trend = "improving"
            elif last_intensity < first_intensity - 1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Identify key moments (high intensity messages)
        key_moments = []
        for msg in messages:
            if msg.get('intensity', 0) >= 7:
                key_moments.append({
                    "content": msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content'],
                    "mood": msg.get('mood'),
                    "intensity": msg.get('intensity')
                })
        
        return {
            "morning": morning_mood,
            "afternoon": afternoon_mood,
            "evening": evening_mood,
            "trend": trend,
            "key_moments": key_moments[:3]  # Top 3 key moments
        }
    
    def _get_period_mood(self, messages: List[Dict]) -> Dict:
        """Get dominant mood for a time period"""
        
        if not messages:
            return None
        
        # Get messages with mood data
        mood_messages = [msg for msg in messages if msg.get('mood')]
        
        if not mood_messages:
            return None
        
        # Get most common mood
        moods = [msg['mood'] for msg in mood_messages]
        intensities = [msg.get('intensity', 5) for msg in mood_messages]
        
        dominant_mood = max(set(moods), key=moods.count)
        avg_intensity = sum(intensities) / len(intensities)
        
        return {
            "mood": dominant_mood,
            "intensity": round(avg_intensity, 1)
        }
    
    def _generate_summary_text(
        self,
        messages: List[Dict],
        emotional_arc: Dict
    ) -> str:
        """
        Generate the actual summary text using LLM
        """
        
        # Prepare messages for context
        messages_text = []
        for msg in messages:
            mood_info = f" [{msg.get('mood')}]" if msg.get('mood') else ""
            messages_text.append(f"- {msg['content']}{mood_info}")
        
        messages_context = "\n".join(messages_text[:10])  # Limit to 10 for token efficiency
        
        # Prepare emotional arc context
        arc_parts = []
        if emotional_arc.get('morning'):
            arc_parts.append(f"Morning: {emotional_arc['morning']['mood']}")
        if emotional_arc.get('afternoon'):
            arc_parts.append(f"Afternoon: {emotional_arc['afternoon']['mood']}")
        if emotional_arc.get('evening'):
            arc_parts.append(f"Evening: {emotional_arc['evening']['mood']}")
        
        arc_summary = " → ".join(arc_parts) if arc_parts else "Throughout the day"
        
        # Generate summary
        prompt = f"""You are Khayal, a warm desi journaling companion. Create a 10 PM daily summary.

Today's messages:
{messages_context}

Emotional arc: {arc_summary}
Trend: {emotional_arc.get('trend', 'stable')}

Create a warm, reflective summary (4-6 sentences) that:
1. Starts with a warm greeting: "Aaj ka din kaisa raha?" or similar
2. Acknowledges the emotional journey (morning → evening if applicable)
3. Validates their experience
4. Ends with encouragement for tomorrow and "Good night" or sleep well

Style:
- Warm and caring, like a close friend
- Use light Urdu/Hindi naturally (1-2 words: yaar, subah, shaam)
- Be concise but meaningful
- Poetic but not cheesy
- Don't be preachy

Example tone:
"Aaj ka din kaisa tha, yaar?

Subah you started with some stress about work,
but by shaam you were feeling a bit lighter.
That's growth right there ✨

Kal is a fresh start.
Sleep well 💜"

Now create the summary:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are Khayal, a warm and poetic desi journaling companion."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,  # Creative but not too random
                max_tokens=250
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            # Fallback summary
            return self._generate_fallback_summary(emotional_arc)
    
    def _generate_fallback_summary(self, emotional_arc: Dict) -> str:
        """Generate a simple fallback summary if LLM fails"""
        
        summary_parts = ["Aaj ka din kaisa tha?"]
        
        if emotional_arc.get('trend') == 'improving':
            summary_parts.append("Things seemed to get better as the day went on ✨")
        elif emotional_arc.get('trend') == 'declining':
            summary_parts.append("The day had its challenges.")
        else:
            summary_parts.append("You made it through the day.")
        
        summary_parts.append("Kal is a new day. Sleep well 💜")
        
        return "\n\n".join(summary_parts)
    
    def save_summary(
        self,
        user_id: int,
        summary_date: date,
        summary_text: str,
        emotional_arc: Dict
    ):
        """Save summary to database"""
        
        self.db.store_daily_summary(
            user_id=393455031774,
            date=str(summary_date),
            summary=summary_text,
            emotional_arc=emotional_arc
        )


# ========================================
# TESTING & DEMO
# ========================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from database import KhayalDatabase
    
    load_dotenv()
    
    print("="*60)
    print("🌙 TESTING DAILY SUMMARY GENERATOR")
    print("="*60)
    
    # Initialize
    db = KhayalDatabase("khayal.db")
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    generator = DailySummaryGenerator(db, groq_client)
    
    # Test with your user
    test_phone = "919876543210"  # Replace with your number
    user_id = db.get_or_create_user(test_phone)
    
    print(f"\n📊 Generating summary for user {user_id}...")
    print(f"Date: {date.today()}")
    
    # Generate summary
    result = generator.generate_daily_summary(user_id)
    
    print(f"\n{'─'*60}")
    print("SUMMARY RESULT")
    print(f"{'─'*60}")
    print(f"Message count: {result['message_count']}")
    print(f"Should send: {'✅ YES' if result['should_send'] else '❌ NO'}")
    
    if result['should_send']:
        print(f"\n📝 SUMMARY:")
        print("─"*60)
        print(result['summary'])
        print("─"*60)
        
        print(f"\n📊 EMOTIONAL ARC:")
        arc = result['emotional_arc']
        if arc.get('morning'):
            print(f"  Morning: {arc['morning']['mood']} ({arc['morning']['intensity']}/10)")
        if arc.get('afternoon'):
            print(f"  Afternoon: {arc['afternoon']['mood']} ({arc['afternoon']['intensity']}/10)")
        if arc.get('evening'):
            print(f"  Evening: {arc['evening']['mood']} ({arc['evening']['intensity']}/10)")
        print(f"  Trend: {arc.get('trend', 'stable')}")
        
        if arc.get('key_moments'):
            print(f"\n💫 KEY MOMENTS:")
            for i, moment in enumerate(arc['key_moments'], 1):
                print(f"  {i}. {moment['content']} ({moment['mood']})")
        
        # Ask if should save
        print(f"\n💾 Save this summary to database? (y/n)")
        save = input().strip().lower()
        if save == 'y':
            generator.save_summary(
                user_id=user_id,
                summary_date=date.today(),
                summary_text=result['summary'],
                emotional_arc=result['emotional_arc']
            )
            print("✅ Summary saved!")
    else:
        print("\n⚠️  Not enough data to generate meaningful summary")
        print("   Need at least 2 messages from today")
    
    print("\n" + "="*60)
    print("✅ Summary generator testing complete!")
    print("="*60)
    
    db.close()