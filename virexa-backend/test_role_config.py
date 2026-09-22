"""Domain detection + technical routing regression tests.

Run:  python test_role_config.py
Covers the reported bug (AI/ML profile asked Nursing questions) and the
neighboring first-match traps (SaaS sales -> Finance, ed-tech -> Teaching).
"""
from agents import role_config as r

passed = []


def check(name, cond, detail=""):
    assert cond, f"FAILED: {name} {detail}"
    passed.append(name)
    print(f"  PASS {name} {detail}")


# 1. The reported bug: AI voice-engineer JD mentioning patients.
ai_profile = {
    "candidate_skills": ["LLMs", "RAG", "PyTorch", "Python (Advanced)", "SQL", "Pandas"],
    "required_skills": ["Node.js", "WebRTC", "LiveKit", "Twilio"],
    "skill_gaps": ["Rate limiting", "ASR"],
}
ai_jd = ("AI voice engineer for a healthcare clinic. Build patient calling "
         "agents with Python, speech recognition and LiveKit.")
d = r.detect_domain(ai_jd, ai_profile)
check("health-tech AI JD not Nursing", d != "Nursing", f"-> {d}")
check("health-tech AI JD technical", r.is_technical_role(ai_jd, ai_profile, d) is True)
check("health-tech AI JD domain Data Analysis", d == "Data Analysis", f"-> {d}")
check("health-tech AI gets coding round",
      "coding" in r.build_round_plan(r.is_technical_role(ai_jd, ai_profile, d)))

# 2. Genuine nurse JD still routes to Nursing (no regression).
nurse_profile = {"candidate_skills": ["triage", "patient care"],
                 "required_skills": ["medication safety"], "skill_gaps": []}
nurse_jd = "Staff Nurse for ICU ward. Patient care, triage and family communication."
d = r.detect_domain(nurse_jd, nurse_profile)
check("nurse JD -> Nursing", d == "Nursing", f"-> {d}")
check("nurse JD non-technical", r.is_technical_role(nurse_jd, nurse_profile, d) is False)

# 3. SaaS sales JD mentioning software + key accounts.
sales_profile = {"candidate_skills": ["prospecting", "negotiation"],
                 "required_skills": ["cold calling"], "skill_gaps": ["objection handling"]}
sales_jd = "Sales Executive selling our software platform. Manage key accounts and pipeline."
d = r.detect_domain(sales_jd, sales_profile)
check("SaaS sales not Finance/technical", d == "Sales", f"-> {d}")
check("SaaS sales non-technical", r.is_technical_role(sales_jd, sales_profile, d) is False)

# 4. Java backend JD.
java_profile = {"candidate_skills": ["Java", "Spring", "SQL"],
                "required_skills": ["REST APIs"], "skill_gaps": []}
java_jd = "Backend Engineer (Java). Build microservices with Spring and SQL."
d = r.detect_domain(java_jd, java_profile)
check("java backend technical + Java domain",
      r.is_technical_role(java_jd, java_profile, d) and d == "Java", f"-> {d}")

# 5. Finance JD mentioning the stock market must not become Marketing.
fin_profile = {"candidate_skills": ["reconciliation", "auditing"],
               "required_skills": ["financial reporting"], "skill_gaps": []}
fin_jd = "Accountant. Reconcile statements; follow stock market trends for valuations."
d = r.detect_domain(fin_jd, fin_profile)
check("finance JD -> Finance", d == "Finance", f"-> {d}")

# 6. Frontend React JD stays technical without collapsing to Java.
fe_profile = {"candidate_skills": ["JavaScript", "React", "TypeScript"],
              "required_skills": ["CSS"], "skill_gaps": []}
fe_jd = "Frontend Developer. React and TypeScript single-page apps."
d = r.detect_domain(fe_jd, fe_profile)
check("frontend technical, not Java",
      r.is_technical_role(fe_jd, fe_profile, d) and d != "Java", f"-> {d}")

# 7. State machine sanity.
check("non-tech plan", r.build_round_plan(False) == ["intro", "domain", "hr"])
check("tech plan", r.build_round_plan(True) == ["intro", "domain", "coding", "hr"])
check("next_round", r.next_round(["intro", "domain", "coding", "hr"], "domain") == "coding")

print(f"ALL {len(passed)} ROLE_CONFIG CHECKS PASSED")
