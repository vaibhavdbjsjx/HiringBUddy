"""End-to-end API smoke tests.

Runs with pytest (`pytest tests/`) or standalone (`python tests/test_api.py`).
Uses a throwaway SQLite DB and offline AI mode (no network).
"""
import os
import sys
import tempfile

# Configure a throwaway environment BEFORE importing the app.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["GROQ_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = "dummy-key"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-000000"

# Allow running from the backend dir directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402
import main  # noqa: E402
from database import SessionLocal  # noqa: E402
from db_models import Assessment, Candidate  # noqa: E402

client = TestClient(main.app)
_EMAIL = "tester@example.com"


def _auth():
    r = client.post("/api/auth/register", json={"email": _EMAIL, "password": "supersecret"})
    if r.status_code == 409:
        r = client.post("/api/auth/login", json={"email": _EMAIL, "password": "supersecret"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_auth_protects_recruiter_routes():
    assert client.get("/api/candidates/").status_code == 401
    assert client.get("/api/jobs/").status_code == 401


def test_register_login_me():
    h = _auth()
    me = client.get("/api/auth/me", headers=h)
    assert me.status_code == 200 and me.json()["email"] == _EMAIL


def test_job_create_and_ai_generate():
    h = _auth()
    job = client.post("/api/jobs/", headers=h, json={"title": "Backend Eng", "required_skills": ["python"]}).json()
    full = client.post(f"/api/jobs/{job['id']}/generate", headers=h).json()
    assert full["description"] and full["responsibilities"] and full["technical_questions"]


def test_assessment_generate_scores_and_hides_answers():
    h = _auth()
    a = client.post("/api/assessments/generate", headers=h,
                    json={"skills": ["python"], "num_questions": 3}).json()
    assert a["questions"] and all("answer_index" not in q for q in a["questions"])
    db = SessionLocal()
    correct = [q["answer_index"] for q in db.query(Assessment).filter(Assessment.id == a["id"]).first().questions]
    db.close()
    res = client.post(f"/api/assessments/{a['id']}/submit", headers=h, json={"answers": correct}).json()
    assert res["score"] == 100.0


def test_copilot_ranks_candidates():
    h = _auth()
    db = SessionLocal()
    db.add(Candidate(name="TopCand", status="completed", overall_score=95.0, skills=["python"]))
    db.commit()
    db.close()
    r = client.post("/api/copilot/query", headers=h, json={"message": "top 1"}).json()
    assert r["candidates"] and r["candidates"][0]["name"] == "TopCand"


def test_public_careers_flow():
    h = _auth()
    job = client.post("/api/jobs/", headers=h, json={"title": "Data Analyst"}).json()
    client.patch(f"/api/jobs/{job['id']}", headers=h, json={"status": "open"})
    # public job view (no auth)
    assert client.get(f"/api/jobs/public/{job['public_slug']}").status_code == 200
    # apply (no auth)
    r = client.post(f"/api/jobs/public/{job['public_slug']}/apply",
                    files={"resume": ("cv.pdf", b"%PDF-1.4 test", "application/pdf")})
    assert r.status_code == 200 and r.json().get("application_id")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  [PASS] {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  [FAIL] {t.__name__}: {e}")
    os.unlink(_tmp.name)
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
