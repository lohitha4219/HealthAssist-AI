from pathlib import Path
from typing import Dict, List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.rate_limit import auth_rate_limiter
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.services.ai_service import (
    AICompletionResult,
    AIStatus,
    AIUnavailableError,
    get_ai_service,
)
from datetime import datetime, timezone


class FakeAIService:
    def __init__(self, available: bool = True):
        self.available = available
        self.calls: List[List[Dict[str, str]]] = []

    async def get_health(self) -> AIStatus:
        if not self.available:
            return AIStatus(
                available=False,
                provider="llamacpp",
                configured_provider="auto",
                model="qwen2.5-1.5b-instruct-q4_k_m",
                base_url="http://127.0.0.1:8080",
                status="offline",
                detail="Fake AI offline for test",
                setup_hint="Start llama-server",
                checked_at=datetime.now(timezone.utc),
            )
        return AIStatus(
            available=True,
            provider="llamacpp",
            configured_provider="auto",
            model="qwen2.5-1.5b-instruct-q4_k_m",
            base_url="http://127.0.0.1:8080",
            status="online",
            detail="Fake AI online",
            setup_hint="Running",
            checked_at=datetime.now(timezone.utc),
        )

    async def generate_chat_reply(
        self, messages: List[Dict[str, str]], system_prompt: str = ""
    ) -> AICompletionResult:
        if not self.available:
            raise AIUnavailableError("Local AI server is offline", status_code=503)
        self.calls.append(messages)
        last_user = messages[-1]["content"]
        prior_count = len(messages) - 1
        return AICompletionResult(
            content=f"AI reply to '{last_user}' (context messages: {prior_count})",
            provider="llamacpp",
            model="qwen2.5-1.5b-instruct-q4_k_m",
        )

    async def generate_chat_stream(
        self, messages: List[Dict[str, str]], system_prompt: str = ""
    ):
        if not self.available:
            raise AIUnavailableError("Local AI server is offline", status_code=503)
        res = await self.generate_chat_reply(messages, system_prompt)
        for part in res.content.split():
            yield part + " "


@pytest.fixture()
def test_db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def fake_ai():
    return FakeAIService(available=True)


@pytest.fixture()
def client(test_db_session, fake_ai, tmp_path: Path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("EXPOSE_DEV_RESET_TOKEN", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-minimum-32-characters-long")
    get_settings.cache_clear()
    auth_rate_limiter.reset()

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_service] = lambda: fake_ai
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def register_and_login(
    client: TestClient,
    *,
    full_name: str = "Alice Morgan",
    email: str = "alice@example.com",
    password: str = "HealthPass123",
) -> dict:
    resp = client.post(
        "/api/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
