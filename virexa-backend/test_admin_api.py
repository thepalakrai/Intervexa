"""API-level checks for /admin/questions (auth, CRUD, review, seed).

Run:  python test_admin_api.py
Stubs the Azure SDKs (not needed for curation routes) and restores the
local curated file afterwards.
"""
import json
import os
import shutil
import sys
import types

for name in ["azure", "azure.cosmos", "azure.storage", "azure.storage.blob"]:
    sys.modules[name] = types.ModuleType(name)
sys.modules["azure.cosmos"].CosmosClient = object
sys.modules["azure.cosmos"].PartitionKey = object
sys.modules["azure.storage.blob"].BlobServiceClient = object
_pypdf = types.ModuleType("pypdf")
_pypdf.PdfReader = object
sys.modules["pypdf"] = _pypdf
_bcrypt = types.ModuleType("bcrypt")  # only hash/verify need it; admin tests use JWT only
_bcrypt.hashpw = lambda pw, salt: pw
_bcrypt.gensalt = lambda: b""
_bcrypt.checkpw = lambda pw, h: True
sys.modules["bcrypt"] = _bcrypt

for var in ("COSMOS_ENDPOINT", "COSMOS_KEY"):
    os.environ.pop(var, None)

LOCAL_FILE = os.path.join(os.path.dirname(__file__), "data", "questions_curated.json")
BACKUP = LOCAL_FILE + ".testbak2"
if os.path.exists(LOCAL_FILE):
    shutil.copy2(LOCAL_FILE, BACKUP)
elif os.path.exists(BACKUP):
    os.remove(BACKUP)

import main
from fastapi.testclient import TestClient

client = TestClient(main.app)
ADMIN = {"user_id": "u1", "email": "admin@example.com"}
main.app.dependency_overrides[main.get_current_user] = lambda: ADMIN
main.app.dependency_overrides[main.require_admin] = lambda: ADMIN

if os.path.exists(LOCAL_FILE):
    os.remove(LOCAL_FILE)

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"  PASS {name}")


def test_unauthorized_without_token():
    main.app.dependency_overrides.clear()
    r = TestClient(main.app).get("/admin/questions")
    assert r.status_code == 401, r.status_code
    main.app.dependency_overrides[main.get_current_user] = lambda: ADMIN
    main.app.dependency_overrides[main.require_admin] = lambda: ADMIN


def test_create_list_get():
    r = client.post("/admin/questions", json={
        "topic": "Nursing", "difficulty": 2,
        "text": "How do you handle a distressed family member?",
        "expected_concepts": ["empathy"], "domain": "Nursing",
    })
    assert r.status_code == 201, r.text
    qid = r.json()["id"]
    assert r.json()["status"] == "draft"

    # duplicate -> 409
    r2 = client.post("/admin/questions", json={
        "topic": "Nursing", "difficulty": 2,
        "text": "How do you handle a distressed family member?",
    })
    assert r2.status_code == 409, r2.status_code

    # invalid -> 422
    r3 = client.post("/admin/questions", json={"topic": "Nope", "difficulty": 2, "text": "Long enough question here?"})
    assert r3.status_code == 422, r3.status_code

    # client cannot force status=active
    r4 = client.post("/admin/questions", json={
        "topic": "Nursing", "difficulty": 2,
        "text": "Trying to sneak straight to active status here?",
        "status": "active",
    })
    assert r4.status_code == 422, r4.status_code

    r5 = client.get("/admin/questions", params={"topic": "Nursing", "status": "draft"})
    assert r5.json()["total"] == 1, r5.json()

    r6 = client.get(f"/admin/questions/{qid}")
    assert r6.status_code == 200 and r6.json()["id"] == qid

    r7 = client.get("/admin/questions/does-not-exist")
    assert r7.status_code == 404


def test_review_lifecycle():
    qid = client.get("/admin/questions").json()["items"][0]["id"]
    assert client.post(f"/admin/questions/{qid}/review", json={"action": "approve"}).json()["status"] == "active"
    bad = client.post(f"/admin/questions/{qid}/review", json={"action": "approve"})
    assert bad.status_code == 422, bad.status_code
    # edit active text -> demoted
    edited = client.patch(f"/admin/questions/{qid}", json={"text": "How do you calm an anxious patient before surgery?"})
    assert edited.json()["status"] == "pending_review", edited.json()
    assert client.post(f"/admin/questions/{qid}/review", json={"action": "approve"}).json()["status"] == "active"
    # soft delete -> archived, still retrievable
    assert client.delete(f"/admin/questions/{qid}").json()["archived"]["status"] == "archived"
    assert client.get("/admin/questions", params={"status": "active"}).json()["total"] == 0


def test_bulk_and_seed():
    r = client.post("/admin/questions/bulk", json={"items": [
        {"topic": "Sales", "difficulty": 2, "text": "Walk me through a cold call that worked well for you?"},
        {"topic": "Sales", "difficulty": 2, "text": "Walk me through a cold call that worked well for you?"},
        {"topic": "Bogus", "difficulty": 2, "text": "This one has a bad topic field here?"},
    ]})
    body = r.json()
    assert body["created_count"] == 1 and len(body["errors"]) == 2, body
    s1 = client.post("/admin/questions/seed").json()
    s2 = client.post("/admin/questions/seed").json()
    assert s1["imported"] > 100 and s2["imported"] == 0, (s1, s2)
    actives = client.get("/admin/questions", params={"status": "active", "limit": 200}).json()
    assert actives["total"] == s1["imported"], (actives["total"], s1)


try:
    check("401-without-token", test_unauthorized_without_token)
    check("create-list-get", test_create_list_get)
    check("review-lifecycle", test_review_lifecycle)
    check("bulk-and-seed", test_bulk_and_seed)
    print(f"ALL {len(passed)} ADMIN API CHECKS PASSED")
finally:
    main.app.dependency_overrides.clear()
    if os.path.exists(LOCAL_FILE):
        os.remove(LOCAL_FILE)
    if os.path.exists(BACKUP):
        shutil.move(BACKUP, LOCAL_FILE)
