from pydantic import BaseModel
from typing import List


class CandidateProfile(BaseModel):
    candidate_skills: List[str] = []
    required_skills: List[str] = []
    skill_gaps: List[str] = []
    experience_level: str = "entry-level"


class UploadResponse(BaseModel):
    candidate_id: str
    resume_blob_url: str | None = None
    jd_blob_url: str | None = None
    resume_text_preview: str | None = None
    jd_text_preview: str | None = None
