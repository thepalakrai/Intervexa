import json
import uuid
from services import foundry, search

SYSTEM_PROMPT = """You are Virexa AI, an adaptive technical interviewer.

You are given:
- A candidate profile (skills, skill gaps, experience level)
- The interview history so far (questions asked, answers given, evaluations)
- A target difficulty level (1=Beginner, 2=Easy, 3=Medium, 4=Hard, 5=Expert)

Your job: generate the SINGLE next interview question.

Rules:
- Ask ONE question at a time. Never ask multiple questions in one turn.
- Match the question to the target difficulty level.
- Prioritize topics from the candidate's skill_gaps and required_skills.
- If the previous answer was weak, you may ask a simpler follow-up on the SAME topic
  instead of jumping to a new one (e.g. "Let's step back - can you explain X?").
- If the previous answer was strong, you may go deeper on the same topic or move to
  a new required skill.
- Vary between HR, resume/project, and technical topics rather than only technical.
- Never repeat a question already in the history.

Respond ONLY with a JSON object, no prose, no markdown fences:
{
  "topic": "short topic label, e.g. 'Java Collections' or 'HR'",
  "text": "the actual question text to show the candidate"
}
"""


def _pick_topic_hint(profile: dict, history: list[dict]) -> str:
    """
    Picks which topic to search for next - favors skill_gaps/required_skills
    that have come up least often so far in this session.
    """
    candidate_topics = list(profile.get("skill_gaps", [])) + list(profile.get("required_skills", []))
    if not candidate_topics:
        candidate_topics = ["Data Analysis", "SQL", "Python"]

    topic_counts = {t: 0 for t in candidate_topics}
    for h in history:
        asked_topic = h.get("question_text", "")
        for t in candidate_topics:
            if t.lower() in asked_topic.lower():
                topic_counts[t] += 1

    # topic asked least so far
    least_asked = min(topic_counts, key=topic_counts.get)
    return least_asked


def generate_next_question(profile: dict, history: list[dict], difficulty: int) -> dict:
    """
    First tries to pull a matching question from the Azure AI Search question
    bank (Day 3). Falls back to generating one with the LLM if nothing
    suitable is found in the bank - e.g. very high/low difficulty, or the
    bank's relevant questions for this topic are exhausted.
    """
    already_asked_ids = [h.get("question_id") for h in history if h.get("question_id")]
    topic_hint = _pick_topic_hint(profile, history)

    bank_question = search.find_question(topic_hint, difficulty, already_asked_ids)
    if bank_question:
        return bank_question

    # Fallback: nothing suitable in the bank, ask the LLM to invent one
    user_message = json.dumps({
        "candidate_profile": profile,
        "interview_history": history,
        "target_difficulty": difficulty,
    })

    raw = foundry.chat(SYSTEM_PROMPT, user_message, json_mode=True)
    parsed = json.loads(raw)

    return {
        "id": str(uuid.uuid4()),
        "topic": parsed.get("topic", "General"),
        "difficulty": difficulty,
        "text": parsed.get("text", ""),
    }


def generate_opening_question(profile: dict) -> dict:
    """
    Always starts with a fixed HR opener - keeps the demo predictable
    and avoids burning a model/search call on something that doesn't
    need adapting.
    """
    return {
        "id": str(uuid.uuid4()),
        "topic": "HR",
        "difficulty": 2,
        "text": "Tell me about yourself.",
    }
