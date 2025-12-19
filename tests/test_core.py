import sys
import types
import pytest

# Lightweight stub for groq so tests don't depend on external API
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


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_endpoint(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data


def test_webhook_verify_success(client):
    # set the token on the already-imported module to avoid reloads
    webhook_module.config.WEBHOOK_VERIFY_TOKEN = 'test-token'

    resp = client.get('/webhook?hub.mode=subscribe&hub.verify_token=test-token&hub.challenge=CHALLENGE')
    assert resp.status_code == 200
    assert resp.data.decode() == 'CHALLENGE'


def test_webhook_post_no_entry(client):
    resp = client.post('/webhook', json={})
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == 'No entry'
