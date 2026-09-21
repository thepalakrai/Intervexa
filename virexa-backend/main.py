import os
import uuid
from dotenv import load_dotenv

load_dotenv()  # must run before importing services that read env vars

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from services import storage, cosmos, judge0, speech, auth
from services import ai_service as foundry
from agents import interviewer, evaluator, planner
from models.candidate import UploadResponse

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

    session_id = str(uuid.uuid4())
    opening_question = interviewer.generate_opening_question(profile)

    session_doc = {
        "id": session_id,
        "candidateId": req.candidate_id,
        "profile": profile,
        "current_difficulty": opening_question["difficulty"],
        "history": [],  # filled in as answers come back
        "current_question": opening_question,
        "status": "in_progress",
    }
    cosmos.create_session(session_doc)

    return {
        "session_id": session_id,
        "profile": profile,
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
    next_question = interviewer.generate_next_question(
        session["profile"], session["history"], new_difficulty
    )

    session["current_difficulty"] = new_difficulty
    session["current_question"] = next_question
    cosmos.update_session(session)

    return {
        "status": "in_progress",
        "evaluation": evaluation,
        "next_question": next_question,
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

    return {
        "candidate_id": candidate_id,
        "session_id": session_id,
        "overall_readiness": round(average_overall, 1),
        "questions_answered": len(history),
        "skill_gaps": session["profile"].get("skill_gaps", []),
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
    audio_bytes = await file.read()
    try:
        text = speech.speech_to_text(audio_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech recognition failed: {e}")

    return {"text": text}


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
