import hashlib
import json
import re
import uuid
from services import foundry, search

OPENING_QUESTION_ID = "hr_tell_me_about_yourself"
OPENING_QUESTION_TEXT = "Tell me about yourself."

# bank topic -> coarse domain mapping lives in role_config; the reverse
# (domain -> allowed bank topics) is defined here so the interviewer can
# enforce domain filtering without importing heavy deps.
DOMAIN_TOPICS: dict[str, list[str]] = {
    "Nursing": ["Nursing"],
    "Finance": ["Finance"],
    "Mechanical Engineering": ["Mechanical Engineering"],
    "Civil Engineering": ["Civil Engineering"],
    "Electrical Engineering": ["Electrical Engineering"],
    "Teaching": ["Teaching"],
    "Aviation": ["Aviation"],
    "HR Recruitment": ["HR Recruitment"],
    "Customer Service": ["Customer Service"],
    "Marketing": ["Marketing"],
    "Sales": ["Sales"],
    "Hospitality": ["Hospitality"],
    "Legal": ["Legal"],
    "Retail Operations": ["Retail Operations"],
    "SQL": ["SQL", "DBMS"],
    "Python": ["Python", "DSA"],
    "Data Analysis": ["Data Analysis", "SQL", "Python"],
    "Java": ["Java", "DSA"],
    "General": ["HR", "Project"],
}

SYSTEM_PROMPT = """You are Virexa AI, an adaptive technical interviewer.

You are given:
- A candidate profile (skills, skill gaps, experience level)
- The interview history so far (questions asked, answers given, evaluations)
- A target difficulty level (1=Beginner, 2=Easy, 3=Medium, 4=Hard, 5=Expert)
- The current_round and allowed_topics fields — you MUST stay within them

Your job: generate the SINGLE next interview question.

Rules:
- Ask ONE question at a time. Never ask multiple questions in one turn.
- Match the question to the target difficulty level.
- CRITICAL: If allowed_topics is provided, you MUST only ask about topics in that list.
  For the "hr" round, allowed_topics will be ["HR", "HR Recruitment", "Project"] —
  do NOT ask technical questions (no SQL, Python, coding, algorithms, etc.).
  HR round questions must be behavioural, situational, or about the candidate's
  background, goals, teamwork, strengths/weaknesses, and career motivations.
- If the previous answer was weak, you may ask a simpler follow-up on the SAME topic.
- If the previous answer was strong, you may go deeper on the same topic or move to
  a related allowed topic.
- Never repeat a question already in the history.

Respond ONLY with a JSON object, no prose, no markdown fences:
{
  "topic": "short topic label, e.g. 'HR' or 'Project'",
  "text": "the actual question text to show the candidate"
}
"""


def normalize_question(text: str) -> str:
    """Lowercase, strip punctuation/extra spaces - for repeat detection."""
    cleaned = re.sub(r"[^a-z0-9 ]", "", (text or "").lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def question_hash(text: str) -> str:
    return hashlib.sha256(normalize_question(text).encode("utf-8")).hexdigest()


def asked_hashes(history: list[dict]) -> set[str]:
    return {question_hash(h.get("question_text", "")) for h in history if h.get("question_text")}


def allowed_topics_for_domain(domain: str | None, round_name: str) -> list[str] | None:
    """Domain filter (Phase 2).

    - intro round: opener only, handled by caller.
    - hr round: HR + Project topics only (never domain-technical).
    - domain round: only the session domain's topics (+Project resume
      questions, which are domain-agnostic) - never HR openers.
    Returns None when no domain is known (legacy sessions): no filtering.
    """
    if not domain:
        return None
    if round_name == "hr":
        return ["HR", "HR Recruitment", "Project"]
    if round_name == "domain":
        topics = list(DOMAIN_TOPICS.get(domain, []))
        if "Project" not in topics:
            topics.append("Project")
        # The intro opener must never reappear as a domain question.
        return topics
    return None


def _pick_topic_hint(profile: dict, history: list[dict], round_name: str = "domain") -> str:
    """
    Picks which topic to search for next - favors skill_gaps/required_skills
    that have come up least often so far in this session.

    For the HR round, always returns "HR" so the bank search stays on-topic.
    """
    if round_name == "hr":
        return "HR"

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


def generate_next_question(
    profile: dict,
    history: list[dict],
    difficulty: int,
    domain: str | None = None,
    round_name: str = "domain",
) -> dict:
    """
    Bank-first with domain filter + dedup (Phase 2), LLM fallback last.

    0. Curated store (active, reviewed records) - highest trust.
    1. Azure AI Search bank / local static bank, restricted to
       ``allowed_topics_for_domain`` and excluding asked IDs *and*
       normalized-text hashes (so "Tell me about yourself."
       can never reappear after the opener).
    2. Fall back to the LLM only when the bank is exhausted; the LLM
       prompt includes the asked questions + domain so it does not
       repeat or drift domains. Its output is hash-checked with one
       retry before acceptance.
    """
    already_asked_ids = [h.get("question_id") for h in history if h.get("question_id")]
    seen_hashes = asked_hashes(history)
    topic_hint = _pick_topic_hint(profile, history, round_name)
    allowed = allowed_topics_for_domain(domain, round_name)

    # For HR round, always use a domain value so allowed_topics is populated.
    if round_name == "hr" and not domain:
        domain = "General"

    try:
        from services import question_store

        curated = question_store.find_active(
            topic_hint, difficulty, already_asked_ids, allowed, seen_hashes
        )
        if curated:
            return curated
    except Exception as e:
        print(f"[interviewer] curated store lookup failed, continuing: {e}")

    bank_question = search.find_question(topic_hint, difficulty, already_asked_ids)
    if bank_question and question_hash(bank_question.get("text", "")) not in seen_hashes:
        if allowed is None or bank_question.get("topic") in allowed:
            return bank_question

    local = search.find_question_local(
        topic_hint, difficulty, already_asked_ids, allowed, seen_hashes
    )
    if local:
        return local

    # Fallback: nothing suitable in the bank, ask the LLM to invent one
    asked_texts = [h.get("question_text", "") for h in history if h.get("question_text")]
    user_message = json.dumps({
        "candidate_profile": profile,
        "interview_history": history,
        "target_difficulty": difficulty,
        "domain": domain,
        "current_round": round_name,
        "allowed_topics": allowed,
        "already_asked_questions": asked_texts,
        "constraint": (
            "Do NOT repeat any already-asked question (including rephrasings of "
            "'Tell me about yourself'). Stay within allowed_topics for this round."
        ),
    })

    for _ in range(2):  # one retry if the LLM repeats itself
        raw = foundry.chat(SYSTEM_PROMPT, user_message, json_mode=True)
        parsed = json.loads(raw)
        text = (parsed.get("text") or "").strip()
        if text and question_hash(text) not in seen_hashes:
            return {
                "id": str(uuid.uuid4()),
                "topic": parsed.get("topic", "General"),
                "difficulty": difficulty,
                "text": text,
            }
        user_message += '\nRETRY: that question was already asked. Ask a DIFFERENT question.'

    return {
        "id": str(uuid.uuid4()),
        "topic": parsed.get("topic", "General"),
        "difficulty": difficulty,
        "text": parsed.get("text", ""),
    }


def generate_opening_question(profile: dict) -> dict:
    """
    Fixed HR opener with a STABLE id (was a random uuid, which defeated
    the bank's exclude-by-id dedup and let "Tell me about yourself."
    reappear mid-interview).
    """
    return {
        "id": OPENING_QUESTION_ID,
        "topic": "HR",
        "difficulty": 2,
        "text": OPENING_QUESTION_TEXT,
    }
