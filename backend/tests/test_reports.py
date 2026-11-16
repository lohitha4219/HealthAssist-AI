from io import BytesIO
from PIL import Image

from tests.conftest import register_and_login


def _make_png_bytes() -> bytes:
    buf = BytesIO()
    img = Image.new("RGB", (64, 48), color=(20, 120, 200))
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_report_upload_validation_download_and_isolation(client):
    alice = register_and_login(client, email="alice@example.com")
    bob = register_and_login(client, full_name="Bob", email="bob@example.com")
    alice_headers = {"Authorization": f"Bearer {alice['access_token']}"}
    bob_headers = {"Authorization": f"Bearer {bob['access_token']}"}

    # Invalid magic bytes rejected
    bad_upload = client.post(
        "/api/reports/upload",
        files={"file": ("fake.pdf", b"not really a pdf", "application/pdf")},
        data={"category": "Lab Results"},
        headers=alice_headers,
    )
    assert bad_upload.status_code == 400

    # Valid PNG upload succeeds
    png_bytes = _make_png_bytes()
    good_upload = client.post(
        "/api/reports/upload",
        files={"file": ("scan.png", png_bytes, "image/png")},
        data={"category": "Imaging", "notes": "Chest X-ray summary"},
        headers=alice_headers,
    )
    assert good_upload.status_code == 201
    report = good_upload.json()
    assert report["processing_status"] == "image_stored"
    assert report["image_width"] == 64
    assert report["image_height"] == 48

    # List reports
    listed = client.get("/api/reports", headers=alice_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    # Download report succeeds for owner
    dl = client.get(f"/api/reports/{report['id']}/download", headers=alice_headers)
    assert dl.status_code == 200
    assert dl.content == png_bytes

    # Bob cannot view, download, or delete Alice's report
    assert client.get(f"/api/reports/{report['id']}", headers=bob_headers).status_code == 404
    assert client.get(f"/api/reports/{report['id']}/download", headers=bob_headers).status_code == 404
    assert client.delete(f"/api/reports/{report['id']}", headers=bob_headers).status_code == 404

    # Delete succeeds for owner
    deleted = client.delete(f"/api/reports/{report['id']}", headers=alice_headers)
    assert deleted.status_code == 200
    assert client.get("/api/reports", headers=alice_headers).json()["total"] == 0
