from tests.conftest import register_and_login


def test_chat_lifecycle_context_and_ownership(client, fake_ai):
    alice = register_and_login(client, email="alice@example.com")
    bob = register_and_login(client, full_name="Bob", email="bob@example.com")
    alice_headers = {"Authorization": f"Bearer {alice['access_token']}"}
    bob_headers = {"Authorization": f"Bearer {bob['access_token']}"}

    # Health check
    health = client.get("/api/chat/health", headers=alice_headers)
    assert health.status_code == 200
    assert health.json()["available"] is True

    # Create conversation
    conv = client.post("/api/chat/conversations", json={}, headers=alice_headers)
    assert conv.status_code == 201
    conv_id = conv.json()["id"]

    # Send general-purpose programming question
    m1 = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"content": "Explain Python list comprehensions simply"},
        headers=alice_headers,
    )
    assert m1.status_code == 201
    assert "Explain Python list comprehensions" in m1.json()["assistant_message"]["content"]
    assert m1.json()["conversation"]["title"].startswith("Explain Python")

    # Follow-up question preserves context
    m2 = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"content": "Can you give a healthcare data filtering example?"},
        headers=alice_headers,
    )
    assert m2.status_code == 201
    assert "context messages: 2" in m2.json()["assistant_message"]["content"]

    # Rename conversation
    renamed = client.patch(
        f"/api/chat/conversations/{conv_id}",
        json={"title": "Python Tips"},
        headers=alice_headers,
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Python Tips"

    # Bob cannot access, rename, message, or delete Alice's conversation
    assert client.get(f"/api/chat/conversations/{conv_id}", headers=bob_headers).status_code == 404
    assert (
        client.patch(
            f"/api/chat/conversations/{conv_id}",
            json={"title": "Hijacked"},
            headers=bob_headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/chat/conversations/{conv_id}/messages",
            json={"content": "Hello"},
            headers=bob_headers,
        ).status_code
        == 404
    )
    assert client.delete(f"/api/chat/conversations/{conv_id}", headers=bob_headers).status_code == 404

    # Graceful offline error does not crash app or persist partial message
    fake_ai.available = False
    offline_resp = client.post(
        f"/api/chat/conversations/{conv_id}/messages",
        json={"content": "Are you online?"},
        headers=alice_headers,
    )
    assert offline_resp.status_code == 503

    # Offline streaming returns immediate 503 without saving orphan user message
    offline_stream = client.post(
        f"/api/chat/conversations/{conv_id}/stream",
        json={"content": "Stream will fail fast"},
        headers=alice_headers,
    )
    assert offline_stream.status_code == 503

    msgs = client.get(
        f"/api/chat/conversations/{conv_id}/messages", headers=alice_headers
    )
    assert len(msgs.json()) == 4

    # Online streaming succeeds and updates DB
    fake_ai.available = True
    online_stream = client.post(
        f"/api/chat/conversations/{conv_id}/stream",
        json={"content": "Stream will succeed"},
        headers=alice_headers,
    )
    assert online_stream.status_code == 200
    assert "data: " in online_stream.text

    msgs_after = client.get(
        f"/api/chat/conversations/{conv_id}/messages", headers=alice_headers
    )
    assert len(msgs_after.json()) == 6

    # Alice deletes conversation
    assert client.delete(f"/api/chat/conversations/{conv_id}", headers=alice_headers).status_code == 200
    assert client.get("/api/chat/conversations", headers=alice_headers).json() == []
