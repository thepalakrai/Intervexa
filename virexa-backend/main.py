import os
import uuid
from dotenv import load_dotenv

load_dotenv()  # must run before importing services that read env vars

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pydantic import BaseModel, Field

from services import storage, cosmos, judge0, speech, auth, question_store
from services import ai_service as foundry
from agents import interviewer, evaluator, planner
from agents import role_config
from models.candidate import UploadResponse

bearer_scheme = HTTPBearer(auto_error=False)

_admin_warned = False


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """Any valid JWT. All /admin/* endpoints require authentication."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization: Bearer <token>.")
    try:
        payload = auth.decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return {"user_id": payload.get("user_id"), "email": payload.get("email")}


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Writes (and generation) additionally require admin rights.

    Set ADMIN_EMAILS="a@x.com,b@y.com" in .env. When unset, any
    authenticated user may curate (local-dev convenience) — a warning is
    logged once so this never looks intentional in production.
    """
    global _admin_warned
    allowlist = [e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]
    if not allowlist:
        if not _admin_warned:
            print("[admin] WARNING: ADMIN_EMAILS not set - any logged-in user can curate.")
            _admin_warned = True
        return user
    if (user.get("email") or "").lower() not in allowlist:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user

app = FastAPI(title="Virexa AI Backend")

# Open for the demo frontend - it may be opened as a plain local file
# (origin "null") or served from any port, so we allow all origins here.
# Tighten this before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "virexa-backend"}


@app.post("/upload-resume", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported right now.")

    file_bytes = await file.read()
    blob_name, blob_url = storage.upload_resume(file_bytes, file.filename)

    resume_text = ""
    try:
        resume_text = storage.extract_text_from_pdf(file_bytes)
    except Exception:
        # Scanned/image PDFs will fail simple extraction - handled in a later phase
        pass

    candidate_id = str(uuid.uuid4())

    return UploadResponse(
        candidate_id=candidate_id,
        resume_blob_url=blob_url,
        resume_text_preview=resume_text if resume_text else None,
    )


@app.post("/upload-jd", response_model=UploadResponse)
async def upload_job_description(file: UploadFile = File(...), candidate_id: str = "unknown"):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF job descriptions are supported right now.")

    file_bytes = await file.read()
    blob_name, blob_url = storage.upload_job_description(file_bytes, file.filename)

    jd_text = ""
    try:
        jd_text = storage.extract_text_from_pdf(file_bytes)
    except Exception:
        pass

    return UploadResponse(
        candidate_id=candidate_id,
        jd_blob_url=blob_url,
        jd_text_preview=jd_text if jd_text else None,
    )


# ---------------------------------------------------------------------------
# Day 2: the adaptive interview loop
# ---------------------------------------------------------------------------

class StartInterviewRequest(BaseModel):
    candidate_id: str
    resume_text: str
    jd_text: str


class AnswerRequest(BaseModel):
    session_id: str
    candidate_id: str
    question_id: str
    question_text: str
    answer_text: str


@app.post("/start-interview")
def start_interview(req: StartInterviewRequest):
    """
    Analyzes resume + JD, creates a session in Cosmos, and returns the
    opening question. Call this once per candidate, right after upload.
    """
    profile = foundry.analyze_profile(req.resume_text, req.jd_text)

    # Phase 1: role-based round engine - stored on the session so every
    # later transition (Q&A rounds, coding availability) is deterministic.
    domain = role_config.detect_domain(req.jd_text, profile)
    is_technical = role_config.is_technical_role(req.jd_text, profile, domain)
    round_plan = role_config.build_round_plan(is_technical)

    session_id = str(uuid.uuid4())
    opening_question = interviewer.generate_opening_question(profile)

    session_doc = {
        "id": session_id,
        "candidateId": req.candidate_id,
        "profile": profile,
        "domain": domain,
        "is_technical": is_technical,
        "round_plan": round_plan,
        "current_round": "intro",
        "current_difficulty": opening_question["difficulty"],
        "history": [],  # filled in as answers come back
        "current_question": opening_question,
        "proctoring_events": [],
        "status": "in_progress",
    }
    cosmos.create_session(session_doc)

    return {
        "session_id": session_id,
        "profile": profile,
        "domain": domain,
        "is_technical": is_technical,
        "round_plan": round_plan,
        "current_round": "intro",
        "question": opening_question,
    }


@app.post("/answer")
def submit_answer(req: AnswerRequest):
    """
    Evaluates the candidate's answer, adjusts difficulty, and either
    returns the next question or the final report if the interview is done.
    """
    session = cosmos.get_session(req.session_id, req.candidate_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    evaluation = evaluator.evaluate_answer(req.question_text, req.answer_text)

    session["history"].append({
        "question_id": req.question_id,
        "question_text": req.question_text,
        "answer_text": req.answer_text,
        "evaluation": evaluation,
        "difficulty": session["current_difficulty"],
    })

    # Save evaluation as its own record too, useful later for the skill-gap dashboard
    cosmos.save_evaluation({
        "id": str(uuid.uuid4()),
        "candidateId": req.candidate_id,
        "session_id": req.session_id,
        "question_id": req.question_id,
        **evaluation,
    })

    if planner.is_interview_complete(session["history"]):
        session["status"] = "completed"
        cosmos.update_session(session)
        return {
            "status": "completed",
            "evaluation": evaluation,
            "message": "Interview complete. Call /final-report to see the full results.",
        }

    new_difficulty = planner.next_difficulty(session["current_difficulty"], evaluation["decision"])

    # Phase 1+2: round-aware next question. Q&A covers intro -> domain ->
    # hr; the coding round (when in round_plan) is a separate section via
    # /next-coding-problem, never injected here (fixes #6 domain->HR skip
    # confusion and #4 coding-for-non-technical).
    domain = session.get("domain")
    if not domain:  # backfill for sessions started before the round engine
        domain = role_config.detect_domain("", session["profile"])
        session["domain"] = domain
    if "round_plan" not in session or "is_technical" not in session:
        session["is_technical"] = role_config.is_technical_role("", session["profile"], domain)
        session["round_plan"] = role_config.build_round_plan(session["is_technical"])
    next_index = len(session["history"])  # 0-based index of the upcoming question
    if next_index >= planner.TOTAL_QUESTIONS - 1:
        next_round = "hr"
    elif next_index == 0:
        next_round = "intro"
    else:
        next_round = "domain"
    next_question = interviewer.generate_next_question(
        session["profile"], session["history"], new_difficulty,
        domain=domain, round_name=next_round,
    )

    session["current_difficulty"] = new_difficulty
    session["current_question"] = next_question
    session["current_round"] = next_round
    cosmos.update_session(session)

    return {
        "status": "in_progress",
        "evaluation": evaluation,
        "next_question": next_question,
        "current_round": next_round,
        "round_plan": session["round_plan"],
    }


@app.get("/final-report/{candidate_id}/{session_id}")
def final_report(candidate_id: str, session_id: str):
    session = cosmos.get_session(session_id, candidate_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    history = session["history"]
    if not history:
        raise HTTPException(status_code=400, detail="No answers recorded yet.")

    overall_scores = [h["evaluation"]["overall"] for h in history]
    average_overall = sum(overall_scores) / len(overall_scores)

    proctoring_events = session.get("proctoring_events", [])
    proctoring_summary = {
        "total_events": len(proctoring_events),
        "tab_switches": sum(1 for e in proctoring_events if e.get("event_type") == "TAB_SWITCH"),
        "focus_loss": sum(1 for e in proctoring_events if e.get("event_type") == "FOCUS_LOSS"),
        "fullscreen_exits": sum(1 for e in proctoring_events if e.get("event_type") == "FULLSCREEN_EXIT"),
        "copy_paste": sum(1 for e in proctoring_events if e.get("event_type") in ("COPY", "PASTE")),
        "no_face": sum(1 for e in proctoring_events if e.get("event_type") == "NO_FACE"),
    }

    return {
        "candidate_id": candidate_id,
        "session_id": session_id,
        "overall_readiness": round(average_overall, 1),
        "questions_answered": len(history),
        "skill_gaps": session["profile"].get("skill_gaps", []),
        "domain": session.get("domain"),
        "is_technical": session.get("is_technical"),
        "round_plan": session.get("round_plan"),
        "proctoring_summary": proctoring_summary,
        "history": history,
    }


# ---------------------------------------------------------------------------
# Day 4 (started early): the coding round
# ---------------------------------------------------------------------------

from data import coding_problems
from data.coding_problems import CODING_PROBLEMS


class SubmitCodeRequest(BaseModel):
    session_id: str
    candidate_id: str
    problem_id: str
    source_code: str
    language: str = "python"


@app.get("/coding-problems")
def list_coding_problems():
    """
    Returns the coding problems WITHOUT test cases (so the candidate
    doesn't see the expected outputs) - just id, title, topic, difficulty,
    description. Useful for browsing; /next-coding-problem is what actually
    auto-selects one based on the candidate's profile.
    """
    return [
        {
            "id": p["id"],
            "title": p["title"],
            "topic": p["topic"],
            "difficulty": p["difficulty"],
            "description": p["description"],
        }
        for p in CODING_PROBLEMS
    ]


@app.get("/next-coding-problem/{candidate_id}/{session_id}")
def next_coding_problem(candidate_id: str, session_id: str):
    """
    Auto-picks the best next coding problem for this candidate: matches
    topic relevance to their JD/skill_gaps and their current interview
    difficulty, excluding problems already attempted this session.
    """
    session = cosmos.get_session(session_id, candidate_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Phase 1 (#4): non-technical roles have no coding round at all.
    is_technical = session.get("is_technical")
    if is_technical is None:
        is_technical = role_config.is_technical_role(
            "", session.get("profile", {}), session.get("domain"))
        session["is_technical"] = is_technical
    if not is_technical:
        raise HTTPException(
            status_code=403,
            detail="Coding round is not part of this interview (non-technical role).",
        )

    already_attempted = [
        h["question_id"] for h in session["history"]
        if h["question_id"].startswith("cp_")
    ]

    problem = coding_problems.pick_problem(
        session["profile"], session["current_difficulty"], already_attempted
    )
    if problem is None:
        return {"message": "All coding problems have been attempted this session."}

    return {
        "id": problem["id"],
        "title": problem["title"],
        "topic": problem["topic"],
        "difficulty": problem["difficulty"],
        "description": problem["description"],
    }


@app.post("/submit-code")
def submit_code(req: SubmitCodeRequest):
    """
    Runs the candidate's code against the problem's real test cases via
    Judge0, records the result in the session (same history/evaluation
    shape as a regular answer, so it feeds into the final report and the
    difficulty engine the same way).
    """
    problem = next((p for p in CODING_PROBLEMS if p["id"] == req.problem_id), None)
    if problem is None:
        raise HTTPException(status_code=404, detail="Coding problem not found.")

    session = cosmos.get_session(req.session_id, req.candidate_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.get("is_technical") is False:
        raise HTTPException(
            status_code=403,
            detail="Coding round is not part of this interview (non-technical role).",
        )

    judged = judge0.judge_submission(req.source_code, problem["test_cases"], req.language)

    # Map the coding score into the same evaluation shape used elsewhere,
    # so the difficulty engine and final report don't need special-casing.
    evaluation = {
        "technical_accuracy": judged["score"],
        "depth": judged["score"],
        "communication": None,  # not applicable for a coding submission
        "problem_solving": judged["score"],
        "confidence": None,
        "overall": judged["score"],
        "decision": (
            "increase_difficulty" if judged["score"] == 100
            else "decrease_difficulty" if judged["score"] == 0
            else "same"
        ),
    }

    session["history"].append({
        "question_id": problem["id"],
        "question_text": f"[Coding] {problem['title']}",
        "answer_text": req.source_code,
        "evaluation": evaluation,
        "difficulty": problem["difficulty"],
        "test_results": judged["test_results"],
    })
    cosmos.update_session(session)

    return {
        "problem_title": problem["title"],
        "score": judged["score"],
        "passed": judged["passed"],
        "total": judged["total"],
        "test_results": judged["test_results"],
    }


# ---------------------------------------------------------------------------
# Question curation (admin): generate / create / review / publish.
# Only "active" records are served in interviews (see question_store).
# Reads need any valid login; writes need admin (ADMIN_EMAILS).
# ---------------------------------------------------------------------------

class QuestionCreateRequest(BaseModel):
    topic: str
    difficulty: int
    text: str
    expected_concepts: list[str] = Field(default_factory=list)
    domain: str | None = None
    status: str = "draft"  # draft | pending_review (never trust client-sent "active")


class QuestionBulkRequest(BaseModel):
    items: list[QuestionCreateRequest]


class QuestionPatchRequest(BaseModel):
    topic: str | None = None
    difficulty: int | None = None
    text: str | None = None
    expected_concepts: list[str] | None = None
    domain: str | None = None


class QuestionReviewRequest(BaseModel):
    action: str  # submit | approve | reject | archive
    note: str | None = None


class QuestionGenerateRequest(BaseModel):
    domain: str | None = None
    topic: str | None = None
    difficulty: int = 2
    count: int = 5
    context: str | None = None  # e.g. role focus, extra constraints


def _question_error(e: Exception):
    if isinstance(e, question_store.DuplicateQuestionError):
        raise HTTPException(status_code=409, detail=str(e))
    if isinstance(e, question_store.QuestionValidationError):
        raise HTTPException(status_code=422, detail=str(e))
    raise e


@app.get("/admin/questions/topics")
def admin_question_topics(user: dict = Depends(get_current_user)):
    """Allowlist values for the curation forms (topics, domains, statuses)."""
    return {
        "topics": question_store.valid_topics(),
        "domains": question_store.valid_domains(),
        "statuses": list(question_store.STATUSES),
    }


@app.get("/admin/questions")
def admin_list_questions(
    topic: str | None = None,
    domain: str | None = None,
    difficulty: int | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
):
    items, total = question_store.list_questions(
        topic=topic, domain=domain, difficulty=difficulty, status=status,
        q=q, limit=min(limit, 200), offset=max(0, offset),
    )
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@app.post("/admin/questions", status_code=201)
def admin_create_question(req: QuestionCreateRequest, admin: dict = Depends(require_admin)):
    if req.status not in ("draft", "pending_review"):
        raise HTTPException(status_code=422, detail="New questions must start as draft or pending_review.")
    try:
        doc = question_store.create_question(
            topic=req.topic, difficulty=req.difficulty, text=req.text,
            expected_concepts=req.expected_concepts, domain=req.domain,
            status=req.status, source="manual", created_by=admin.get("email"),
        )
    except Exception as e:
        _question_error(e)
    return doc


@app.post("/admin/questions/bulk", status_code=201)
def admin_bulk_create_questions(req: QuestionBulkRequest, admin: dict = Depends(require_admin)):
    if len(req.items) > 100:
        raise HTTPException(status_code=422, detail="Bulk limit is 100 items per request.")
    created, errors = [], []
    for i, item in enumerate(req.items):
        if item.status not in ("draft", "pending_review"):
            errors.append({"index": i, "error": "New questions must start as draft or pending_review."})
            continue
        try:
            created.append(question_store.create_question(
                topic=item.topic, difficulty=item.difficulty, text=item.text,
                expected_concepts=item.expected_concepts, domain=item.domain,
                status=item.status, source="manual", created_by=admin.get("email"),
            ))
        except (question_store.DuplicateQuestionError, question_store.QuestionValidationError) as e:
            errors.append({"index": i, "error": str(e)})
    return {"created": created, "created_count": len(created), "errors": errors}


@app.get("/admin/questions/{question_id}")
def admin_get_question(question_id: str, user: dict = Depends(get_current_user)):
    doc = question_store.get_question(question_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    return doc


@app.patch("/admin/questions/{question_id}")
def admin_update_question(
    question_id: str, req: QuestionPatchRequest, admin: dict = Depends(require_admin)
):
    patch = {k: v for k, v in req.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(status_code=422, detail="No fields to update.")
    try:
        doc = question_store.update_question(question_id, patch)
    except Exception as e:
        _question_error(e)
    if doc is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    return doc


@app.post("/admin/questions/{question_id}/review")
def admin_review_question(
    question_id: str, req: QuestionReviewRequest, admin: dict = Depends(require_admin)
):
    try:
        doc = question_store.review_question(question_id, req.action, req.note)
    except Exception as e:
        _question_error(e)
    if doc is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    return doc


@app.delete("/admin/questions/{question_id}")
def admin_delete_question(
    question_id: str, hard: bool = False, admin: dict = Depends(require_admin)
):
    if hard:
        ok = question_store.delete_question(question_id, hard=True)
        if not ok:
            raise HTTPException(status_code=404, detail="Question not found.")
        return {"ok": True, "hard_deleted": True}
    try:
        doc = question_store.review_question(question_id, "archive", f"Archived by {admin.get('email')}")
    except Exception as e:
        _question_error(e)
    if doc is None:
        raise HTTPException(status_code=404, detail="Question not found.")
    return {"ok": True, "archived": doc}


@app.post("/admin/questions/generate", status_code=201)
def admin_generate_questions(req: QuestionGenerateRequest, admin: dict = Depends(require_admin)):
    """LLM-assisted drafting: generates candidates and saves them as
    drafts for human review. NEVER auto-publishes (always needs approve)."""
    import json as _json

    if req.topic and req.topic not in question_store.valid_topics():
        raise HTTPException(status_code=422, detail=f"Unknown topic '{req.topic}'.")
    if req.domain and req.domain not in question_store.valid_domains():
        raise HTTPException(status_code=422, detail=f"Unknown domain '{req.domain}'.")
    if not 1 <= req.difficulty <= 5:
        raise HTTPException(status_code=422, detail="difficulty must be 1-5.")
    count = max(1, min(req.count, 10))

    existing, _ = question_store.list_questions(
        topic=req.topic, domain=req.domain, status=None, limit=200, offset=0)
    avoid = [r["text"] for r in existing if r.get("status") in ("active", "pending_review", "draft")]

    system_prompt = (
        "You are an expert interview-question author. Given a domain/topic and "
        "difficulty (1=Beginner..5=Expert), write distinct, role-relevant interview "
        "questions. Respond ONLY with a JSON object: "
        '{"questions": [{"text": "...", "expected_concepts": ["..."]}]}. '
        "No prose, no markdown fences."
    )
    user_message = _json.dumps({
        "domain": req.domain, "topic": req.topic or req.domain or "General",
        "difficulty": req.difficulty, "count": count,
        "context": req.context,
        "avoid_repeats": avoid[:50],
    })
    try:
        raw = foundry.chat(system_prompt, user_message, json_mode=True)
        parsed = _json.loads(raw)
        candidates = parsed.get("questions", [])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Generation failed: {e}")
    if not isinstance(candidates, list):
        raise HTTPException(status_code=502, detail="Model returned an unexpected shape.")

    created, skipped, errors = [], 0, []
    for i, c in enumerate(candidates[:count]):
        try:
            created.append(question_store.create_question(
                topic=req.topic or req.domain or "General",
                difficulty=req.difficulty,
                text=(c.get("text") or "").strip(),
                expected_concepts=c.get("expected_concepts", []),
                domain=req.domain,
                status="draft",
                source="generated",
                created_by=admin.get("email"),
            ))
        except question_store.DuplicateQuestionError:
            skipped += 1
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    return {"created": created, "created_count": len(created),
            "skipped_duplicates": skipped, "errors": errors}


@app.post("/admin/questions/seed")
def admin_seed_questions(admin: dict = Depends(require_admin)):
    """Idempotent one-time import of the static bank as active records."""
    return question_store.seed_from_static_bank(created_by=admin.get("email"))


# ---------------------------------------------------------------------------
# Day 4: voice (speech-to-text / text-to-speech)
# ---------------------------------------------------------------------------

from fastapi.responses import Response


class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "en-US-JennyNeural"


@app.post("/speech-to-text")
async def speech_to_text_endpoint(file: UploadFile = File(...)):
    """
    Accepts a WAV audio file (16kHz, 16-bit, mono PCM) and returns the
    recognized text. The frontend's recorder must produce audio in this
    format - most browser recording + a quick conversion step handles this.
    """
    import time

    started = time.perf_counter()
    audio_bytes = await file.read()
    # Phase 3: guard against oversized uploads (long recordings stall the
    # interview). ~10MB ~= ~5min at 16kHz mono 16-bit. Frontend VAD trims
    # silence and auto-stops well before this.
    if len(audio_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Audio clip too long. Please record answers under ~2 minutes.",
        )
    try:
        text = speech.speech_to_text(audio_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech recognition failed: {e}")

    latency_ms = int((time.perf_counter() - started) * 1000)
    print(f"[stt] bytes={len(audio_bytes)} latency_ms={latency_ms}")
    return {"text": text, "stt_latency_ms": latency_ms}


class ProctoringEventRequest(BaseModel):
    session_id: str
    candidate_id: str
    event_type: str  # TAB_SWITCH | FOCUS_LOSS | FULLSCREEN_EXIT | COPY | PASTE | NO_FACE | FACE_OK | CAMERA_DENIED
    payload: dict = {}


@app.post("/proctoring/event")
def proctoring_event(req: ProctoringEventRequest):
    """Phase 4: log a camera/focus/tab-switch signal onto the session."""
    import datetime

    session = cosmos.get_session(req.session_id, req.candidate_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    event = {
        "event_type": req.event_type,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "payload": req.payload or {},
    }
    session.setdefault("proctoring_events", []).append(event)
    cosmos.update_session(session)
    return {"ok": True, "total_events": len(session["proctoring_events"])}


@app.post("/text-to-speech")
def text_to_speech_endpoint(req: TextToSpeechRequest):
    """
    Converts text to speech and returns raw MP3 audio bytes directly
    (not JSON) - the frontend plays this straight from the response body.
    """
    try:
        audio_bytes = speech.text_to_speech(req.text, req.voice)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {e}")

    return Response(content=audio_bytes, media_type="audio/mpeg")


# ---------------------------------------------------------------------------
# Authentication (signup / login)
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/me")
def me(user: dict = Depends(get_current_user)):
    """Validate the stored token and return the profile it belongs to."""
    name = None
    try:
        record = cosmos.get_user_by_email(user.get("email") or "")
        name = (record or {}).get("name")
    except Exception:
        pass
    return {"user_id": user.get("user_id"), "name": name, "email": user.get("email")}


@app.post("/signup")
def signup(req: SignupRequest):
    existing = cosmos.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": req.email,
        "name": req.name,
        "password_hash": auth.hash_password(req.password),
    }
    cosmos.create_user(user_doc)

    token = auth.create_token(user_id, req.email)
    return {"token": token, "name": req.name, "email": req.email}


@app.post("/login")
def login(req: LoginRequest):
    user = cosmos.get_user_by_email(req.email)
    if not user or not auth.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = auth.create_token(user["id"], user["email"])
    return {"token": token, "name": user["name"], "email": user["email"]}


# ---------------------------------------------------------------------------
# Serve the frontend (frontend/index.html) at the root path.
# Mounted LAST so it never shadows the API routes defined above -
# FastAPI matches explicit routes first, falling back to this mount
# only for paths not already handled.
# ---------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    # Azure App Service sets the PORT env var; default to 8000 for local dev.
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
