MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 5

# How many questions the full interview asks before generating the final report.
# Kept small for a 5-day build - increase once the core loop is proven solid.
TOTAL_QUESTIONS = 8


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


def is_interview_complete(history: list[dict]) -> bool:
    return len(history) >= TOTAL_QUESTIONS
