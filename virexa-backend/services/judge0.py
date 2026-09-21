"""
Code execution via Judge0's public Community Edition instance.
No API key required for this free instance - good enough for a demo,
but expect occasional slowness/rate limits since it's a shared public
resource. If it becomes unreliable close to your demo, the RapidAPI
Judge0 tier (with a key) is a drop-in swap - just change JUDGE0_URL
and add the RapidAPI headers.
"""
import requests

JUDGE0_URL = "https://ce.judge0.com/submissions"

# Common Judge0 language IDs - Python 3 is the default for Day 4's coding round
LANGUAGE_IDS = {
    "python": 71,
    "java": 62,
    "cpp": 54,
    "javascript": 63,
}


def run_code(source_code: str, stdin: str, language: str = "python") -> dict:
    """
    Submits code to Judge0, waits for the result (synchronous), and
    returns {stdout, stderr, status, compile_output}.
    """
    language_id = LANGUAGE_IDS.get(language, 71)

    params = {
        "base64_encoded": "false",
        "wait": "true",  # synchronous - waits for execution to finish before responding
    }
    body = {
        "source_code": source_code,
        "language_id": language_id,
        "stdin": stdin,
    }

    response = requests.post(JUDGE0_URL, params=params, json=body, timeout=30)
    response.raise_for_status()
    data = response.json()

    return {
        "stdout": (data.get("stdout") or "").strip(),
        "stderr": (data.get("stderr") or "").strip(),
        "compile_output": (data.get("compile_output") or "").strip(),
        "status": data.get("status", {}).get("description", "Unknown"),
    }


def judge_submission(source_code: str, test_cases: list[dict], language: str = "python") -> dict:
    """
    Runs source_code against every test case and returns a pass/fail
    breakdown plus an overall score out of 100.
    """
    results = []
    passed_count = 0

    for tc in test_cases:
        run_result = run_code(source_code, tc["stdin"], language)
        actual = run_result["stdout"]
        expected = tc["expected_stdout"].strip()
        passed = actual == expected

        if passed:
            passed_count += 1

        results.append({
            "stdin": tc["stdin"],
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "stderr": run_result["stderr"],
            "compile_output": run_result["compile_output"],
            "status": run_result["status"],
        })

    total = len(test_cases)
    score = round((passed_count / total) * 100) if total else 0

    return {
        "score": score,
        "passed": passed_count,
        "total": total,
        "test_results": results,
    }
