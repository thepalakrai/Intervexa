"""Role-based round engine (Phase 1).

Derives, from resume/JD text + analyzed profile, a deterministic
``round_plan`` stored on the interview session, e.g.::

    ["intro", "domain", "hr"]                     # non-technical
    ["intro", "domain", "coding", "hr"]            # technical

``next_round()`` is a pure index step over that plan — it replaces the
old implicit behaviour where the Q&A loop always ended in HR and the
coding round was reachable for every role via an always-visible button.
"""

from __future__ import annotations

# Keywords that mark a role as technical (coding round applies).
TECHNICAL_KEYWORDS = (
    "software", "backend", "frontend", "full-stack", "full stack",
    "developer", "engineer", "engineering", "data scientist",
    "machine learning", "ml engineer", "devops", "sde", "programmer",
    "python", "java", "javascript", "typescript", "coding",
)

# Job-title phrases that on their own mark a role technical. Bare
# "software" is deliberately excluded (SaaS sales JDs mention software),
# as are bare "engineer"/"engineering" (sales engineer, etc. — those need
# stack evidence, see has_technical_evidence).
TECH_TITLE_KEYWORDS = (
    "software engineer", "software developer", "backend", "frontend",
    "full-stack", "full stack", "developer", "data scientist",
    "machine learning", "ml engineer", "ai engineer", "devops",
    "sde", "programmer", "data engineer",
)

# Stack skills counted in the candidate/required/skill-gap lists. Two or
# more distinct hits mark a role technical even without a technical title
# (e.g. an "AI Specialist" whose skills are Python + SQL + PyTorch).
TECH_STACK_KEYWORDS = (
    "python", "java", "javascript", "typescript", "c++", "sql",
    "pytorch", "tensorflow", "dsa", "data structures", "algorithm",
    "machine learning", "deep learning", "data science", "coding",
    "rest api", "nlp",
)

ENGINEER_WORDS = ("engineer", "engineering")

# Non-technical domain fragments (lowercase substrings of JD + skills).
# Checked ONLY when no technical evidence exists, so incidental mentions
# (a health-tech JD saying "patient", a SaaS JD saying "software" or
# "accounts") can no longer hijack a technical role. Fragments were also
# hardened vs the old map: bare "account"/"bank"/"market" matched
# "account management", "riverbank", "stock/job market".
NONTECH_DOMAIN_KEYWORDS: dict[str, str] = {
    "nurs": "Nursing",
    "healthcare": "Nursing",
    "patient": "Nursing",
    "hospital": "Nursing",
    "clinic": "Nursing",
    "pharmacy": "Nursing",
    "financ": "Finance",
    "accountant": "Finance",
    "accounting": "Finance",
    "banking": "Finance",
    "audit": "Finance",
    "ledger": "Finance",
    "mechanical": "Mechanical Engineering",
    "civil": "Civil Engineering",
    "construction": "Civil Engineering",
    "electrical": "Electrical Engineering",
    "teacher": "Teaching",
    "teaching": "Teaching",
    "school": "Teaching",
    "curriculum": "Teaching",
    "education": "Teaching",
    "aviation": "Aviation",
    "pilot": "Aviation",
    "cabin crew": "Aviation",
    "airport": "Aviation",
    "recruit": "HR Recruitment",
    "human resources": "HR Recruitment",
    "customer service": "Customer Service",
    "support agent": "Customer Service",
    "call center": "Customer Service",
    "marketing": "Marketing",
    "sales": "Sales",
    "hospitality": "Hospitality",
    "hotel": "Hospitality",
    "restaurant": "Hospitality",
    "legal": "Legal",
    "lawyer": "Legal",
    "paralegal": "Legal",
    "retail": "Retail Operations",
}

# Kept for compatibility (question_store.valid_domains reads the values).
# Technical fragments retained so the bank's tech topics stay listed.
DOMAIN_KEYWORDS: dict[str, str] = {
    **NONTECH_DOMAIN_KEYWORDS,
    "sql": "SQL",
    "python": "Python",
    "data": "Data Analysis",
    "java": "Java",
    "algorithm": "DSA",
    "dsa": "DSA",
}

NON_TECHNICAL_DOMAINS = {
    "Nursing", "Finance", "Mechanical Engineering", "Civil Engineering",
    "Electrical Engineering", "Teaching", "Aviation", "HR Recruitment",
    "Customer Service", "Marketing", "Sales", "Hospitality", "Legal",
    "Retail Operations",
}


def _skills_text(profile: dict) -> str:
    return " ".join([
        " ".join(profile.get("candidate_skills", []) or []),
        " ".join(profile.get("required_skills", []) or []),
        " ".join(profile.get("skill_gaps", []) or []),
    ]).lower()


def has_technical_evidence(jd_text: str, profile: dict) -> bool:
    """True when the JD/skills clearly describe a technical role.

    Three independent signals (any one suffices): an explicit technical
    title phrase, two-plus stack skills, or an engineer-titled role backed
    by at least one stack skill.
    """
    haystack = " ".join([jd_text or "", _skills_text(profile)]).lower()
    if any(t in haystack for t in TECH_TITLE_KEYWORDS):
        return True
    skills = _skills_text(profile)
    stack_hits = sum(1 for k in TECH_STACK_KEYWORDS if k in skills)
    if stack_hits >= 2:
        return True
    if any(w in haystack for w in ENGINEER_WORDS) and stack_hits >= 1:
        return True
    return False


def _technical_domain(jd_text: str, profile: dict) -> str:
    """Pick the closest bank domain for a technical role from its skills."""
    s = " ".join([jd_text or "", _skills_text(profile)]).lower()
    ml_markers = ("machine learning", "deep learning", "pandas", "tensorflow",
                  "pytorch", "nlp", "model ")
    if any(k in s for k in ml_markers) or ("data" in s and ("python" in s or "sql" in s)):
        return "Data Analysis"
    # "java" is a substring of "javascript" — strip those first so a
    # frontend profile isn't mistaken for a Java backend role.
    s_no_js = s.replace("javascript", "").replace("typescript", "")
    web_markers = ("react", "node", "angular", "vue", "frontend")
    if "java" in s_no_js and not any(w in s for w in web_markers):
        return "Java"
    if "python" in s:
        return "Python"
    if "sql" in s or "database" in s:
        return "SQL"
    if "algorithm" in s or "dsa" in s:
        return "DSA"
    return "Python"


def detect_domain(jd_text: str, profile: dict) -> str:
    """Pick the bank domain best matching the JD + skills.

    Technical evidence is evaluated FIRST: a technical role is routed to
    the closest technical domain and non-technical fragments are never
    consulted (this fixes health-tech AI roles tagged Nursing, SaaS sales
    tagged Finance, ed-tech roles tagged Teaching, ...).
    """
    if has_technical_evidence(jd_text, profile):
        return _technical_domain(jd_text, profile)
    haystack = " ".join([
        jd_text or "",
        " ".join(profile.get("required_skills", []) or []),
        " ".join(profile.get("skill_gaps", []) or []),
    ]).lower()
    for fragment, domain in NONTECH_DOMAIN_KEYWORDS.items():
        if fragment in haystack:
            return domain
    return "General"


def _is_technical_text(haystack_lower: str) -> bool:
    return any(k in haystack_lower for k in TECHNICAL_KEYWORDS)


def is_technical_role(jd_text: str, profile: dict, domain: str | None = None) -> bool:
    if has_technical_evidence(jd_text, profile):
        return True
    domain = domain or detect_domain(jd_text, profile)
    if domain in NON_TECHNICAL_DOMAINS:
        return False
    haystack = " ".join([
        jd_text or "",
        " ".join(profile.get("required_skills", []) or []),
        " ".join(profile.get("candidate_skills", []) or []),
    ]).lower()
    return _is_technical_text(haystack)


def build_round_plan(is_technical: bool) -> list[str]:
    """State machine: INTRO -> DOMAIN -> [CODING] -> HR."""
    plan = ["intro", "domain"]
    if is_technical:
        plan.append("coding")
    plan.append("hr")
    return plan


def next_round(round_plan: list[str], current_round: str) -> str | None:
    """Return the round after ``current_round``, or None if HR was last."""
    try:
        idx = round_plan.index(current_round)
    except ValueError:
        return None
    if idx + 1 < len(round_plan):
        return round_plan[idx + 1]
    return None


def current_round_for_question_count(answered_count: int, round_plan: list[str]) -> str:
    """Map Q&A progress onto the round plan.

    Q1 (index 0) is always the intro opener; everything after that until
    the final question is the domain section; the last question is HR.
    TOTAL_QUESTIONS lives in planner; this helper only needs counts.
    """
    if answered_count <= 0:
        return "intro"
    # Caller passes len(history) after appending; question just answered
    # index = answered_count - 1. We report the round of the NEXT question.
    return "domain"  # refined by caller once total is known
