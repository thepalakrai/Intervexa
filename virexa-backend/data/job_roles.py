"""
Pre-built job role templates - lets a candidate pick a role instead of
uploading a JD PDF. Each template's text is fed into the same
analyze_profile() function a real uploaded JD would go through, so the
rest of the pipeline (skill gaps, question bank matching) works unchanged.
"""

ROLE_TEMPLATES = {
    "data_analyst": {
        "label": "Data Analyst",
        "jd_text": "Data Analyst role requiring strong SQL, Python, and data visualization skills. Responsible for collecting, cleaning, and analyzing data, building dashboards, running statistical analysis, and presenting insights to stakeholders. Experience with ETL processes and hypothesis testing is a plus.",
    },
    "software_engineer": {
        "label": "Software Engineer",
        "jd_text": "Software Engineer role requiring strong Java or Python skills, data structures and algorithms (DSA), database design (DBMS), and REST API development. Responsible for writing clean, efficient code, debugging, and collaborating in an agile team.",
    },
    "nurse": {
        "label": "Registered Nurse",
        "jd_text": "Registered Nurse role requiring patient care experience, ability to handle emergencies calmly, strong communication with patients and families, and attention to safety protocols and medication administration.",
    },
    "financial_analyst": {
        "label": "Financial Analyst",
        "jd_text": "Financial Analyst role requiring strong understanding of financial statements, budgeting, forecasting, and accounting principles. Responsible for financial reporting, variance analysis, and supporting business decision-making.",
    },
    "mechanical_engineer": {
        "label": "Mechanical Engineer",
        "jd_text": "Mechanical Engineer role requiring knowledge of mechanical design, materials, stress analysis, and manufacturing processes. Responsible for designing and testing mechanical components and systems.",
    },
    "civil_engineer": {
        "label": "Civil Engineer",
        "jd_text": "Civil Engineer role requiring knowledge of structural design, construction methods, and project management. Responsible for planning, designing, and overseeing construction projects.",
    },
    "electrical_engineer": {
        "label": "Electrical Engineer",
        "jd_text": "Electrical Engineer role requiring strong understanding of circuit design, power systems, and safety standards. Responsible for designing, testing, and troubleshooting electrical systems.",
    },
    "teacher": {
        "label": "Teacher",
        "jd_text": "Teacher role requiring strong communication and classroom management skills, ability to adapt lessons for different learning styles, and experience assessing student understanding.",
    },
    "aviation": {
        "label": "Aviation / Cabin Crew",
        "jd_text": "Aviation / Cabin Crew role requiring calm handling of emergencies, strict adherence to safety procedures, excellent customer service, and clear communication under pressure.",
    },
    "hr_recruiter": {
        "label": "HR Recruiter",
        "jd_text": "HR Recruiter role requiring strong interpersonal skills, experience with candidate evaluation, conflict resolution, and knowledge of employment policies and fair hiring practices.",
    },
    "customer_service": {
        "label": "Customer Service Representative",
        "jd_text": "Customer Service Representative role requiring strong communication skills, patience, problem-solving under pressure, and the ability to de-escalate difficult customer situations.",
    },
    "marketing": {
        "label": "Marketing Executive",
        "jd_text": "Marketing Executive role requiring experience with campaign planning, audience research, performance measurement (KPIs/ROI), and creative problem-solving on a budget.",
    },
    "sales": {
        "label": "Sales Executive",
        "jd_text": "Sales Executive role requiring strong persuasion and negotiation skills, objection handling, relationship-building with clients, and pipeline management.",
    },
    "hospitality": {
        "label": "Hospitality / Hotel Management",
        "jd_text": "Hospitality role requiring excellent guest service skills, ability to handle complaints gracefully, attention to detail, and composure during high-pressure peak hours.",
    },
    "legal": {
        "label": "Legal Assistant",
        "jd_text": "Legal Assistant role requiring strong attention to detail, ability to explain legal concepts in plain language, confidentiality, and legal research skills.",
    },
    "retail": {
        "label": "Retail Operations",
        "jd_text": "Retail Operations role requiring strong customer service, inventory management skills, ability to train new staff, and composure during busy shifts.",
    },
}


def get_role_list():
    return [{"key": k, "label": v["label"]} for k, v in ROLE_TEMPLATES.items()]


def get_template_jd(role_key: str) -> str | None:
    role = ROLE_TEMPLATES.get(role_key)
    return role["jd_text"] if role else None
