import sys
import types
import pytest

# Ensure groq stub exists for deterministic responses
_groq_stub = types.SimpleNamespace(
    Groq=lambda api_key=None: types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=lambda **kw: types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="ok"))])
            )
        )
    )
)
sys.modules.setdefault('groq', _groq_stub)

from khayal.app import create_app
from khayal.config import TestingConfig
import khayal.routes.webhook as webhook_module


class DummyDB:
    def __init__(self):
        self.stored_messages = []
        self.stored_khayal = []

    def get_or_create_user(self, phone):
        return 1

    def store_user_message(self, **kwargs):
        self.stored_messages.append(kwargs)

    def store_khayal_message(self, user_id, message):
        self.stored_khayal.append((user_id, message))


class DummyWhatsApp:
    def __init__(self):
        self.sent = []
        self.read = []

    def send_message(self, to_number, message_text):
        self.sent.append((to_number, message_text))
        return {"id": "msgid"}

    def mark_as_read(self, message_id):
        self.read.append(message_id)
        return True


class DummyOnboarding:
    def is_onboarding_complete(self, user_id):
        return True

    def get_onboarding_step(self, user_id):
        return 0


class DummyCrisis:
    def detect_crisis(self, text):
        return {"should_escalate": False, "is_crisis": False}


class DummyMood:
    def analyze(self, text):
        return {"mood": "anxious", "intensity": 6, "themes": ["work"], "needs_support": False}


class DummyMemory:
    def detect_patterns(self, user_id, days=7):
        return {"needs_attention": False}

    def get_enriched_context(self, user_id, message):
        return "context"


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    return app.test_client()


def test_normal_webhook_flow(client):
    # Monkeypatch module-level components
    webhook_module.db = DummyDB()
    wa = DummyWhatsApp()
    webhook_module.whatsapp_client = wa
    webhook_module.onboarding_manager = DummyOnboarding()
    webhook_module.crisis_detector = DummyCrisis()
    webhook_module.mood_analyzer = DummyMood()
    webhook_module.semantic_memory = DummyMemory()

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "m1",
                                    "from": "+911234567890",
                                    "type": "text",
                                    "text": {"body": "I'm feeling anxious today"}
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    resp = client.post('/webhook', json=payload)
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == 'EVENT_RECEIVED'

    # WhatsApp client should have marked message as read and sent a reply
    assert 'm1' in wa.read
    assert len(wa.sent) == 1

    # DB should have stored the user message and Khayal response
    assert len(webhook_module.db.stored_messages) == 1
    assert len(webhook_module.db.stored_khayal) == 1
