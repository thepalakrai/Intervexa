MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 5

# Per-round Q&A question quotas.
# Coding problems are tracked separately and do NOT count toward these totals.
ROUND_QUOTAS: dict[str, int] = {
    "intro": 1,
    "domain": 4,
    "hr": 3,
}

# How many coding problems are shown per session before advancing to HR.
CODING_PROBLEM_QUOTA = 2

# Total Q&A questions (sum of all round quotas, for backward-compat callers).
TOTAL_QUESTIONS = sum(ROUND_QUOTAS.values())  # 8


def next_difficulty(current_difficulty: int, decision: str) -> int:
    """
    Rule-based on top of the evaluator's decision, rather than purely LLM-driven -
    keeps the difficulty engine predictable and demoable.
    """
    if decision == "increase_difficulty":
        new_difficulty = current_difficulty + 1
    elif decision == "decrease_difficulty":
        new_difficulty = current_difficulty - 1
    else:
        # "same" or "follow_up" - hold steady
        new_difficulty = current_difficulty

    return max(MIN_DIFFICULTY, min(MAX_DIFFICULTY, new_difficulty))


def questions_answered_in_round(history: list[dict], round_name: str) -> int:
    """Count how many Q&A answers belong to a specific round.

    Coding submissions (question_id starts with 'cp_') are excluded because
    they are tracked separately and do not count toward Q&A quotas.
    """
    return sum(
        1 for h in history
        if h.get("round") == round_name
        and not (h.get("question_id") or "").startswith("cp_")
    )


def is_round_complete(history: list[dict], round_name: str) -> bool:
    """True when the answered count for *round_name* meets its quota."""
    quota = ROUND_QUOTAS.get(round_name, 0)
    return questions_answered_in_round(history, round_name) >= quota


def is_interview_complete(history: list[dict], current_round: str = "hr") -> bool:
    """True only after the HR round quota is fully satisfied.

    Falls back to the old len-based check for sessions that pre-date the
    round-aware history tagging (backward compatibility).
    """
    # New-style: check hr quota explicitly
    if any(h.get("round") for h in history):
        return current_round == "hr" and is_round_complete(history, "hr")
    # Legacy fallback
    return len(history) >= TOTAL_QUESTIONS
