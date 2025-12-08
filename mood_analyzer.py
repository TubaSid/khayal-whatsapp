# mood_analyzer.py
# Khayal Mood Analyzer - Phase 2
# Detects emotions, intensity, and themes from user messages

import json
from typing import Dict, List
from groq import Groq

class MoodAnalyzer:
    """Analyze mood and emotional content of messages"""
    
    def __init__(self, groq_client: Groq):
        """Initialize with Groq client"""
        self.client = groq_client
        self.model = "llama-3.3-70b-versatile"
    
    def analyze(self, message: str) -> Dict:
        """
        Analyze a message and return mood data
        
        Args:
            message: User's message text
        
        Returns:
            {
                "mood": str,  # primary emotion
                "intensity": int,  # 1-10 scale
                "themes": List[str],  # topics/themes
                "needs_support": bool,  # urgent support needed?
                "secondary_moods": List[str]  # other emotions present
            }
        """
        
        analysis_prompt = f"""Analyze this message for emotional content.

Message: "{message}"

Return ONLY a JSON object (no markdown, no explanation) with:
{{
  "mood": "primary emotion (happy/sad/anxious/stressed/excited/frustrated/overwhelmed/grateful/lonely/neutral)",
  "intensity": 1-10 (1=mild, 10=extreme),
  "themes": ["topic1", "topic2"],
  "needs_support": true/false (urgent emotional support needed?),
  "secondary_moods": ["emotion2", "emotion3"]
}}

Guidelines:
- mood: Choose the DOMINANT emotion
- intensity: How strong is the emotion?
  - 1-3: Mild (mentioning casually)
  - 4-6: Moderate (clearly present)
  - 7-8: Strong (very emotional)
  - 9-10: Extreme (crisis/celebration)
- themes: What topics are mentioned? (work, family, relationships, health, etc.)
- needs_support: true if expressing distress, crisis, or needs immediate validation
- secondary_moods: Other emotions present (max 2)

Examples:
"Yaar, aaj bahut stressed hoon work se" → {{"mood": "stressed", "intensity": 7, "themes": ["work"], "needs_support": true, "secondary_moods": ["anxious"]}}
"I got promoted!!" → {{"mood": "excited", "intensity": 9, "themes": ["work", "achievement"], "needs_support": false, "secondary_moods": ["happy"]}}
"Feeling kinda meh today" → {{"mood": "neutral", "intensity": 3, "themes": [], "needs_support": false, "secondary_moods": []}}

Respond with ONLY the JSON object."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an emotion analysis expert. Respond ONLY with valid JSON, no markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            # Parse JSON
            mood_data = json.loads(result_text.strip())
            
            # Validate and set defaults
            mood_data.setdefault("mood", "neutral")
            mood_data.setdefault("intensity", 5)
            mood_data.setdefault("themes", [])
            mood_data.setdefault("needs_support", False)
            mood_data.setdefault("secondary_moods", [])
            
            return mood_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response was: {result_text}")
            # Return default mood data
            return self._get_default_mood()
            
        except Exception as e:
            print(f"❌ Mood analysis error: {e}")
            return self._get_default_mood()
    
    def _get_default_mood(self) -> Dict:
        """Return default mood data when analysis fails"""
        return {
            "mood": "neutral",
            "intensity": 5,
            "themes": [],
            "needs_support": False,
            "secondary_moods": []
        }
    
    def get_mood_summary(self, mood_data: Dict) -> str:
        """Get human-readable mood summary"""
        
        mood = mood_data.get("mood", "neutral")
        intensity = mood_data.get("intensity", 5)
        
        intensity_labels = {
            range(1, 4): "mildly",
            range(4, 7): "moderately",
            range(7, 9): "very",
            range(9, 11): "extremely"
        }
        
        intensity_label = next(
            (label for r, label in intensity_labels.items() if intensity in r),
            "moderately"
        )
        
        return f"{intensity_label} {mood}"
    
    def should_respond_immediately(self, mood_data: Dict) -> bool:
        """
        Decide if this message needs immediate response
        
        Criteria for immediate response:
        - needs_support is true
        - intensity >= 7
        - mood is anxious, stressed, sad, lonely, overwhelmed
        """
        
        urgent_moods = ["anxious", "stressed", "sad", "lonely", "overwhelmed", "frustrated"]
        
        if mood_data.get("needs_support"):
            return True
        
        if mood_data.get("intensity", 0) >= 7:
            return True
        
        if mood_data.get("mood") in urgent_moods:
            return True
        
        # Celebrations also get immediate response
        if mood_data.get("mood") in ["excited", "happy"] and mood_data.get("intensity", 0) >= 7:
            return True
        
        return False


# ========================================
# TESTING & DEMO
# ========================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("="*60)
    print("🧠 TESTING MOOD ANALYZER")
    print("="*60)
    
    # Initialize
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    analyzer = MoodAnalyzer(groq_client)
    
    # Test messages
    test_messages = [
        "Yaar, aaj bahut stressed hoon work se",
        "I got the promotion!!!",
        "Feeling overwhelmed with everything",
        "Kya haal hai?",
        "Bahut akela feel ho raha hai",
        "Work went great but I'm exhausted",
        "Just had chai, feeling peaceful",
        "Can't sleep, too many thoughts",
    ]
    
    print("\n📊 Analyzing test messages:\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"{'─'*60}")
        print(f"Test {i}/{len(test_messages)}")
        print(f"{'─'*60}")
        print(f"💬 Message: {message}")
        
        mood_data = analyzer.analyze(message)
        
        print(f"\n📋 Analysis:")
        print(f"  Mood: {mood_data['mood']}")
        print(f"  Intensity: {mood_data['intensity']}/10")
        print(f"  Themes: {', '.join(mood_data['themes']) if mood_data['themes'] else 'None'}")
        print(f"  Needs support: {'Yes' if mood_data['needs_support'] else 'No'}")
        print(f"  Secondary moods: {', '.join(mood_data['secondary_moods']) if mood_data['secondary_moods'] else 'None'}")
        
        print(f"\n💡 Summary: {analyzer.get_mood_summary(mood_data)}")
        
        immediate = analyzer.should_respond_immediately(mood_data)
        print(f"⚡ Immediate response: {'YES - respond now' if immediate else 'NO - can save for summary'}")
        
        print()
    
    print("="*60)
    print("✅ Mood analyzer testing complete!")
    print("="*60)