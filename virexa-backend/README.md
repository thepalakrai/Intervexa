# Virexa AI — AI Interview Coach (Topic #19)

Full product: upload resume + JD → adaptive interview → coding round →
voice → report → admin curation. Built on Microsoft Foundry
(`gpt-4.1-mini` deployment), Azure AI Search, Blob Storage, Cosmos DB,
Speech, and (new) Azure Key Vault.

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the env template and fill in your real Azure credentials
copy .env.example .env
# then edit .env:
#   - Foundry API key + endpoint + deployment (gpt-4.1-mini)
#   - Blob Storage connection string
#   - Cosmos DB endpoint + key
#   - Search endpoint + key, Speech key + region
#   - (production) AZURE_KEY_VAULT_URL — see "Secrets" below
```

## Run it

```bash
python main.py
```

API live at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`. Static frontend (`frontend/index.html`)
is served at `/`.

## What's wired up

- `POST /upload-resume` — PDF → `resumes` Blob container, text extract,
  returns `candidate_id` + text preview.
- `POST /upload-jd` — same for `job-descriptions`.
- `POST /start-interview` — resume + JD → profile via Foundry, Cosmos
  session, opening question.
- `POST /answer` — evaluate via Foundry, adjust difficulty, next question.
  Returns `status: "completed"` after 8 questions.
- `GET /final-report/{candidate_id}/{session_id}` — readiness score,
  skill gaps, history, proctoring summary.
- Coding round: `GET /coding-problems`, `GET /next-coding-problem/...`,
  `POST /submit-code` (Judge0; technical roles only).
- Voice: `POST /speech-to-text` (WAV 16k mono, 10 MB guard),
  `POST /text-to-speech` (MP3 bytes).
- Proctoring: `POST /proctoring/event` + summary in the final report.
- Admin curation: `GET/POST /admin/questions`, bulk create, get/patch,
  review (submit|approve|reject|archive), delete, `POST
  /admin/questions/generate` (LLM drafts → always `draft`), `POST
  /admin/questions/seed`. Reads need login; writes need `ADMIN_EMAILS`.
- Auth: `POST /signup`, `POST /login`, `GET /me` (JWT).

### New: Foundry Agent workflow + Key Vault (slide-gap closure)

- `GET /foundry/status` — slide steps 1–8 → yes/partial + how.
- `GET /foundry/agents` — the 4 Foundry Agent definitions
  (interviewer, evaluator, profile analyzer, admin generator).
- `GET /foundry/agents/{name}` — full card (instructions + tools).
- `GET /foundry/agents/{name}/export` — copy-paste pack to recreate the
  agent in the Foundry portal (for the optional playground screenshot).
- `POST /foundry/agents/{name}/test {"message": "..."}` — in-app
  playground (portal "Test in playground" equivalent).
- `GET /foundry/deployment` — honest production story (app is deployed,
  not a Foundry-hosted Agent endpoint; promotion path documented).
- `GET /secrets/status` — env vs Key Vault source per secret (no values).

## Slide mapping (what judges check)

### Is the workflow "done"?

| Verdict | Meaning |
|---|---|
| Conceptually: yes | Connect → instruct → tools → test → iterate → ship in an app |
| Literally as on the slide | Covered in code via `services/foundry_agent.py` + `/foundry/*`; the only literal-portal piece is the optional screenshot upgrade below |

### Step-by-step

| Step on slide | Done? | How |
|---|---|---|
| 1. Connect to your Foundry project | Yes | Foundry endpoint + key + deployment (`AZURE_OPENAI_*` via Key Vault or `.env`) |
| 2. Create an AI agent | Yes | 4 Foundry Agent definitions in `services/foundry_agent.py` (interviewer, evaluator, profile analyzer, admin generator); mirror in portal via `/foundry/agents/{name}/export` |
| 3. Configure agent instructions | Yes | System prompts in `agents/interviewer.py`, `agents/evaluator.py`, `analyze_profile`, admin generator — imported live by the registry (versioned) |
| 4. Add tools | Yes | Question bank (Azure AI Search + curated store), Judge0, Cosmos, Blob, Speech — called from FastAPI; listed per-agent in the registry |
| 5. Test the agent in playground | Yes | `POST /foundry/agents/{name}/test` (in-app playground) + `/docs` + unit tests (`test_role_config`, `test_question_store`, …) + portal playground via export |
| 6. Iterate on design | Yes | Domain routing fixes, hash dedup, rounds, curation, reindex scripts; instructions versioned (`INSTRUCTIONS_VERSION`) |
| 7. Deploy agent to production | Partial | The app (FastAPI + frontend) is deployed, not a Foundry-hosted Agent endpoint — this is the documented architecture; promotion path in `GET /foundry/deployment` |
| 8. Integrate into applications | Yes | Full product: upload → interview → coding → voice → report → admin |

### Resources

| Resource | You |
|---|---|
| Microsoft Foundry project + model deployment (e.g. GPT-4.1-class) | Yes (`gpt-4.1-mini` deployment) |
| Azure AI Search | Yes |
| Azure Storage | Yes |
| Azure Key Vault | Yes — supported (`AZURE_KEY_VAULT_URL` + `services/secrets.py`); falls back to `.env` / App Settings when unset |
| Azure Functions | No — logic lives in FastAPI (documented architecture; each route is function-sized if migration is ever required) |

### Secrets (Key Vault)

- Local/demo: leave `AZURE_KEY_VAULT_URL` empty → app runs on `.env`.
- Production: create a vault, store secrets with **dashes**
  (`AZURE-OPENAI-API-KEY`, …), grant the app Managed Identity
  `Key Vault Secrets User`, set `AZURE_KEY_VAULT_URL=https://<vault>.vault.azure.net/`.
  `services/secrets.py` resolves env-first, vault-second, and warms values
  into `os.environ` at startup — no other code changes needed.
- Check: `GET /secrets/status`.

### Optional portal upgrade (only if you have time before presenting)

Create ONE Foundry Agent in the portal with the interviewer system prompt
+ one tool, test in playground, screenshot it — then say the production
path still goes through your API for sessions and scoring. Not required
for a working demo.

```bash
# 1. Get the copy-paste pack
curl http://localhost:8000/foundry/agents/virexa-interviewer/export
# 2. Foundry portal → project → Agents → + Create agent → paste
#    instructions → attach 1 tool → Test in playground → screenshot.
```

### How to say this if a judge points at that slide

> "We followed the same development workflow, implemented as a custom
> application on Foundry: same connect → instruct → tools → test →
> iterate → ship loop. Our four agents are defined in
> `services/foundry_agent.py` with the same instructions and tools you'd
> attach in the portal — try `GET /foundry/status` and
> `POST /foundry/agents/virexa-interviewer/test`. Production runs through
> our API because interviews need sessions, scoring, and proctoring — the
> portal playground can't hold that state. Key Vault is supported for
> secrets; Functions logic lives in FastAPI by design."

## Testing the full loop (no frontend needed)

1. Run the server (`python main.py`)
2. Open `http://localhost:8000/docs`
3. `POST /upload-resume` with a real PDF → copy `candidate_id` + text
4. `POST /upload-jd` the same way (same `candidate_id` as query param)
5. `POST /start-interview` with `{candidate_id, resume_text, jd_text}`
6. `POST /answer` with question + typed answers (try strong + weak, watch
   difficulty adapt)
7. After `"status": "completed"`, `GET /final-report/{candidate_id}/{session_id}`
8. (New) `GET /foundry/status` + `POST /foundry/agents/virexa-interviewer/test`
   for the slide coverage demo.

**Note:** Day-1 `text_preview` is capped; for real testing paste full text
so profile analysis has enough signal.
