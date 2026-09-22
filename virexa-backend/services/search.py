import os
import requests

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "virexa-question-bank")


def _headers():
    return {"api-key": SEARCH_KEY, "Content-Type": "application/json"}


def find_question(topic_hint: str, difficulty: int, exclude_ids: list[str]) -> dict | None:
    """
    Looks up a question from the bank matching a topic hint and difficulty
    (+/- 1 tolerance), excluding any question already asked this session.
    Returns None if nothing suitable is found - the caller should fall back
    to generating a question with the LLM in that case.
    """
    if not SEARCH_ENDPOINT or not SEARCH_KEY:
        return find_question_local(
            topic_hint, difficulty, exclude_ids, allowed_topics=None,
            exclude_text_hashes=None,
        )

    url = f"{SEARCH_ENDPOINT.rstrip('/')}/indexes/{SEARCH_INDEX}/docs/search?api-version=2023-11-01"

    # Filter to a difficulty band around the target, and exclude used questions
    filter_parts = [f"difficulty ge {max(1, difficulty - 1)}", f"difficulty le {min(5, difficulty + 1)}"]
    for qid in exclude_ids:
        filter_parts.append(f"id ne '{qid}'")
    filter_str = " and ".join(filter_parts)

    body = {
        "search": topic_hint,
        "filter": filter_str,
        "top": 5,
        "queryType": "simple",
    }

    response = requests.post(url, headers=_headers(), json=body, timeout=30)
    if response.status_code != 200:
        return None

    results = response.json().get("value", [])
    if not results:
        return None

    # Take the top match (Azure Search already ranks by relevance to topic_hint)
    top = results[0]
    return {
        "id": top["id"],
        "topic": top["topic"],
        "difficulty": top["difficulty"],
        "text": top["text"],
    }


def find_question_local(
    topic_hint: str,
    difficulty: int,
    exclude_ids: list[str] | None = None,
    allowed_topics: list[str] | None = None,
    exclude_text_hashes: set[str] | None = None,
) -> dict | None:
    """Local fallback over ``data.question_bank.QUESTIONS``.

    Used when Azure AI Search is not configured (local dev) and as a
    domain-filtered first pass even when it is. Enforces:

    - difficulty within +/- 1 of target
    - ``id`` not in ``exclude_ids``
    - normalized text hash not in ``exclude_text_hashes`` (dedup, Phase 2)
    - topic in ``allowed_topics`` when given (domain filter, Phase 2)
    """
    from data import question_bank

    exclude_ids = set(exclude_ids or [])
    exclude_text_hashes = exclude_text_hashes or set()
    hint = (topic_hint or "").lower()

    def _norm(text: str) -> str:
        import hashlib
        import re

        cleaned = re.sub(r"[^a-z0-9 ]", "", (text or "").lower()).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    candidates = []
    for i, q in enumerate(question_bank.QUESTIONS):
        qid = q.get("id") or f"bank_{i}"
        if qid in exclude_ids:
            continue
        if _norm(q.get("text", "")) in exclude_text_hashes:
            continue
        if allowed_topics and q.get("topic") not in allowed_topics:
            continue
        if abs(int(q.get("difficulty", 3)) - difficulty) > 1:
            continue
        topic_lower = str(q.get("topic", "")).lower()
        score = 0
        if hint and (hint in topic_lower or topic_lower in hint):
            score = 2
        elif hint and any(w in topic_lower for w in hint.split() if len(w) > 3):
            score = 1
        candidates.append((score, abs(int(q.get("difficulty", 3)) - difficulty), i, q, qid))

    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c[0], c[1], c[2]))
    _, _, _, best, best_id = candidates[0]
    return {
        "id": best_id,
        "topic": best.get("topic", "General"),
        "difficulty": best.get("difficulty", difficulty),
        "text": best.get("text", ""),
    }
