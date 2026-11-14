# VERITY AI

An editorial intelligence workspace for investigating AI-generated answers. Verity extracts factual claims, searches live web sources, compares evidence, assesses freshness separately from confidence, and presents a source-linked report and careful correction.

## Stack

- React, Vite, Tailwind CSS, React Router, Lucide, Recharts and Axios
- FastAPI, Pydantic, HTTPX and an initial SQLite report repository
- Groq structured chat completions with model discovery from the current account catalog
- Tavily Search and optional Extract

## Development

Requirements: Node.js 22, pnpm 11.25.0 and Python 3.12.

```bash
pnpm install
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
```

Set `GROQ_API_KEY` and `TAVILY_API_KEY` as environment variables through the protected project-secret interface. Never paste credentials into `.env`, source code, browser variables, Git or logs. Optional `GROQ_MODEL` explicitly selects a chat-completions-compatible model in the account catalog; when omitted, the backend discovers the live model catalog and selects from recognized general-purpose text families, excluding audio and guard models. The project secret flow keeps both API keys server-side.

Run the API and frontend in separate terminals:

```bash
PYTHONPATH=backend VERITY_DB_PATH=data/verity.sqlite uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
pnpm dev
```

The Vite server listens on port 3000 and proxies `/api/*` and `/health` to FastAPI at port 8000. API reference: `/api/docs`; health: `/health`.

## Verification behavior

`POST /api/verify` creates a report record and returns its ID with processing status. The client polls `GET /api/report/{report_id}`; the report's stage statuses are persisted as the backend progresses. The pipeline extracts claims, searches Tavily, optionally extracts page content, asks Groq to assess evidence, and generates a correction. Report status and provider errors are explicit. An absent source/date is not guessed, and a generated citation is made clickable only if its source ID resolves to a Tavily-returned source. Confidence is an ordinal evidence assessment; an internal ranking supports sorting and is not presented as a scientific probability.

Report routes are `GET /api/history`, `GET /api/report/{report_id}`, `DELETE /api/report/{report_id}` and `POST /api/correct`; extraction is available at `POST /api/extract-claims`. Input is limited to 12,000 characters.

## Persistence and deployment

The application currently uses SQLite, as requested for the initial version; data is stored at `VERITY_DB_PATH` (default `data/verity.sqlite`) behind a repository boundary. The development workspace retains the local SQLite file. **The published server container's filesystem is ephemeral; the SQLite file is not a durable production store across container replacement.** Before relying on production history, migrate the repository to durable managed storage/database. The container serves the Vite production build from FastAPI on `PORT` (default 3000) and exposes `/health` as an unauthenticated readiness path.

Build locally with `docker build -t verity-ai .` and run with provider credentials in the environment (never in the image):

```bash
docker run --rm -p 3000:3000 -e GROQ_API_KEY -e TAVILY_API_KEY verity-ai
```

## Tests and benchmark

```bash
pip install -r backend/requirements-dev.txt
PYTHONPATH=backend pytest -q
python evaluation/evaluate.py --predictions evaluation/predictions.example.json
```

`evaluation/benchmark.json` contains 50 manually labelled, task-scoped example claims across stable, current, stale, contradicted, unsupported and conflicting labels, using 2026-11-13 as the reference date for time-sensitive labels. Treat these as an evaluation fixture rather than live user-facing results. The evaluation script reports accuracy, per-class precision/recall/F1, macro F1, average latency and cost from supplied prediction records; it can compare the same metrics with a baseline JSON file. No measured score or provider cost is claimed until real predictions are supplied.

To generate an optional LLM-only comparison, run `PYTHONPATH=backend python evaluation/run_llm_only_baseline.py`; this makes one sequential Groq request per benchmark claim and does not use Tavily. Compare generated baseline predictions with the application predictions using `python evaluation/evaluate.py --predictions path/to/verity-predictions.json --baseline evaluation/llm-only-predictions.json`. Cost remains unreported unless measured `cost_usd` values are supplied; the benchmark runner never assumes cost is zero.

## Limitations

- Web evidence quality depends on source coverage and provider responses; model verdicts should not replace independent judgment.
- Freshness and confidence are separate fields; publication age alone does not establish stale content.
- SQLite is suitable for the initial prototype, but not a durable multi-instance production database in the ephemeral container.
- This prototype has no user accounts or per-user report access controls; keep it in a private Preview until access control and durable production storage are added.
- The illustrative report preview on the landing page is clearly labelled and is not a fabricated verification.


## Before public launch

The footer's GitHub link currently opens the general GitHub site, and the contact email uses the reserved `.example` placeholder because no project repository URL or contact address was supplied. Replace both with project-specific destinations before publishing. Full benchmark metric collection and the measured LLM-only comparison are not yet run; the benchmark fixture and scripts are provided, but no unmeasured results are claimed.


For local development, copy `.env.example` to `.env` at the repository root and fill in the provider keys there; the backend loads it with `python-dotenv`. Never commit `.env` or paste those values into React/browser code. Hosted project credentials remain in protected server-side settings.
