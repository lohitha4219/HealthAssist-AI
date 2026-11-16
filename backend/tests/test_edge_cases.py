from datetime import timedelta
import io

import httpx
import pytest
from pypdf import PdfWriter

from app.core.config import Settings
from app.core.security import create_access_token
from app.services.ai_service import AIUnavailableError, LocalAIService
from tests.conftest import register_and_login


def _make_blank_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _make_text_pdf_bytes(text: str = "Complete Blood Count Normal") -> bytes:
    # Minimal PDF 1.4 containing a Helvetica text stream readable by pypdf
    stream = f"BT /F1 12 Tf 20 100 Td ({text}) Tj ET".encode("latin-1")
    objs = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
        + stream
        + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    body = b"%PDF-1.4\n"
    offsets = []
    for o in objs:
        offsets.append(len(body))
        body += o
    xref_pos = len(body)
    body += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode("latin-1")
    for off in offsets:
        body += f"{off:010d} 00000 n \n".encode("latin-1")
    body += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
        "latin-1"
    )
    return body


def test_pdf_text_extraction_and_scanned_pdf(client):
    tokens = register_and_login(client, email="pdfuser@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Text PDF extracts cleanly
    pdf_bytes = _make_text_pdf_bytes("Hemoglobin 14.2 g/dL")
    res_text = client.post(
        "/api/reports/upload",
        files={"file": ("lab_cbc.pdf", pdf_bytes, "application/pdf")},
        data={"category": "Lab Results"},
        headers=headers,
    )
    assert res_text.status_code == 201, res_text.text
    assert res_text.json()["processing_status"] == "extracted"
    assert "Hemoglobin 14.2" in (res_text.json()["extracted_text"] or "")

    # Scanned/blank PDF handled gracefully without fabricated text
    blank_pdf = _make_blank_pdf_bytes()
    res_blank = client.post(
        "/api/reports/upload",
        files={"file": ("scanned_scan.pdf", blank_pdf, "application/pdf")},
        data={"category": "Imaging"},
        headers=headers,
    )
    assert res_blank.status_code == 201
    assert res_blank.json()["processing_status"] == "scanned_no_text"
    assert res_blank.json()["extracted_text"] is None


def test_expired_jwt_and_weak_password_validation(client):
    weak = client.post(
        "/api/auth/register",
        json={
            "full_name": "Weak Pass",
            "email": "weak@example.com",
            "password": "short",
            "confirm_password": "short",
        },
    )
    assert weak.status_code == 422

    tokens = register_and_login(client, email="exp@example.com")
    expired = create_access_token(
        subject=tokens["user"]["id"],
        expires_delta=timedelta(minutes=-5),
    )
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_local_ai_service_llamacpp_and_ollama_providers(monkeypatch):
    def llamacpp_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "qwen2.5-1.5b-q4"}]})
        if request.url.path == "/v1/chat/completions":
            return httpx.Response(
                200,
                json={
                    "model": "qwen2.5-1.5b-q4",
                    "choices": [{"message": {"content": "Hello from llama.cpp!"}}],
                },
            )
        return httpx.Response(404)

    settings = Settings(AI_PROVIDER="llamacpp")
    svc = LocalAIService(settings=settings)
    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(llamacpp_handler), **kwargs
        ),
    )

    health = await svc.get_health()
    assert health.available is True
    assert health.provider == "llamacpp"
    assert health.model == "qwen2.5-1.5b-q4"

    reply = await svc.generate_chat_reply([{"role": "user", "content": "Hi"}])
    assert reply.content == "Hello from llama.cpp!"
    assert reply.provider == "llamacpp"

    # Now test Ollama missing model handling
    def ollama_missing_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        return httpx.Response(404)

    svc_ollama = LocalAIService(settings=Settings(AI_PROVIDER="ollama"))
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(ollama_missing_handler), **kwargs
        ),
    )
    o_health = await svc_ollama.get_health()
    assert o_health.available is False
    assert o_health.status == "model_missing"
    with pytest.raises(AIUnavailableError):
        await svc_ollama.generate_chat_reply([{"role": "user", "content": "Hi"}])
