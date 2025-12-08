# crisis_detector.py
# Crisis Detection & Mental Health Resources
# Ethical safety system for Khayal

from typing import Dict, List, Optional
from groq import Groq
import json

class CrisisDetector:
    """Detect mental health crises and provide appropriate resources"""
    
    def __init__(self, groq_client: Groq):
        self.client = groq_client
        self.model = "llama-3.3-70b-versatile"
        
        # Crisis keywords (backup if LLM fails)
        self.crisis_keywords = [
            'suicide', 'kill myself', 'end my life', 'want to die',
            'self harm', 'cut myself', 'hurt myself', 'no reason to live',
            'better off dead', 'can\'t go on', 'give up on life'
        ]
    
    def detect_crisis(self, message: str, mood_data: Dict = None) -> Dict:
        """
        Detect if message indicates mental health crisis
        
        Returns:
            {
                "is_crisis": bool,
                "severity": str,  # low/medium/high/critical
                "crisis_type": str,  # suicidal/self_harm/severe_distress/none
                "should_escalate": bool,
                "recommended_action": str
            }
        """
        
        # Quick keyword check first (fast)
        has_keywords = self._check_keywords(message)
        
        # Use LLM for deeper analysis
        llm_analysis = self._llm_detect_crisis(message, mood_data)
        
        # Combine both (keyword check + LLM)
        is_crisis = has_keywords or llm_analysis.get('is_crisis', False)
        
        if is_crisis:
            severity = llm_analysis.get('severity', 'high')
            crisis_type = llm_analysis.get('crisis_type', 'severe_distress')
        else:
            severity = 'low'
            crisis_type = 'none'
        
        # Determine if should escalate
        should_escalate = (
            severity in ['high', 'critical'] or
            crisis_type in ['suicidal', 'self_harm']
        )
        
        return {
            "is_crisis": is_crisis,
            "severity": severity,
            "crisis_type": crisis_type,
            "should_escalate": should_escalate,
            "recommended_action": self._get_recommended_action(crisis_type, severity)
        }
    
    def _check_keywords(self, message: str) -> bool:
        """Quick keyword-based check"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.crisis_keywords)
    
    def _llm_detect_crisis(self, message: str, mood_data: Dict = None) -> Dict:
        """Use LLM to detect crisis with nuance"""
        
        mood_context = ""
        if mood_data:
            mood_context = f"\nMood: {mood_data.get('mood')}, Intensity: {mood_data.get('intensity')}/10"
        
        prompt = f"""Analyze this message for mental health crisis indicators.

Message: "{message}"{mood_context}

Determine:
1. Is this a mental health crisis? (true/false)
2. Severity: low/medium/high/critical
3. Crisis type: suicidal/self_harm/severe_distress/none

Crisis indicators:
- Suicidal ideation (wanting to die, planning suicide)
- Self-harm intentions (cutting, hurting self)
- Severe distress (can't cope, giving up)
- Hopelessness with no coping ability

NOT a crisis (don't over-detect):
- General sadness or stress
- Venting frustration
- Expressing tiredness
- Normal grief/loss

Return ONLY JSON:
{{
  "is_crisis": true/false,
  "severity": "low/medium/high/critical",
  "crisis_type": "suicidal/self_harm/severe_distress/none",
  "reasoning": "brief explanation"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a mental health crisis detection expert. Be sensitive but not alarmist. Return only JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temp for consistent detection
                max_tokens=150
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text.strip())
            return result
            
        except Exception as e:
            print(f"⚠️  LLM crisis detection failed: {e}")
            # Fallback to safe default
            return {
                "is_crisis": False,
                "severity": "low",
                "crisis_type": "none",
                "reasoning": "Detection failed"
            }
    
    def _get_recommended_action(self, crisis_type: str, severity: str) -> str:
        """Get recommended action based on crisis level"""
        
        if crisis_type == "suicidal":
            return "immediate_resources"
        elif crisis_type == "self_harm":
            return "urgent_resources"
        elif severity in ["high", "critical"]:
            return "supportive_resources"
        else:
            return "gentle_support"
    
    def get_crisis_response(
        self,
        crisis_type: str,
        user_location: str = "IN"  # Default India
    ) -> Dict:
        """
        Get appropriate crisis response message and resources
        
        Args:
            crisis_type: Type of crisis detected
            user_location: Country code (IN/PK/US/UK/etc.)
        
        Returns:
            {
                "message": str,  # Message to send to user
                "resources": List[Dict],  # Helpline info
                "followup": str  # Follow-up actions
            }
        """
        
        resources = self._get_helplines(user_location)
        
        if crisis_type == "suicidal":
            message = """I'm really concerned about you right now. What you're going through sounds incredibly painful.

Please know: You don't have to face this alone.

🆘 Immediate Help Available 24/7:
{resources}

These people are trained to help and they care. Please reach out to them right now.

I'm here too, but they can provide the support you need in this moment. You matter, and there are people who want to help you through this."""

        elif crisis_type == "self_harm":
            message = """I hear how much pain you're in right now. That urge to hurt yourself must be really overwhelming.

Please pause for a moment. You deserve care and support:

🆘 Get Support Now:
{resources}

These helplines have counselors who understand what you're going through and can help you through this moment.

You're stronger than you know, but you don't have to be strong alone."""

        elif crisis_type == "severe_distress":
            message = """What you're going through sounds really difficult, and I want you to know it's okay to ask for help.

If things feel too heavy right now:

💚 Support Available:
{resources}

Talking to someone trained can really help. You don't have to carry this alone.

I'm here to listen, but please consider reaching out to them too."""

        else:
            message = """I can feel you're going through a tough time. That takes courage to share.

If you ever need more support:

💚 Resources Available:
{resources}

Sometimes talking to a professional really helps. Just know the option is there whenever you need it."""
        
        # Format resources into message
        resource_text = "\n".join([
            f"• {r['name']}: {r['number']}"
            for r in resources[:3]  # Top 3
        ])
        
        formatted_message = message.format(resources=resource_text)
        
        return {
            "message": formatted_message,
            "resources": resources,
            "followup": "check_in_24h"  # System should check in after 24 hours
        }
    
    def _get_helplines(self, country_code: str) -> List[Dict]:
        """Get mental health helplines by country"""
        
        helplines = {
            "IN": [  # India
                {
                    "name": "AASRA",
                    "number": "91-9820466726",
                    "hours": "24/7",
                    "languages": "English, Hindi"
                },
                {
                    "name": "Vandrevala Foundation",
                    "number": "1860-266-2345",
                    "hours": "24/7",
                    "languages": "English, Hindi, Multiple"
                },
                {
                    "name": "iCall",
                    "number": "91-9152987821",
                    "hours": "Mon-Sat, 8am-10pm",
                    "languages": "English, Hindi, Marathi"
                },
                {
                    "name": "Snehi",
                    "number": "91-22-27546669",
                    "hours": "24/7",
                    "languages": "Hindi"
                }
            ],
            "PK": [  # Pakistan
                {
                    "name": "Umang Helpline",
                    "number": "0317-4288665",
                    "hours": "24/7",
                    "languages": "Urdu, English"
                },
                {
                    "name": "Rozan Helpline",
                    "number": "0800-22444",
                    "hours": "Mon-Fri, 9am-6pm",
                    "languages": "Urdu"
                }
            ],
            "US": [  # United States
                {
                    "name": "988 Suicide & Crisis Lifeline",
                    "number": "988",
                    "hours": "24/7",
                    "languages": "English, Spanish"
                },
                {
                    "name": "Crisis Text Line",
                    "number": "Text HOME to 741741",
                    "hours": "24/7",
                    "languages": "English"
                }
            ],
            "UK": [  # United Kingdom
                {
                    "name": "Samaritans",
                    "number": "116-123",
                    "hours": "24/7",
                    "languages": "English"
                }
            ]
        }
        
        return helplines.get(country_code, helplines["IN"])  # Default to India


# ========================================
# TESTING
# ========================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("="*60)
    print("🚨 TESTING CRISIS DETECTION SYSTEM")
    print("="*60)
    
    # Initialize
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    detector = CrisisDetector(groq_client)
    
    # Test cases
    test_messages = [
        # Critical
        ("I want to end my life", "suicidal ideation"),
        ("I'm going to kill myself tonight", "suicidal plan"),
        
        # Self-harm
        ("I want to cut myself", "self-harm intention"),
        ("I've been hurting myself and can't stop", "ongoing self-harm"),
        
        # Severe distress (not crisis)
        ("I can't cope anymore, everything is too much", "severe distress"),
        ("I feel completely hopeless", "hopelessness"),
        
        # NOT crisis (should not trigger)
        ("I'm really stressed about work", "normal stress"),
        ("Feeling sad today", "normal sadness"),
        ("I'm so tired I could die", "figure of speech"),
    ]
    
    for message, label in test_messages:
        print(f"\n{'─'*60}")
        print(f"Test: {label}")
        print(f"{'─'*60}")
        print(f"💬 Message: \"{message}\"")
        
        result = detector.detect_crisis(message)
        
        print(f"\n📊 Detection Result:")
        print(f"  Is crisis: {'🚨 YES' if result['is_crisis'] else '✅ No'}")
        print(f"  Severity: {result['severity']}")
        print(f"  Type: {result['crisis_type']}")
        print(f"  Should escalate: {'⚠️  YES' if result['should_escalate'] else 'No'}")
        print(f"  Action: {result['recommended_action']}")
        
        if result['should_escalate']:
            response = detector.get_crisis_response(result['crisis_type'], "IN")
            print(f"\n📝 Would send this message:")
            print("─"*60)
            print(response['message'][:200] + "...")
            print("─"*60)
    
    print("\n" + "="*60)
    print("✅ Crisis detection testing complete!")
    print("="*60)