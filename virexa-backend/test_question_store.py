"""Curation layer checks: validation, dedup, review workflow, retrieval.

Run:  python test_question_store.py
Uses the local JSON backend (no Cosmos creds in env) and restores the
pre-existing curated file afterwards, so it never pollutes real data.
"""
import json
import os
import shutil

LOCAL_FILE = os.path.join(os.path.dirname(__file__), "data", "questions_curated.json")
BACKUP = LOCAL_FILE + ".testbak"

if os.path.exists(LOCAL_FILE):
    shutil.copy2(LOCAL_FILE, BACKUP)

# Force local backend even if Cosmos env vars leak in.
for var in ("COSMOS_ENDPOINT", "COSMOS_KEY"):
    os.environ.pop(var, None)

from services import question_store as qs
from services.question_store import (
    DuplicateQuestionError, QuestionValidationError,
)

passed = []


def check(name, fn):
    fn()
    passed.append(name)
    print(f"  PASS {name}")


def test_validation():
    for bad, kwargs in [
        ("bad topic", dict(topic="Nope", difficulty=2, text="This is a long enough question text?")),
        ("bad difficulty", dict(topic="Nursing", difficulty=9, text="This is a long enough question text?")),
        ("short text", dict(topic="Nursing", difficulty=2, text="Too short")),
        ("bad domain", dict(topic="Nursing", difficulty=2, text="This is a long enough question text?", domain="Mars")),
        ("bad status", dict(topic="Nursing", difficulty=2, text="This is a long enough question text?", status="live")),
    ]:
        try:
            qs.create_question(**kwargs)
        except QuestionValidationError:
            continue
        raise AssertionError(f"{bad} was accepted")


def test_create_and_dedup():
    d = qs.create_question(
        topic="Nursing", difficulty=2,
        text="How do you prioritize care with multiple patients at once?",
        expected_concepts=["triage"], domain="Nursing", status="draft",
        source="manual", created_by="test",
    )
    assert d["status"] == "draft" and d["id"].startswith("q_"), d
    # exact + case/punctuation variants must 409
    for variant in [
        "How do you prioritize care with multiple patients at once?",
        "  how do you prioritize care with multiple patients at once!! ",
    ]:
        try:
            qs.create_question(topic="Nursing", difficulty=3, text=variant)
        except DuplicateQuestionError as e:
            assert e.existing_id == d["id"]
            continue
        raise AssertionError(f"duplicate accepted: {variant!r}")


def test_review_workflow():
    recs, _ = qs.list_questions(status="draft", limit=200, offset=0)
    qid = recs[0]["id"]
    doc = qs.review_question(qid, "approve", "looks good")
    assert doc["status"] == "active", doc
    # approving again is invalid
    try:
        qs.review_question(qid, "approve")
    except QuestionValidationError:
        pass
    else:
        raise AssertionError("double approve allowed")
    # editing active text demotes to pending_review
    doc2 = qs.update_question(qid, {"text": "How do you handle five patients needing you at once?"})
    assert doc2["status"] == "pending_review", doc2
    assert "re-review" in (doc2["review_note"] or ""), doc2
    # non-material edit keeps status
    qs.review_question(qid, "approve")
    doc3 = qs.update_question(qid, {"expected_concepts": ["triage", "teamwork"]})
    assert doc3["status"] == "active", doc3
    # archive then edit blocked
    qs.review_question(qid, "archive")
    try:
        qs.update_question(qid, {"text": "Something else entirely new here?"})
    except QuestionValidationError:
        pass
    else:
        raise AssertionError("editing archived allowed")


def test_find_active_filters():
    # only active records served; domain allowlist respected
    qs.create_question(topic="Sales", difficulty=2,
                       text="How do you build long-term trust with a client?",
                       domain="Sales", status="active", source="manual")
    got = qs.find_active("sales", 2, [], ["Sales"], set())
    assert got and got["topic"] == "Sales", got
    got_none = qs.find_active("sales", 2, [], ["Nursing"], set())
    assert got_none is None or got_none["topic"] == "Nursing", got_none
    # drafts never served
    qs.create_question(topic="Nursing", difficulty=2,
                       text="What does patient-centered care mean to you in practice?",
                       domain="Nursing", status="draft", source="manual")
    served, total = qs.list_questions(status="active", limit=200, offset=0)
    assert all(r["status"] == "active" for r in served)


def test_interviewer_prefers_curated():
    from agents import interviewer

    hist = [{"question_id": "hr_tell_me_about_yourself", "question_text": "Tell me about yourself."}]
    profile = {"required_skills": ["cold calling"], "skill_gaps": ["objection handling"],
               "candidate_skills": ["prospecting"]}
    q = interviewer.generate_next_question(profile, hist, 2, domain="Sales", round_name="domain")
    assert q["topic"] == "Sales", q  # came from curated store, not LLM/bank
    assert interviewer.question_hash(q["text"]) not in interviewer.asked_hashes(hist)


def test_seed_idempotent():
    r1 = qs.seed_from_static_bank(created_by="test")
    r2 = qs.seed_from_static_bank(created_by="test")
    assert r1["imported"] > 0, r1
    assert r2["imported"] == 0 and r2["skipped_duplicates"] >= r1["imported"], (r1, r2)


try:
    # start from a clean slate for deterministic assertions
    if os.path.exists(LOCAL_FILE):
        os.remove(LOCAL_FILE)
    check("validation", test_validation)
    check("create+dedup", test_create_and_dedup)
    check("review-workflow", test_review_workflow)
    check("find-active-filters", test_find_active_filters)
    check("interviewer-prefers-curated", test_interviewer_prefers_curated)
    check("seed-idempotent", test_seed_idempotent)
    print(f"ALL {len(passed)} CURATION CHECKS PASSED")
finally:
    if os.path.exists(LOCAL_FILE):
        os.remove(LOCAL_FILE)
    if os.path.exists(BACKUP):
        shutil.move(BACKUP, LOCAL_FILE)
