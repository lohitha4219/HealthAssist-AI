import asyncio
from datetime import date, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.config import Settings
from app.models.doctor import DoctorAvailability, DoctorLeave, DoctorProfile
from app.models.hospital import Hospital, HospitalDepartment
from app.models.user import User
from app.services.ai_service import AIStatus, AIUnavailableError, LocalAIService
from tests.conftest import register_and_login


def test_gemini_health_unconfigured():
    settings = Settings(GEMINI_API_KEY="", AI_PROVIDER="auto")
    svc = LocalAIService(settings=settings)
    status = svc.check_gemini()
    assert status.available is False
    assert status.provider == "gemini"
    assert status.status == "unconfigured"
    assert "aistudio.google.com" in status.setup_hint


def test_gemini_health_configured():
    settings = Settings(GEMINI_API_KEY="test-gemini-key-12345", AI_PROVIDER="auto")
    svc = LocalAIService(settings=settings)
    status = svc.check_gemini()
    assert status.available is True
    assert status.provider == "gemini"
    assert status.status == "online"
    assert status.model == "gemini-3.5-flash"


@pytest.mark.asyncio
async def test_auto_resolution_prefers_gemini_when_key_set():
    settings = Settings(GEMINI_API_KEY="test-gemini-key", AI_PROVIDER="auto")
    svc = LocalAIService(settings=settings)
    health = await svc.get_health()
    assert health.available is True
    assert health.provider == "gemini"


@pytest.mark.asyncio
async def test_gemini_generate_chat_reply_mocked():
    settings = Settings(GEMINI_API_KEY="test-gemini-key", AI_PROVIDER="gemini")
    svc = LocalAIService(settings=settings)

    mock_resp = MagicMock()
    mock_resp.text = "Normal fasting glucose is typically 70 to 99 mg/dL. Consult a doctor for diagnosis."

    mock_aio_models = AsyncMock()
    mock_aio_models.generate_content.return_value = mock_resp

    mock_client = MagicMock()
    mock_client.aio.models = mock_aio_models

    with patch("google.genai.Client", return_value=mock_client):
        res = await svc.generate_chat_reply(
            messages=[{"role": "user", "content": "What is normal fasting blood sugar?"}]
        )
        assert res.provider == "gemini"
        assert "70 to 99 mg/dL" in res.content
        assert mock_aio_models.generate_content.called


def test_doctor_slots_and_booking_concurrency(client, test_db_session):
    db = test_db_session
    # 1. Create hospital and department
    h = Hospital(
        name="Apollo Health City Test",
        slug="apollo-health-city-test",
        hospital_type="Super Specialty Hospital",
        address="Health City, Arilova, Visakhapatnam",
        city="Visakhapatnam",
        district="Visakhapatnam",
        state="Andhra Pradesh",
        phone="0891-2867777",
        website="https://www.apollohospitals.com",
        verification_status="verified",
        is_published=True,
        is_active=True,
    )
    db.add(h)
    db.flush()

    dept = HospitalDepartment(hospital_id=h.id, name="Cardiology", is_verified=True)
    db.add(dept)
    db.flush()

    # 2. Create doctor user and profile
    doc_user = User(
        email="doc.test.cardio@example.com",
        hashed_password="hashedpassword123",
        full_name="Dr. Test Cardiologist",
        role="doctor",
        is_active=True,
    )
    db.add(doc_user)
    db.flush()

    doc_profile = DoctorProfile(
        user_id=doc_user.id,
        hospital_id=h.id,
        department_id=dept.id,
        qualification="MBBS, MD, DM (Cardiology)",
        specialization="Cardiology",
        designation="Senior Consultant Cardiologist",
        published_timings="Mon-Sat 09:00 AM - 01:00 PM",
        official_source_url="https://www.apollohospitals.com/doctors",
        listing_source="official_directory",
        verification_status="verified",
        languages=["English", "Telugu"],
    )
    db.add(doc_profile)
    db.flush()

    # 3. Add availability rule for Monday (day_of_week=0)
    avail = DoctorAvailability(
        doctor_id=doc_profile.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(11, 0),
        slot_duration_minutes=30,
        break_start=None,
        break_end=None,
        is_active=True,
    )
    db.add(avail)
    db.commit()

    # Calculate target upcoming Monday
    today = date.today()
    days_ahead = (0 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    target_monday = today + timedelta(days=days_ahead)

    # 4. Query doctor slots
    slots_resp = client.get(
        f"/api/doctors/{doc_profile.id}/slots?date={target_monday.isoformat()}"
    )
    assert slots_resp.status_code == 200
    slots_data = slots_resp.json()
    assert slots_data["unavailable_reason"] is None
    assert len(slots_data["slots"]) == 4  # 09:00, 09:30, 10:00, 10:30
    assert slots_data["slots"][0]["time"] == "09:00"
    assert slots_data["slots"][0]["available"] is True

    # 5. Register patient and book 09:00 slot
    patient = register_and_login(client, email="patient1.booking@example.com")
    headers = {"Authorization": f"Bearer {patient['access_token']}"}

    book_res = client.post(
        "/api/appointments",
        json={
            "doctor_id": doc_profile.id,
            "hospital_id": h.id,
            "appointment_date": target_monday.isoformat(),
            "appointment_time": "09:00:00",
            "reason": "Chest tightness on moderate exertion",
        },
        headers=headers,
    )
    assert book_res.status_code == 201
    appt_data = book_res.json()
    assert appt_data["status"] == "pending"
    assert appt_data["doctor_name"] == "Dr. Test Cardiologist"

    # 6. Verify 09:00 slot is now marked available=False
    slots_after = client.get(
        f"/api/doctors/{doc_profile.id}/slots?date={target_monday.isoformat()}"
    ).json()
    s0 = next(s for s in slots_after["slots"] if s["time"] == "09:00")
    assert s0["available"] is False

    # 7. Attempting to book the same slot again with patient 2 must return 409 Conflict
    patient2 = register_and_login(client, email="patient2.booking@example.com")
    headers2 = {"Authorization": f"Bearer {patient2['access_token']}"}

    conflict_res = client.post(
        "/api/appointments",
        json={
            "doctor_id": doc_profile.id,
            "hospital_id": h.id,
            "appointment_date": target_monday.isoformat(),
            "appointment_time": "09:00:00",
            "reason": "Routine cardiac consultation",
        },
        headers=headers2,
    )
    assert conflict_res.status_code == 409
    assert "already been booked" in conflict_res.json()["detail"].lower()


def test_doctor_detail_contains_official_source_and_timings(client, test_db_session):
    db = test_db_session
    h = Hospital(
        name="SVIMS Tirupati Test",
        slug="svims-tirupati-test",
        hospital_type="Autonomous Tertiary Medical Institute",
        address="Alipiri Road, Tirupati",
        city="Tirupati",
        district="Tirupati",
        state="Andhra Pradesh",
        phone="0877-2287777",
        website="https://svimstpt.ap.nic.in",
        verification_status="verified",
        is_published=True,
        is_active=True,
    )
    db.add(h)
    db.flush()

    u = User(
        email="doc.svims.prof@example.com",
        hashed_password="pw",
        full_name="Dr. Senior SVIMS Professor",
        role="doctor",
        is_active=True,
    )
    db.add(u)
    db.flush()

    doc = DoctorProfile(
        user_id=u.id,
        hospital_id=h.id,
        qualification="MBBS, MD, DM",
        specialization="Cardiology",
        designation="Senior Professor & Head, Department of Cardiology",
        published_timings="Mon-Sat 09:00 AM - 01:00 PM (OPD)",
        official_source_url="https://svimstpt.ap.nic.in/faculty",
        listing_source="official_directory",
        verification_status="verified",
        languages=["English", "Telugu"],
    )
    db.add(doc)
    db.commit()

    detail_res = client.get(f"/api/doctors/{doc.id}")
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["full_name"] == "Dr. Senior SVIMS Professor"
    assert data["designation"] == "Senior Professor & Head, Department of Cardiology"
    assert data["published_timings"] == "Mon-Sat 09:00 AM - 01:00 PM (OPD)"
    assert data["official_source_url"] == "https://svimstpt.ap.nic.in/faculty"
    assert data["hospital_name"] == "SVIMS Tirupati Test"
    assert data["hospital_website"] == "https://svimstpt.ap.nic.in"
