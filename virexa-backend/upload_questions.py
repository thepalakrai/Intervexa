"""
Uploads the curated question bank (data/question_bank.py) into your
Azure AI Search index. Safe to re-run any time you add more questions -
IDs are generated deterministically from (topic + text), so re-uploading
the same question just overwrites it instead of creating a duplicate.

Run with:
    python upload_questions.py
"""
import os
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

from data.question_bank import QUESTIONS

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")  # e.g. https://virexa-search-palak.search.windows.net
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "virexa-question-bank")

if not SEARCH_ENDPOINT or not SEARCH_KEY:
    raise RuntimeError("AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_KEY not set. Check your .env file.")

url = f"{SEARCH_ENDPOINT.rstrip('/')}/indexes/{SEARCH_INDEX}/docs/index?api-version=2023-11-01"

headers = {
    "api-key": SEARCH_KEY,
    "Content-Type": "application/json",
}


def stable_id(topic: str, text: str) -> str:
    """Deterministic ID so re-uploading the same question is idempotent."""
    raw = f"{topic}::{text}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


documents = []
for q in QUESTIONS:
    documents.append({
        "@search.action": "upload",
        "id": stable_id(q["topic"], q["text"]),
        "topic": q["topic"],
        "difficulty": q["difficulty"],
        "text": q["text"],
        "expected_concepts": q["expected_concepts"],
    })

print(f"Uploading {len(documents)} questions to index '{SEARCH_INDEX}'...")

# Azure Search accepts up to 1000 docs per batch; we're well under that,
# but batching in chunks of 100 keeps each request small and reliable.
BATCH_SIZE = 100
total_failed = 0

for i in range(0, len(documents), BATCH_SIZE):
    batch = documents[i:i + BATCH_SIZE]
    response = requests.post(url, headers=headers, json={"value": batch}, timeout=60)

    if response.status_code in (200, 201):
        results = response.json().get("value", [])
        failed = [r for r in results if not r.get("status")]
        total_failed += len(failed)
        print(f"  Batch {i // BATCH_SIZE + 1}: {len(batch)} sent, {len(failed)} failed")
        if failed:
            print(failed)
    else:
        print(f"  Batch {i // BATCH_SIZE + 1} FAILED with status {response.status_code}")
        print(response.text)
        total_failed += len(batch)

if total_failed == 0:
    print(f"SUCCESS! All {len(documents)} questions uploaded.")
else:
    print(f"Done with {total_failed} failures - check the output above.")
