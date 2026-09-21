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
        return None

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
