"""
Wipes the Azure AI Search question-bank index and re-uploads ONLY the
questions currently in question_bank.py.

Why this exists: the live index has stale documents left over from an
earlier version of the question bank that phrased HR questions per-role
(e.g. "Why do you want to work as a Data Analyst?"). Nothing in the
schema filters by role - only topic + difficulty - so those old docs
still surface for candidates of ANY role whenever "HR" is searched.
question_bank.py itself is clean (no role names anywhere in it) - the
index just doesn't reflect that yet. This script fixes the index to
match the file, rather than changing any matching/search logic.

Usage:
    pip install requests --break-system-packages
    python reindex_questions.py
Requires the same env vars search.py already uses:
    AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, AZURE_SEARCH_INDEX (optional)
"""
import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()  # picks up the same .env your backend uses (walks up from this file's folder)

from question_bank import QUESTIONS

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "virexa-question-bank")
API_VERSION = "2023-11-01"

if not SEARCH_ENDPOINT or not SEARCH_KEY:
    raise SystemExit(
        "AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_KEY not set. "
        "Run this with the same .env your backend uses."
    )

BASE_URL = f"{SEARCH_ENDPOINT.rstrip('/')}/indexes/{SEARCH_INDEX}/docs"
HEADERS = {"api-key": SEARCH_KEY, "Content-Type": "application/json"}


def _chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def fetch_all_ids() -> list[str]:
    """Pages through the index with search=* to collect every existing doc id."""
    ids = []
    skip = 0
    page_size = 1000
    while True:
        body = {"search": "*", "top": page_size, "skip": skip, "select": "id"}
        resp = requests.post(
            f"{BASE_URL}/search?api-version={API_VERSION}",
            headers=HEADERS, json=body, timeout=30,
        )
        resp.raise_for_status()
        page = resp.json().get("value", [])
        if not page:
            break
        ids.extend(d["id"] for d in page)
        if len(page) < page_size:
            break
        skip += page_size
    return ids


def delete_all(ids: list[str]):
    if not ids:
        print("Index already empty - nothing to delete.")
        return
    for batch in _chunks(ids, 500):
        actions = [{"@search.action": "delete", "id": doc_id} for doc_id in batch]
        resp = requests.post(
            f"{BASE_URL}/index?api-version={API_VERSION}",
            headers=HEADERS, json={"value": actions}, timeout=30,
        )
        resp.raise_for_status()
    print(f"Deleted {len(ids)} stale document(s) from the index.")


def upload_current_questions():
    actions = []
    for q in QUESTIONS:
        doc = dict(q)
        doc["id"] = str(uuid.uuid4())
        doc["@search.action"] = "upload"
        actions.append(doc)

    for batch in _chunks(actions, 500):
        resp = requests.post(
            f"{BASE_URL}/index?api-version={API_VERSION}",
            headers=HEADERS, json={"value": batch}, timeout=30,
        )
        resp.raise_for_status()
    print(f"Uploaded {len(actions)} question(s) from the current question_bank.py.")


if __name__ == "__main__":
    print(f"Reindexing '{SEARCH_INDEX}' at {SEARCH_ENDPOINT} ...")
    existing_ids = fetch_all_ids()
    print(f"Found {len(existing_ids)} existing document(s) in the index.")
    delete_all(existing_ids)
    upload_current_questions()
    print("Done. The index now matches question_bank.py exactly - no stale role-specific questions left.")
