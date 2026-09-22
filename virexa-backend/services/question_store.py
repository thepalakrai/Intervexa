"""Curated question bank store (production curation layer).

Every question served in an interview should come from a reviewed,
domain-tagged record — not from an unversioned Python list or an
unconstrained LLM call. This module owns that layer:

- **Schema + validation**: topic allowlist, difficulty 1-5, text length
  bounds, expected_concepts hygiene, known-domain check.
- **Dedup**: normalized-text SHA-256 hash; creating a duplicate of any
  live (non-rejected, non-archived) record is a 409-style error.
- **Review workflow**: ``draft -> pending_review -> active``,
  with ``rejected`` and ``archived`` as terminal-ish states.
  Only ``active`` records are served in interviews. Editing the
  text/topic/difficulty of an ``active`` record demotes it back to
  ``pending_review`` so no unreviewed edit ever goes live silently.
- **Backends**: Cosmos DB ``questions`` container when configured,
  otherwise a local JSON file (``data/questions_curated.json``).
  Same interface either way, so local dev and tests work with zero infra.

Document shape (Cosmos partition key = ``topic``)::

    {
      "id": "q_<16 hex chars of hash>",
      "topic": "Nursing",
      "domain": "Nursing",
      "difficulty": 2,
      "text": "...",
      "expected_concepts": ["..."],
      "status": "active",
      "source": "manual | generated | imported",
      "question_hash": "<sha256 of normalized text>",
      "created_by": "admin@example.com",
      "created_at": "iso",
      "updated_at": "iso",
      "review_note": "...",
    }
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone

STATUSES = ("draft", "pending_review", "active", "rejected", "archived")
SOURCES = ("manual", "generated", "imported")

# States that block a same-text create (dedup scope).
DEDUP_BLOCKING_STATUSES = ("draft", "pending_review", "active")

MIN_TEXT_LEN = 12
MAX_TEXT_LEN = 1000
MAX_CONCEPTS = 12

LOCAL_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "questions_curated.json")


class QuestionValidationError(ValueError):
    """Raised for any schema/validation failure (mapped to HTTP 422)."""


class DuplicateQuestionError(ValueError):
    """Raised when the text duplicates a live record (mapped to HTTP 409)."""

    def __init__(self, message: str, existing_id: str | None = None):
        super().__init__(message)
        self.existing_id = existing_id


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9 ]", "", (text or "").lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def text_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def stable_id(topic: str, text: str) -> str:
    return "q_" + hashlib.sha256(f"{topic}::{normalize_text(text)}".encode("utf-8")).hexdigest()[:16]


def valid_topics() -> list[str]:
    """Allowlist = static bank topics + interviewer domain-topic table."""
    topics: set[str] = set()
    try:
        from data import question_bank

        for q in question_bank.QUESTIONS:
            if q.get("topic"):
                topics.add(q["topic"])
    except Exception:
        pass
    try:
        from agents.interviewer import DOMAIN_TOPICS

        for _domain, ts in DOMAIN_TOPICS.items():
            topics.update(ts)
    except Exception:
        pass
    topics.update(["HR", "Project", "General"])
    return sorted(topics)


def valid_domains() -> list[str]:
    domains: set[str] = set()
    try:
        from agents import role_config

        domains.update(role_config.DOMAIN_KEYWORDS.values())
    except Exception:
        pass
    domains.update(["General", "Python", "Data Analysis", "Java", "SQL"])
    return sorted(domains)


def validate_question(
    topic: str,
    difficulty: int,
    text: str,
    expected_concepts: list[str] | None = None,
    domain: str | None = None,
    status: str = "draft",
    source: str = "manual",
) -> dict:
    """Validate fields; returns cleaned values or raises QuestionValidationError."""
    if topic not in valid_topics():
        raise QuestionValidationError(
            f"Unknown topic '{topic}'. Valid topics: {', '.join(valid_topics())}"
        )
    if not isinstance(difficulty, int) or not 1 <= difficulty <= 5:
        raise QuestionValidationError("difficulty must be an integer 1-5.")
    cleaned_text = (text or "").strip()
    if not MIN_TEXT_LEN <= len(cleaned_text) <= MAX_TEXT_LEN:
        raise QuestionValidationError(
            f"text must be {MIN_TEXT_LEN}-{MAX_TEXT_LEN} characters (got {len(cleaned_text)})."
        )
    concepts = list(expected_concepts or [])
    if len(concepts) > MAX_CONCEPTS:
        raise QuestionValidationError(f"At most {MAX_CONCEPTS} expected_concepts.")
    concepts = [c.strip() for c in concepts if c and c.strip()]
    if domain is not None and domain not in valid_domains():
        raise QuestionValidationError(
            f"Unknown domain '{domain}'. Valid domains: {', '.join(valid_domains())}"
        )
    if status not in STATUSES:
        raise QuestionValidationError(f"status must be one of {STATUSES}.")
    if source not in SOURCES:
        raise QuestionValidationError(f"source must be one of {SOURCES}.")
    return {
        "topic": topic,
        "difficulty": difficulty,
        "text": cleaned_text,
        "expected_concepts": concepts,
        "domain": domain,
        "status": status,
        "source": source,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

def _cosmos_available() -> bool:
    return bool(os.getenv("COSMOS_ENDPOINT") and os.getenv("COSMOS_KEY"))


def _read_local() -> list[dict]:
    try:
        with open(LOCAL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _write_local(records: list[dict]) -> None:
    os.makedirs(os.path.dirname(LOCAL_FILE), exist_ok=True)
    with open(LOCAL_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def _list_all() -> tuple[list[dict], bool]:
    """Returns (records, using_cosmos). Falls back to local on any Cosmos error."""
    if _cosmos_available():
        try:
            from services import cosmos

            container = cosmos.get_questions_container()
            return list(container.read_all_items()), True
        except Exception as e:
            print(f"[question_store] Cosmos unavailable, using local file: {e}")
    return _read_local(), False


def _persist(records: list[dict], using_cosmos: bool) -> None:
    if not using_cosmos:
        _write_local(records)


def list_questions(
    topic: str | None = None,
    domain: str | None = None,
    difficulty: int | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Filtered + paginated list. Returns (page_items, total)."""
    records, _ = _list_all()
    if topic:
        records = [r for r in records if r.get("topic") == topic]
    if domain:
        records = [r for r in records if r.get("domain") == domain]
    if difficulty is not None:
        records = [r for r in records if r.get("difficulty") == difficulty]
    if status:
        records = [r for r in records if r.get("status") == status]
    if q:
        needle = q.lower()
        records = [
            r for r in records
            if needle in r.get("text", "").lower()
            or any(needle in c.lower() for c in r.get("expected_concepts", []))
        ]
    records.sort(key=lambda r: (r.get("topic", ""), r.get("difficulty", 0), r.get("created_at", "")))
    total = len(records)
    return records[offset:offset + max(1, limit)], total


def get_question(question_id: str) -> dict | None:
    records, _ = _list_all()
    for r in records:
        if r.get("id") == question_id:
            return r
    return None


def _find_by_hash(qhash: str, records: list[dict]) -> dict | None:
    for r in records:
        if r.get("question_hash") == qhash and r.get("status") in DEDUP_BLOCKING_STATUSES:
            return r
    return None


def create_question(
    topic: str,
    difficulty: int,
    text: str,
    expected_concepts: list[str] | None = None,
    domain: str | None = None,
    status: str = "draft",
    source: str = "manual",
    created_by: str | None = None,
) -> dict:
    cleaned = validate_question(topic, difficulty, text, expected_concepts, domain, status, source)
    records, using_cosmos = _list_all()
    qhash = text_hash(cleaned["text"])
    dup = _find_by_hash(qhash, records)
    if dup:
        raise DuplicateQuestionError(
            f"Duplicate of existing {dup['status']} question '{dup['id']}'.", existing_id=dup["id"]
        )
    now = _now()
    doc = {
        "id": stable_id(cleaned["topic"], cleaned["text"]),
        **cleaned,
        "question_hash": qhash,
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
        "review_note": None,
    }
    if any(r.get("id") == doc["id"] for r in records):
        # Same id can only happen for same topic+hash, already checked above;
        # guard against a rejected/archived twin being resurrected silently.
        raise DuplicateQuestionError(
            f"A record with id '{doc['id']}' already exists.", existing_id=doc["id"]
        )
    if using_cosmos:
        from services import cosmos

        cosmos.get_questions_container().create_item(body=doc)
    else:
        records.append(doc)
        _write_local(records)
    return doc


def update_question(question_id: str, patch: dict) -> dict | None:
    """Edit a record. Changing text/topic/difficulty on an active record
    demotes it to pending_review (must be re-approved before serving)."""
    records, using_cosmos = _list_all()
    for i, r in enumerate(records):
        if r.get("id") != question_id:
            continue
        if r.get("status") == "archived":
            raise QuestionValidationError("Archived questions cannot be edited. Create a new one.")
        new_topic = patch.get("topic", r["topic"])
        new_diff = patch.get("difficulty", r["difficulty"])
        new_text = patch.get("text", r["text"])
        new_concepts = patch.get("expected_concepts", r.get("expected_concepts", []))
        new_domain = patch.get("domain", r.get("domain"))
        validate_question(new_topic, new_diff, new_text, new_concepts, new_domain,
                          r["status"], r.get("source", "manual"))
        new_hash = text_hash(new_text.strip())
        if new_hash != r.get("question_hash"):
            dup = _find_by_hash(new_hash, [x for x in records if x.get("id") != question_id])
            if dup:
                raise DuplicateQuestionError(
                    f"Edit would duplicate {dup['status']} question '{dup['id']}'.",
                    existing_id=dup["id"],
                )
        material_change = (
            new_text.strip() != r["text"] or new_topic != r["topic"] or new_diff != r["difficulty"]
        )
        r.update({
            "topic": new_topic,
            "difficulty": new_diff,
            "text": new_text.strip(),
            "expected_concepts": [c.strip() for c in (new_concepts or []) if c and c.strip()],
            "domain": new_domain,
            "question_hash": new_hash,
            "updated_at": _now(),
        })
        if material_change and r["status"] == "active":
            r["status"] = "pending_review"
            r["review_note"] = "Auto-demoted: content edited after approval; re-review required."
        if using_cosmos:
            from services import cosmos

            cosmos.get_questions_container().upsert_item(body=r)
        else:
            records[i] = r
            _write_local(records)
        return r
    return None


# action -> (allowed_from, to_status)
REVIEW_TRANSITIONS = {
    "submit": (("draft", "rejected"), "pending_review"),
    "approve": (("draft", "pending_review", "rejected"), "active"),
    "reject": (("draft", "pending_review", "active"), "rejected"),
    "archive": (("draft", "pending_review", "active", "rejected"), "archived"),
}


def review_question(question_id: str, action: str, note: str | None = None) -> dict | None:
    if action not in REVIEW_TRANSITIONS:
        raise QuestionValidationError(
            f"Unknown review action '{action}'. Use one of {sorted(REVIEW_TRANSITIONS)}."
        )
    allowed_from, to_status = REVIEW_TRANSITIONS[action]
    records, using_cosmos = _list_all()
    for i, r in enumerate(records):
        if r.get("id") != question_id:
            continue
        if r.get("status") not in allowed_from:
            raise QuestionValidationError(
                f"Cannot '{action}' a question with status '{r.get('status')}'."
            )
        r["status"] = to_status
        r["review_note"] = (note or "").strip() or None
        r["updated_at"] = _now()
        if using_cosmos:
            from services import cosmos

            cosmos.get_questions_container().upsert_item(body=r)
        else:
            records[i] = r
            _write_local(records)
        return r
    return None


def delete_question(question_id: str, hard: bool = False) -> bool:
    """Soft-delete (archive) by default; hard=True removes the record."""
    records, using_cosmos = _list_all()
    for i, r in enumerate(records):
        if r.get("id") != question_id:
            continue
        if hard:
            if using_cosmos:
                from services import cosmos

                cosmos.get_questions_container().delete_item(item=question_id, partition_key=r["topic"])
            else:
                records.pop(i)
                _write_local(records)
        else:
            review_question(question_id, "archive")
        return True
    return False


def find_active(
    topic_hint: str,
    difficulty: int,
    exclude_ids: list[str] | None = None,
    allowed_topics: list[str] | None = None,
    exclude_text_hashes: set[str] | None = None,
) -> dict | None:
    """Retrieval for the interview loop: active records only, same
    contract as search.find_question_local (id/topic/difficulty/text)."""
    records, _ = _list_all()
    exclude_ids = set(exclude_ids or [])
    exclude_text_hashes = exclude_text_hashes or set()
    hint = (topic_hint or "").lower()
    candidates = []
    for order, r in enumerate(records):
        if r.get("status") != "active":
            continue
        if r.get("id") in exclude_ids:
            continue
        if r.get("question_hash") in exclude_text_hashes:
            continue
        if allowed_topics and r.get("topic") not in allowed_topics:
            continue
        if abs(int(r.get("difficulty", 3)) - difficulty) > 1:
            continue
        topic_lower = str(r.get("topic", "")).lower()
        score = 0
        if hint and (hint in topic_lower or topic_lower in hint):
            score = 2
        elif hint and any(w in topic_lower for w in hint.split() if len(w) > 3):
            score = 1
        candidates.append((score, abs(int(r.get("difficulty", 3)) - difficulty), order, r))
    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c[0], c[1], c[2]))
    best = candidates[0][3]
    return {"id": best["id"], "topic": best["topic"],
            "difficulty": best["difficulty"], "text": best["text"]}


def seed_from_static_bank(created_by: str | None = None) -> dict:
    """One-time migration: import data/question_bank.py as active records.
    Idempotent — existing hashes are skipped, never duplicated."""
    from data import question_bank

    try:
        from agents.interviewer import DOMAIN_TOPICS

        topic_to_domain = {}
        for _domain, ts in DOMAIN_TOPICS.items():
            for t in ts:
                topic_to_domain.setdefault(t, _domain)
    except Exception:
        topic_to_domain = {}

    imported, skipped, errors = 0, 0, []
    for i, q in enumerate(question_bank.QUESTIONS):
        try:
            create_question(
                topic=q["topic"],
                difficulty=int(q["difficulty"]),
                text=q["text"],
                expected_concepts=q.get("expected_concepts", []),
                domain=topic_to_domain.get(q["topic"]),
                status="active",
                source="imported",
                created_by=created_by or "seed",
            )
            imported += 1
        except DuplicateQuestionError:
            skipped += 1
        except Exception as e:  # validation etc. — report, don't abort
            errors.append({"index": i, "error": str(e)})
    return {"imported": imported, "skipped_duplicates": skipped, "errors": errors}
