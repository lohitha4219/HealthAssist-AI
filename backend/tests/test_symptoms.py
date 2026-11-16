from tests.conftest import register_and_login


def test_symptom_assessment_and_red_flag_isolation(client):
    alice = register_and_login(client, email="alice@example.com")
    bob = register_and_login(client, full_name="Bob Lee", email="bob@example.com")
    alice_headers = {"Authorization": f"Bearer {alice['access_token']}"}
    bob_headers = {"Authorization": f"Bearer {bob['access_token']}"}

    catalog = client.get("/api/symptoms/catalog", headers=alice_headers)
    assert catalog.status_code == 200
    assert len(catalog.json()) >= 20

    # Routine assessment
    routine = client.post(
        "/api/symptoms/assess",
        json={
            "symptoms": ["Headache", "Fatigue / Low Energy"],
            "duration": "1-3 days",
            "severity": "mild",
            "additional_details": "Working long hours at screen",
        },
        headers=alice_headers,
    )
    assert routine.status_code == 201
    routine_data = routine.json()
    assert routine_data["urgency_level"] == "routine"
    assert len(routine_data["possible_causes"]) >= 1
    assert "does not diagnose" in routine_data["disclaimer"].lower()

    # Emergency red-flag symptom triggers urgent_emergency
    urgent = client.post(
        "/api/symptoms/assess",
        json={
            "symptoms": ["Chest Pain or Pressure", "Shortness of Breath"],
            "duration": "< 24 hours",
            "severity": "severe",
        },
        headers=alice_headers,
    )
    assert urgent.status_code == 201
    assert urgent.json()["urgency_level"] == "urgent_emergency"
    assert urgent.json()["emergency_warning"] is not None

    # History isolation: Bob has 0 assessments
    bob_hist = client.get("/api/symptoms/history", headers=bob_headers)
    assert bob_hist.status_code == 200
    assert bob_hist.json()["total"] == 0

    alice_hist = client.get("/api/symptoms/history", headers=alice_headers)
    assert alice_hist.json()["total"] == 2

    # Bob cannot read Alice's assessment
    forbidden = client.get(
        f"/api/symptoms/{routine_data['id']}", headers=bob_headers
    )
    assert forbidden.status_code == 404
