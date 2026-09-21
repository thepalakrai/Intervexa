import json
from services import foundry

SYSTEM_PROMPT = """You are an expert technical interview evaluator.

You are given one interview question and the candidate's spoken/typed answer.
Evaluate the answer honestly and strictly - do not be generous by default.

Score each of these from 0-100:
- technical_accuracy: is the content factually/technically correct?
- depth: does the answer go beyond a surface-level definition?
- communication: is the answer clearly structured and easy to follow?
- problem_solving: for scenario/coding questions, is the reasoning sound?
  (for pure definition/HR questions, score this the same as communication)
- confidence: does the phrasing suggest the candidate understands what they said,
  vs guessing?

Then compute:
- overall: a weighted average reflecting your judgment (not just a plain mean)
- decision: one of "increase_difficulty" (strong answer), "same" (adequate answer),
  "decrease_difficulty" (weak answer), "follow_up" (partially correct, worth probing
  deeper on the same topic before moving on)

Respond ONLY with a JSON object, no prose, no markdown fences:
{
  "technical_accuracy": 0,
  "depth": 0,
  "communication": 0,
  "problem_solving": 0,
  "confidence": 0,
  "overall": 0,
  "decision": "same"
}
"""


def evaluate_answer(question_text: str, answer_text: str) -> dict:
    user_message = json.dumps({
        "question": question_text,
        "answer": answer_text,
    })

    raw = foundry.chat(SYSTEM_PROMPT, user_message, json_mode=True)
    return json.loads(raw)
