from tests.conftest import register_and_login


def test_dashboard_summary_and_activity_reflect_real_data(client):
    tokens = register_and_login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    summary = client.get("/api/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    data = summary.json()
    assert data["user"]["email"] == "alice@example.com"
    assert data["stats"]["total_assessments"] == 0
    assert data["stats"]["total_reports"] == 0
    assert data["stats"]["total_activities"] >= 1
    assert data["ai_status"]["available"] is True

    # Create a symptom assessment and verify stats update
    client.post(
        "/api/symptoms/assess",
        json={
            "symptoms": ["Cough", "Sore Throat"],
            "duration": "1-3 days",
            "severity": "mild",
        },
        headers=headers,
    )

    updated = client.get("/api/dashboard/summary", headers=headers)
    assert updated.status_code == 200
    assert updated.json()["stats"]["total_assessments"] == 1
    assert len(updated.json()["recent_assessments"]) == 1

    activity = client.get("/api/dashboard/activity", headers=headers)
    assert activity.status_code == 200
    assert len(activity.json()) >= 2
