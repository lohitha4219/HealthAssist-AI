from datetime import date, timedelta
import io

from app.models.education_contact import TreatmentEducation
from app.models.hospital import (
    Hospital,
    HospitalDepartment,
    HospitalFacility,
    HospitalTreatment,
)
from tests.conftest import register_and_login


def _seed_hospital_and_treatment(db):
    h = Hospital(
        name="AIIMS Mangalagiri",
        slug="aiims-mangalagiri",
        hospital_type="Autonomous Tertiary Hospital",
        address="Mangalagiri, Guntur District, Andhra Pradesh",
        city="Mangalagiri",
        district="Guntur",
        state="Andhra Pradesh",
        phone="08645-280021",
        verification_status="verified",
        is_published=True,
        is_active=True,
    )
    db.add(h)
    db.flush()
    dept = HospitalDepartment(hospital_id=h.id, name="Cardiology", is_verified=True)
    db.add(dept)
    db.flush()
    db.add(HospitalFacility(hospital_id=h.id, name="24x7 Emergency", is_verified=True))
    db.add(
        HospitalTreatment(
            hospital_id=h.id,
            department_id=dept.id,
            name="Cardiology Evaluation",
            specialty="Cardiology",
            is_verified=True,
        )
    )
    db.add(
        TreatmentEducation(
            specialty="Cardiology",
            slug="cardiology",
            description="Heart and blood vessel evaluation.",
            common_reasons=["Blood pressure check"],
            preparation=["Bring prior ECGs"],
            precautions=["Do not stop heart medicine without physician advice"],
            aftercare=["Track blood pressure"],
            when_to_consult=["Persistent palpitations"],
            emergency_signs=["Chest pain"],
            sources=["WHO"],
            reviewed_by="Clinical Reference",
            last_reviewed_date=date(2026, 10, 15),
        )
    )
    db.commit()
    return h.id, dept.id


def _make_lab_pdf_bytes() -> bytes:
    lines = [
        "Hemoglobin 10.5 g/dL 12.0 - 16.0",
        "Fasting Glucose 92 mg/dL 70 - 99",
        "Vitamin D 28 ng/mL",
    ]
    ops = ["BT /F1 11 Tf"]
    y = 180
    for ln in lines:
        ops.append(f"1 0 0 1 20 {y} Tm ({ln}) Tj")
        y -= 18
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")
    objs = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 400 240] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
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
    xref = len(body)
    body += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode("latin-1")
    for off in offsets:
        body += f"{off:010d} 00000 n \n".encode("latin-1")
    body += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode(
        "latin-1"
    )
    return body


def test_public_hospitals_contact_treatments_and_maintenance(client, test_db_session, monkeypatch):
    monkeypatch.setenv("HOSPITAL_MAINTENANCE_KEY", "maint-secret-key")
    from app.core.config import get_settings

    get_settings.cache_clear()

    h_id, _ = _seed_hospital_and_treatment(test_db_session)

    overview = client.get("/api/public/overview")
    assert overview.status_code == 200
    assert overview.json()["stats"]["verified_hospitals"] == 1
    assert overview.json()["stats"]["specialties"] == 1

    # Filter hospitals by district and facility
    hospitals = client.get("/api/hospitals?district=Guntur&facility=Emergency")
    assert hospitals.status_code == 200
    assert hospitals.json()["total"] == 1

    detail = client.get(f"/api/hospitals/{h_id}")
    assert detail.status_code == 200
    assert detail.json()["name"] == "AIIMS Mangalagiri"

    treatments = client.get("/api/treatments")
    assert treatments.status_code == 200
    assert len(treatments.json()[0]["verified_hospitals"]) == 1

    # Contact enquiry saved
    enquiry = client.post(
        "/api/contact",
        json={
            "name": "Ravi Kumar",
            "email": "ravi@example.com",
            "subject": "Hospital Info",
            "message": "Confirming OPD timings for Cardiology department.",
        },
    )
    assert enquiry.status_code == 201
    enq_data = enquiry.json()
    assert enq_data["id"] is not None
    assert "delivery_status" in enq_data

    # Test with mocked SMTP delivery to nslohitha2924@gmail.com
    from unittest.mock import MagicMock
    mock_smtp_instance = MagicMock()
    monkeypatch.setattr("smtplib.SMTP", lambda *args, **kwargs: mock_smtp_instance)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USERNAME", "mailer@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SUPPORT_EMAIL", "nslohitha2924@gmail.com")
    from app.core.config import get_settings
    get_settings.cache_clear()

    delivered_enquiry = client.post(
        "/api/contact",
        json={
            "name": "Lakshmi Rao",
            "email": "lakshmi@example.com",
            "subject": "Cardiology Consultation",
            "message": "Enquiring about senior cardiologist appointment timings.",
        },
    )
    assert delivered_enquiry.status_code == 201
    delivered_data = delivered_enquiry.json()
    assert delivered_data["email_delivered"] is True
    assert delivered_data["delivery_status"] == "sent"
    assert "nslohitha2924@gmail.com" in delivered_data["message"]
    assert mock_smtp_instance.send_message.called
    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert sent_msg["To"] == "nslohitha2924@gmail.com"
    assert "Lakshmi Rao" in sent_msg["Reply-To"]
    assert "lakshmi@example.com" in sent_msg["Reply-To"]
    assert "Cardiology Consultation" in sent_msg["Subject"]
    get_settings.cache_clear()

    # Maintenance requires valid key (patients cannot modify)
    unauth_maint = client.post(
        "/api/hospitals/maintain",
        json={
            "name": "Unauthorized Hospital",
            "hospital_type": "General",
            "address": "123 Street",
            "city": "Tirupati",
            "district": "Tirupati",
        },
    )
    assert unauth_maint.status_code == 403


def test_doctor_onboarding_booking_double_book_prevention_and_notes(
    client, test_db_session, monkeypatch
):
    monkeypatch.setenv("DOCTOR_ONBOARDING_KEY", "onboard-secret-key")
    from app.core.config import get_settings

    get_settings.cache_clear()

    h_id, dept_id = _seed_hospital_and_treatment(test_db_session)

    # 1. Patient registers and uploads a lab PDF with supplied & unsupplied ranges
    p1 = register_and_login(client, full_name="Patient One", email="p1@example.com")
    p2 = register_and_login(client, full_name="Patient Two", email="p2@example.com")
    p1_headers = {"Authorization": f"Bearer {p1['access_token']}"}
    p2_headers = {"Authorization": f"Bearer {p2['access_token']}"}

    pdf_bytes = _make_lab_pdf_bytes()
    rep = client.post(
        "/api/reports/upload",
        files={"file": ("cbc.pdf", pdf_bytes, "application/pdf")},
        data={"category": "Lab Results"},
        headers=p1_headers,
    )
    assert rep.status_code == 201, rep.text
    analysis = rep.json()["analysis"]
    assert analysis["parsed_count"] >= 2
    assert analysis["out_of_range_count"] >= 1
    vit_d = next((f for f in analysis["findings"] if "Vitamin D" in f["test_name"]), None)
    if vit_d:
        assert vit_d["status"] == "range_not_supplied"
        assert vit_d["reference_range"] is None

    # 2. Issue doctor invitation & onboard verified doctor
    inv = client.post(
        "/api/auth/doctor-invite",
        json={
            "email": "dr.priya@example.com",
            "hospital_id": h_id,
            "department_id": dept_id,
            "specialization": "Cardiology",
        },
        headers={"X-Onboarding-Key": "onboard-secret-key"},
    )
    assert inv.status_code == 201
    invite_token = inv.json()["invitation_token"]

    doc_reg = client.post(
        "/api/auth/doctor-register",
        json={
            "invitation_token": invite_token,
            "full_name": "Dr. Priya Rao",
            "email": "dr.priya@example.com",
            "password": "DoctorPass123",
            "confirm_password": "DoctorPass123",
            "qualification": "MBBS, MD, DM",
            "specialization": "Cardiology",
            "experience_years": 9,
            "license_number": "APMC-98765",
            "languages": ["English", "Telugu"],
            "consultation_fee": 500,
        },
    )
    assert doc_reg.status_code == 201, doc_reg.text
    assert doc_reg.json()["user"]["role"] == "doctor"
    doc_headers = {"Authorization": f"Bearer {doc_reg.json()['access_token']}"}

    # Patient cannot access doctor portal
    assert client.get("/api/doctor/dashboard", headers=p1_headers).status_code == 403
    # Doctor cannot access patient appointments endpoint
    assert client.get("/api/appointments/my", headers=doc_headers).status_code == 403

    # Find doctor ID
    docs_list = client.get("/api/doctors")
    assert docs_list.status_code == 200
    assert docs_list.json()["total"] == 1
    doctor_id = docs_list.json()["items"][0]["id"]

    # 3. Doctor configures availability for tomorrow's weekday
    tomorrow = date.today() + timedelta(days=2)
    avail = client.put(
        "/api/doctor/availability",
        json=[
            {
                "day_of_week": tomorrow.weekday(),
                "start_time": "09:00:00",
                "end_time": "12:00:00",
                "slot_duration_minutes": 30,
                "is_active": True,
            }
        ],
        headers=doc_headers,
    )
    assert avail.status_code == 200

    # Slots returned
    slots = client.get(f"/api/doctors/{doctor_id}/slots?date={tomorrow.isoformat()}")
    assert slots.status_code == 200
    assert len(slots.json()["slots"]) == 6

    # Past date rejected
    yesterday = date.today() - timedelta(days=1)
    past_book = client.post(
        "/api/appointments",
        json={
            "doctor_id": doctor_id,
            "hospital_id": h_id,
            "appointment_date": yesterday.isoformat(),
            "appointment_time": "09:00:00",
            "reason": "Past date test",
        },
        headers=p1_headers,
    )
    assert past_book.status_code == 400

    # Patient 1 books 09:00 with share_reports=True
    book1 = client.post(
        "/api/appointments",
        json={
            "doctor_id": doctor_id,
            "hospital_id": h_id,
            "appointment_date": tomorrow.isoformat(),
            "appointment_time": "09:00:00",
            "reason": "Routine blood pressure consultation",
            "share_reports": True,
        },
        headers=p1_headers,
    )
    assert book1.status_code == 201, book1.text
    appt_id = book1.json()["id"]

    # Patient 2 double-booking same slot -> 409 Conflict
    book2 = client.post(
        "/api/appointments",
        json={
            "doctor_id": doctor_id,
            "hospital_id": h_id,
            "appointment_date": tomorrow.isoformat(),
            "appointment_time": "09:00:00",
            "reason": "Double book attempt",
        },
        headers=p2_headers,
    )
    assert book2.status_code == 409

    # Doctor confirms, views shared reports, adds shareable + private notes, completes
    assert (
        client.patch(
            f"/api/doctor/appointments/{appt_id}/status",
            json={"status": "confirmed"},
            headers=doc_headers,
        ).status_code
        == 200
    )

    shared_reps = client.get(
        f"/api/doctor/appointments/{appt_id}/reports", headers=doc_headers
    )
    assert shared_reps.status_code == 200
    assert len(shared_reps.json()) == 1

    client.post(
        f"/api/doctor/appointments/{appt_id}/notes",
        json={"observations": "Shareable BP observation", "is_shareable": True},
        headers=doc_headers,
    )
    client.post(
        f"/api/doctor/appointments/{appt_id}/notes",
        json={"observations": "Internal private doctor memo", "is_shareable": False},
        headers=doc_headers,
    )
    client.patch(
        f"/api/doctor/appointments/{appt_id}/status",
        json={"status": "completed"},
        headers=doc_headers,
    )

    # Patient sees ONLY shareable notes + notifications
    my_appts = client.get("/api/appointments/my", headers=p1_headers)
    assert my_appts.status_code == 200
    notes = my_appts.json()[0]["consultation_notes"]
    assert len(notes) == 1
    assert notes[0]["observations"] == "Shareable BP observation"

    notifs = client.get("/api/notifications", headers=p1_headers)
    assert notifs.status_code == 200
    assert len(notifs.json()) >= 2


def test_forgot_password_honest_smtp_status(client, monkeypatch):
    register_and_login(client, email="smtpcheck@example.com", password="OldPassword1")
    monkeypatch.setenv("EXPOSE_DEV_RESET_TOKEN", "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    res = client.post("/api/auth/forgot-password", json={"email": "smtpcheck@example.com"})
    assert res.status_code == 200
    assert res.json()["email_sent"] is False
    assert "not configured" in res.json()["message"].lower()
