"""
Maps each pre-built job role (see job_roles.py) to the question-bank
topics that are actually relevant to it.

Used by search.find_question() to hard-filter which topics can ever be
returned for a given role/round combination.
"""

# Keys here MUST match job_roles.py's ROLE_TEMPLATES keys exactly.
ROLE_TOPICS = {
    "data_analyst": ["SQL", "Python", "Data Analysis", "DBMS"],
    "software_engineer": ["Java", "DSA", "DBMS"],
    "nurse": ["Nursing"],
    "financial_analyst": ["Finance"],
    "mechanical_engineer": ["Mechanical Engineering"],
    "civil_engineer": ["Civil Engineering"],
    "electrical_engineer": ["Electrical Engineering"],
    "teacher": ["Teaching"],
    "aviation": ["Aviation"],
    "hr_recruiter": ["HR Recruitment"],
    "customer_service": ["Customer Service"],
    "marketing": ["Marketing"],
    "sales": ["Sales"],
    "hospitality": ["Hospitality"],
    "legal": ["Legal"],
    "retail": ["Retail Operations"],
}


def get_allowed_topics(role_key: str | None, forced_topic: str | None = None) -> list[str] | None:
    """
    Returns the bank topics allowed for this role/round, or None if
    role_key is unset/unrecognized (JD-upload sessions - can't map a
    free-text JD to a fixed topic list, so don't filter).

    forced_topic mirrors main.py's per-round tracking: "HR" during the
    HR round, None during the domain round.

    CHANGED: previously "HR" was appended to every role's allowed topics
    UNCONDITIONALLY, regardless of round. That meant an HR question could
    still legitimately rank highest and get served during the DOMAIN
    round - the round the candidate explicitly chose for technical/
    professional questions, not behavioral ones. Now:
    - HR round (forced_topic == "HR"): restrict to ONLY "HR" - a domain
      question has no business appearing in a round the candidate chose
      specifically to be behavioral.
    - Domain round (forced_topic is None): restrict to this role's own
      topics + "Project" - "HR" is EXCLUDED here, which is exactly the
      fix.
    """
    if forced_topic == "HR":
        return ["HR"]

    if not role_key or role_key not in ROLE_TOPICS:
        return None

    return ROLE_TOPICS[role_key] + ["Project"]
