import os
import json
import requests

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")  # e.g. https://virexa-budget.openai.azure.com/openai/v1
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")


def chat(system_prompt: str, user_message: str, json_mode: bool = False) -> str:
    """
    Sends a single-turn chat request directly via requests, bypassing the
    openai SDK entirely. This mirrors the exact call confirmed working via
    a manual PowerShell test against this same endpoint.
    """
    if not ENDPOINT or not API_KEY:
        raise RuntimeError(
            "AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY not set. Check your .env file."
        )

    url = f"{ENDPOINT.rstrip('/')}/chat/completions"

    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json",
    }

    body = {
        "model": DEPLOYMENT,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.4,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    response = requests.post(url, headers=headers, json=body, timeout=60)
    response.raise_for_status()  # raises a clear error with Azure's actual message if this fails

    data = response.json()
    return data["choices"][0]["message"]["content"]


def analyze_profile(resume_text: str, jd_text: str) -> dict:
    """
    Turns resume + JD text into a structured candidate profile with skill gaps.
    """
    system_prompt = (
        "You are a resume and job-description analyzer for an interview prep tool. "
        "Given a resume and a job description, respond ONLY with a JSON object with keys: "
        "candidate_skills (list of strings), required_skills (list of strings), "
        "skill_gaps (list of strings), experience_level (string, one of "
        "'entry-level', 'mid-level', 'senior'). No prose, no markdown fences, JSON only."
    )
    user_message = f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd_text}"

    raw = chat(system_prompt, user_message, json_mode=True)
    return json.loads(raw)
