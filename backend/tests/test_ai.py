import json

import pytest

from app.core.errors import AIUnavailableError
from app.dependencies import get_llm_provider
from app.main import app
from app.services.ai.classifier import redact

TEXT = {"subject": "Fuga", "description": "Desde hace tres semanas existe una fuga de agua frente a mi vivienda."}


class FakeProvider:
    model_name = "fake-model"

    def __init__(self, answer=None, error=None):
        self.answer, self.error, self.last_prompt = answer, error, None

    def generate_json(self, system_prompt, user_prompt, schema):
        self.last_prompt = user_prompt
        if self.error:
            raise self.error
        return self.answer


@pytest.fixture()
def use_provider():
    def _use(provider):
        app.dependency_overrides[get_llm_provider] = lambda: provider
        return provider
    yield _use
    app.dependency_overrides.pop(get_llm_provider, None)


def test_valid_suggestion(client, citizen, use_provider):
    use_provider(FakeProvider(json.dumps(
        {"category": "reclamo", "priority": "alta", "summary": "El ciudadano reporta una fuga de agua."})))
    r = client.post("/api/ai/classify", headers=citizen, json=TEXT)
    assert r.status_code == 200
    assert r.json() == {"category": "reclamo", "priority": "alta", "model": "fake-model",
                        "summary": "El ciudadano reporta una fuga de agua."}


@pytest.mark.parametrize("answer", [
    "esto no es json",
    json.dumps({"category": "inventada", "priority": "alta", "summary": "Resumen suficiente."}),
    json.dumps({"category": "reclamo", "priority": "urgentísima", "summary": "Resumen suficiente."}),
    json.dumps({"category": "reclamo", "priority": "alta", "summary": ""}),
    json.dumps(["reclamo"]),
])
def test_invalid_model_output_is_rejected(client, citizen, use_provider, answer):
    use_provider(FakeProvider(answer))
    r = client.post("/api/ai/classify", headers=citizen, json=TEXT)
    assert r.status_code == 503 and r.json()["code"] == "ai_unavailable"


def test_provider_failure_returns_503(client, citizen, use_provider):
    use_provider(FakeProvider(error=AIUnavailableError("caído")))
    assert client.post("/api/ai/classify", headers=citizen, json=TEXT).status_code == 503


def test_without_api_key_ai_is_disabled_but_requests_still_work(client, citizen):
    assert client.post("/api/ai/classify", headers=citizen, json=TEXT).status_code == 503
    r = client.post("/api/requests", headers=citizen, json={**TEXT, "subject": "Fuga de agua", "category": "reclamo"})
    assert r.status_code == 201


def test_personal_data_is_not_sent_to_the_model(client, citizen, use_provider):
    provider = use_provider(FakeProvider(json.dumps(
        {"category": "reclamo", "priority": "alta", "summary": "El ciudadano reporta una fuga."})))
    text = {"subject": "Fuga", "description": "Soy Ana, cédula 1.144.555.666, escríbanme a ana@mail.com o al 3151234567."}
    client.post("/api/ai/classify", headers=citizen, json=text)
    assert "1.144.555.666" not in provider.last_prompt
    assert "ana@mail.com" not in provider.last_prompt
    assert "3151234567" not in provider.last_prompt


def test_redact():
    assert redact("CC 1144555666 y correo a@b.co") == "CC [número] y correo [correo]"


def test_status_never_exposes_the_key(client, citizen):
    body = client.get("/api/ai/status", headers=citizen).json()
    assert body["enabled"] is False and "key" not in str(body).lower()


class _Resp:
    def __init__(self, status, payload=None):
        self.status_code, self._payload = status, payload or {}

    def json(self):
        return self._payload


def _ok(text):
    return _Resp(200, {"candidates": [{"content": {"parts": [{"text": text}]}}]})


def test_gemini_falls_back_to_next_model_when_busy(monkeypatch):
    from app.services.ai import gemini_provider
    calls = []

    def fake_post(url, **_):
        calls.append(url)
        return _Resp(503) if "modelo-a" in url else _ok('{"x": 1}')

    monkeypatch.setattr(gemini_provider.httpx, "post", fake_post)
    provider = gemini_provider.GeminiProvider("k", "modelo-a, modelo-b", 5)
    assert provider.generate_json("s", "u", {}) == '{"x": 1}'
    assert provider.model_name == "modelo-b" and len(calls) == 2


def test_gemini_all_models_busy_raises_unavailable(monkeypatch):
    from app.services.ai import gemini_provider
    monkeypatch.setattr(gemini_provider.httpx, "post", lambda url, **_: _Resp(503))
    provider = gemini_provider.GeminiProvider("k", "modelo-a,modelo-b", 5)
    with pytest.raises(AIUnavailableError, match="saturado"):
        provider.generate_json("s", "u", {})


def test_gemini_rejected_key_does_not_retry(monkeypatch):
    from app.services.ai import gemini_provider
    calls = []
    monkeypatch.setattr(gemini_provider.httpx, "post", lambda url, **_: calls.append(url) or _Resp(401))
    with pytest.raises(AIUnavailableError, match="rechazó"):
        gemini_provider.GeminiProvider("k", "modelo-a,modelo-b", 5).generate_json("s", "u", {})
    assert len(calls) == 1
