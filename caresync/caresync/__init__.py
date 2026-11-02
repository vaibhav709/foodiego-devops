"""CareSync - secure clinic appointment & e-prescription API (DevSecOps practical).

Security controls
  * API-key auth; the key is read from a file mounted from a Kubernetes Secret (never an env var, never in Git)
  * Role separation: doctors may write prescriptions, front-desk staff may only book appointments
  * PII minimisation: patient phone and ABHA health-ID are masked in every response
  * Strict schema validation, 4 KB body limit, per-client rate limiting
  * Hardened HTTP security headers and generic error messages (no stack traces)
  * Structured audit trail that records actor, action and record id - never clinical content
"""
import hmac
import json
import logging
import os
import re
import time
from collections import defaultdict

from flask import Flask, g, jsonify, request

log = logging.getLogger("caresync.audit")
logging.basicConfig(level=logging.INFO, format="%(message)s")

PATIENTS = {
    "CS-101": {"name": "Rohan Kulkarni", "age": 42, "phone": "9822012345", "abha_id": "91234567890123", "doctor": "Dr. Mehta"},
    "CS-102": {"name": "Sneha Joshi", "age": 29, "phone": "9765098765", "abha_id": "91987654321098", "doctor": "Dr. Rao"},
}
SLOTS = {"09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "16:00", "16:30", "17:00"}


def mask(value, keep=4):
    return "*" * (len(value) - keep) + value[-keep:]


def public(pid, p):
    return {"patient_id": pid, "name": p["name"], "age": p["age"], "doctor": p["doctor"],
            "phone": mask(p["phone"]), "abha_id": mask(p["abha_id"])}


def load_keys():
    """Keys file contains JSON: {"<key>": "doctor"|"frontdesk"}. Path comes from CARESYNC_KEYS_FILE."""
    path = os.environ.get("CARESYNC_KEYS_FILE", "/etc/caresync/keys.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def create_app(keys=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 4 * 1024
    api_keys = keys if keys is not None else load_keys()
    appointments, prescriptions = [], []
    hits = defaultdict(list)

    def audit(event, **extra):
        log.info(json.dumps({"ts": int(time.time()), "event": event, "role": getattr(g, "role", None),
                             "path": request.path, "client": request.remote_addr, **extra}))

    def authorise(*roles):
        supplied = request.headers.get("X-API-Key", "")
        for key, role in api_keys.items():
            if hmac.compare_digest(supplied.encode(), key.encode()):
                g.role = role
                if role in roles:
                    return None
                audit("FORBIDDEN")
                return jsonify(error="forbidden"), 403
        audit("AUTH_FAILED")
        return jsonify(error="unauthorized"), 401

    @app.before_request
    def rate_limit():
        now = time.time()
        window = [t for t in hits[request.remote_addr] if now - t < 60]
        window.append(now)
        hits[request.remote_addr] = window
        if len(window) > 120:
            return jsonify(error="too many requests"), 429
        return None

    @app.after_request
    def headers(resp):
        resp.headers.update({
            "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Resource-Policy": "same-origin",
            "Cache-Control": "no-store",
        })
        resp.headers.pop("Server", None)
        return resp

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="not found"), 404

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error="payload too large"), 413

    @app.errorhandler(Exception)
    def generic(_):
        return jsonify(error="request failed"), 500

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.get("/")
    def index():
        return jsonify(service="CareSync clinic API", endpoints=["/healthz", "GET /api/patients/<id>",
                                                                 "POST /api/appointments", "POST /api/prescriptions"],
                       auth="X-API-Key header required for /api/*")

    @app.get("/api/patients/<pid>")
    def get_patient(pid):
        denied = authorise("doctor", "frontdesk")
        if denied:
            return denied
        if not re.fullmatch(r"CS-\d{3}", pid) or pid not in PATIENTS:
            return jsonify(error="not found"), 404
        audit("PATIENT_READ", record=pid)
        return jsonify(public(pid, PATIENTS[pid]))

    @app.post("/api/appointments")
    def book():
        denied = authorise("doctor", "frontdesk")
        if denied:
            return denied
        b = request.get_json(silent=True) or {}
        if b.get("patient_id") not in PATIENTS or b.get("slot") not in SLOTS:
            return jsonify(error="invalid patient_id or slot"), 400
        if any(a["slot"] == b["slot"] for a in appointments):
            return jsonify(error="slot already booked"), 409
        appt = {"appointment_id": f"AP-{len(appointments) + 1:04d}", "patient_id": b["patient_id"], "slot": b["slot"]}
        appointments.append(appt)
        audit("APPOINTMENT_BOOKED", record=appt["appointment_id"])
        return jsonify(appt), 201

    @app.post("/api/prescriptions")
    def prescribe():
        denied = authorise("doctor")
        if denied:
            return denied
        b = request.get_json(silent=True) or {}
        drug, dose = b.get("drug", ""), b.get("dose", "")
        if b.get("patient_id") not in PATIENTS or not re.fullmatch(r"[A-Za-z0-9 \-]{2,40}", drug) \
                or not re.fullmatch(r"[0-9]{1,4} ?(mg|ml|mcg)", dose):
            return jsonify(error="invalid prescription"), 400
        rx = {"rx_id": f"RX-{len(prescriptions) + 1:04d}", "patient_id": b["patient_id"], "drug": drug, "dose": dose}
        prescriptions.append(rx)
        audit("PRESCRIPTION_CREATED", record=rx["rx_id"])
        return jsonify(rx), 201

    return app
