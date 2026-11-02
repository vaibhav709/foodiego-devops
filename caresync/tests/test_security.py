import pytest

from caresync import create_app

DOC, DESK = "doc-test-key-0001", "desk-test-key-0002"


@pytest.fixture()
def c():
    return create_app(keys={DOC: "doctor", DESK: "frontdesk"}).test_client()


def test_health_public(c):
    assert c.get("/healthz").status_code == 200


def test_no_key_401(c):
    assert c.get("/api/patients/CS-101").status_code == 401


def test_wrong_key_401(c):
    assert c.get("/api/patients/CS-101", headers={"X-API-Key": "nope"}).status_code == 401


def test_pii_masked(c):
    p = c.get("/api/patients/CS-101", headers={"X-API-Key": DESK}).get_json()
    assert p["phone"] == "******2345" and p["abha_id"].endswith("0123") and p["abha_id"].startswith("*")


def test_frontdesk_cannot_prescribe(c):
    r = c.post("/api/prescriptions", headers={"X-API-Key": DESK},
               json={"patient_id": "CS-101", "drug": "Paracetamol", "dose": "500 mg"})
    assert r.status_code == 403


def test_doctor_can_prescribe(c):
    r = c.post("/api/prescriptions", headers={"X-API-Key": DOC},
               json={"patient_id": "CS-101", "drug": "Paracetamol", "dose": "500 mg"})
    assert r.status_code == 201


def test_injection_rejected(c):
    r = c.post("/api/prescriptions", headers={"X-API-Key": DOC},
               json={"patient_id": "CS-101", "drug": "<script>alert(1)</script>", "dose": "500 mg"})
    assert r.status_code == 400


def test_double_booking_prevented(c):
    h = {"X-API-Key": DESK}
    assert c.post("/api/appointments", headers=h, json={"patient_id": "CS-101", "slot": "10:00"}).status_code == 201
    assert c.post("/api/appointments", headers=h, json={"patient_id": "CS-102", "slot": "10:00"}).status_code == 409


def test_security_headers(c):
    h = c.get("/healthz").headers
    assert h["X-Frame-Options"] == "DENY" and "default-src 'none'" in h["Content-Security-Policy"]
    assert h["Cache-Control"] == "no-store"


def test_body_size_limit(c):
    r = c.post("/api/appointments", headers={"X-API-Key": DESK}, data="x" * 10000, content_type="application/json")
    assert r.status_code == 413
