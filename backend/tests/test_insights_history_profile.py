from tests.conftest import register_and_login


def test_insights_history_and_profile(client):
    tokens = register_and_login(client, email="user@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Empty insights before activity
    empty_ins = client.get("/api/insights/summary", headers=headers)
    assert empty_ins.status_code == 200
    assert empty_ins.json()["has_data"] is False

    # Add assessment and conversation
    client.post(
        "/api/symptoms/assess",
        json={"symptoms": ["Fever", "Cough"], "duration": "1-3 days", "severity": "moderate"},
        headers=headers,
    )
    client.post("/api/chat/conversations", json={"title": "Wellness Qs"}, headers=headers)

    ins = client.get("/api/insights/summary", headers=headers)
    assert ins.status_code == 200
    assert ins.json()["has_data"] is True
    assert ins.json()["total_assessments"] == 1
    assert ins.json()["top_symptoms"][0]["label"] in {"Fever", "Cough"}

    trends = client.get("/api/insights/trends", headers=headers)
    assert trends.status_code == 200
    assert trends.json()["has_sufficient_data"] is True
    assert len(trends.json()["timeline"]) >= 1

    # Unified history search & filtering
    hist = client.get("/api/history?record_type=assessment&search=Fever", headers=headers)
    assert hist.status_code == 200
    assert hist.json()["total"] == 1
    entry_id = hist.json()["items"][0]["id"]

    # Profile update persists
    prof_upd = client.patch(
        "/api/profile",
        json={
            "full_name": "Alice M. Updated",
            "blood_group": "o+",
            "height_cm": 168.5,
            "weight_kg": 62.0,
            "allergies": "Penicillin",
        },
        headers=headers,
    )
    assert prof_upd.status_code == 200
    assert prof_upd.json()["full_name"] == "Alice M. Updated"
    assert prof_upd.json()["blood_group"] == "O+"

    # Change password
    pw_chg = client.post(
        "/api/profile/change-password",
        json={
            "current_password": "HealthPass123",
            "new_password": "UpdatedPass456",
            "confirm_password": "UpdatedPass456",
        },
        headers=headers,
    )
    assert pw_chg.status_code == 200

    # Delete history record
    del_hist = client.delete(f"/api/history/assessment/{entry_id}", headers=headers)
    assert del_hist.status_code == 200
