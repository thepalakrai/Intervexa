# Intervexa / Virexa AI — Architecture (Phase 0 map)

Stack: FastAPI backend (`virexa-backend/main.py`) + Azure Foundry (LLM),
Azure Speech (STT/TTS), Azure Cosmos DB (sessions), single-file React
frontend (`virexa-backend/frontend/index.html`, served statically at `/`).

## Request flow

1. `POST /upload-resume`, `POST /upload-jd` → `services/storage.py`
   (Blob upload + pypdf text extract) → `{candidate_id, *_text_preview}`.
2. `POST /start-interview {candidate_id, resume_text, jd_text}`
   → `services/ai_service.analyze_profile()` (resume+JD → profile) →
   `agents/role_config.detect_domain/is_technical_role/build_round_plan` →
   `agents/interviewer.generate_opening_question()` (fixed "Tell me about
   yourself.", stable id `hr_tell_me_about_yourself`) →
   `services/cosmos.create_session()` → `{session_id, profile, domain,
   is_technical, round_plan, current_round, question}`.
3. `POST /answer` → `agents/evaluator.evaluate_answer()` (LLM scores) →
   `agents/planner.next_difficulty()` + round resolution
   (next_index >= TOTAL-1 → `hr`, else `domain`) →
   `agents/interviewer.generate_next_question(profile, history,
   difficulty, domain, round_name)` (bank-first, domain-filtered,
   hash-deduped; LLM fallback with retry) → updated session.
4. Coding (technical roles only): `GET /next-coding-problem` →
   `data/coding_problems.pick_problem()`; `POST /submit-code` →
   `services/judge0` → appended to same history shape.
5. Voice: `POST /speech-to-text` (WAV 16k mono → `services/speech.py` →
   Azure STT, returns `{text, stt_latency_ms}`, 10MB guard);
   `POST /text-to-speech` → MP3 bytes. Frontend `useVoiceRecorder`
   records via ScriptProcessor, VAD auto-stops on ~2.5s silence, 120s cap.
6. Proctoring: `POST /proctoring/event` appends
   `{event_type, timestamp, payload}` to `session.proctoring_events`;
   `GET /final-report` aggregates a `proctoring_summary`.
   Frontend `ProctoringBar` handles camera consent + `getUserMedia`,
   `visibilitychange`/`blur`/`fullscreenchange`/`copy`/`paste` events.

## Key files

| Area | File |
|---|---|
| Routes | `main.py` |
| Round engine | `agents/role_config.py` (`detect_domain`, `is_technical_role`, `build_round_plan`, `next_round`) |
| Question gen | `agents/interviewer.py` (normalize/hash dedup, `allowed_topics_for_domain`, bank-first) |
| Difficulty | `agents/planner.py` (`TOTAL_QUESTIONS=8`) |
| Scoring | `agents/evaluator.py` |
| Bank search | `services/search.py` (`find_question` Azure, `find_question_local` fallback) |
| Bank data | `data/question_bank.py`, `data/coding_problems.py` |
| STT/TTS | `services/speech.py` |
| Sessions | `services/cosmos.py` |
| Frontend | `frontend/index.html` (`UploadScreen`, `InterviewScreen`, `CodingScreen`, `ReportScreen`, `ProctoringBar`, `useVoiceRecorder`) |

## Session document

`{id, candidateId, profile, domain, is_technical, round_plan,
current_round, current_difficulty, history[], current_question,
proctoring_events[], status}`. Pre-round-engine sessions are backfilled
on first `/answer` / coding call.

## Issue → fix map
| # | Issue | Fix |
|---|---|---|
| 1 | Irrelevant questions | `allowed_topics_for_domain` + `find_question_local` domain filter + LLM `allowed_topics`/domain constraint |
| 2 | Repeated "Tell me about yourself" | Stable opener id + `question_hash` exclusion in bank + local + LLM retry |
| 3 | STT slow | VAD auto-stop + 120s cap + 10MB guard + `stt_latency_ms` logging/display |
| 4 | Coding for non-technical | `is_technical` in session; 403 in coding endpoints; frontend hides button |
| 5 | Wrong-domain questions | Domain enforced at bank, local, and LLM layers; technical-evidence-first routing (tech roles never fall into Nursing/Finance/etc. on incidental mentions like "patient") |
| 6 | Domain always → HR | `round_plan` state machine (`intro→domain→[coding]→hr`) + round-aware `generate_next_question` |
| 7 | Camera/proctoring missing | `ProctoringBar` + `/proctoring/event` + report summary |

## Question curation (admin)

- Store: `services/question_store.py` — validation (topic allowlist,
  difficulty 1-5, 12-1000 char text, known domain), normalized-text
  SHA-256 dedup (409 on duplicates), review workflow
  (`draft -> pending_review -> active`, plus `rejected`/`archived`).
  Only `active` records are served in interviews. Editing an active
  record's text/topic/difficulty auto-demotes it to `pending_review`.
- Backends: Cosmos `questions` container (partition key `/topic`;
  provisioned 2026-09-22 and seeded with the 134 static-bank records as
  `active`) when `COSMOS_ENDPOINT` / `COSMOS_KEY` are set, else
  `data/questions_curated.json` (local dev; gitignored, seed via
  `POST /admin/questions/seed`).
- API (`main.py`, all require login; writes + generate require admin
  via `ADMIN_EMAILS`): `GET/POST /admin/questions`, `POST
  /admin/questions/bulk` (≤100), `GET/PATCH /admin/questions/{id}`,
  `POST /admin/questions/{id}/review` (submit|approve|reject|archive),
  `DELETE` (archive; `?hard=true` removes),
  `POST /admin/questions/generate` (LLM drafts → always `draft`,
  never auto-published), `POST /admin/questions/seed` (idempotent
  import of the static bank as `active`).
- Retrieval order in `generate_next_question`: curated `active` →
  Azure Search bank → local static bank → LLM invention.
- UI: `AdminScreen` in `frontend/index.html` (header button on the
  upload screen when logged in) — browse/filter, approve/reject/archive,
  create form, AI-generate form, one-click seed.
