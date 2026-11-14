# Verity AI — Implementation Plan

## Product and architecture

Build a responsive, editorial AI-verification product with a React/Vite/Tailwind frontend and a modular FastAPI backend. The browser calls same-origin API routes; the backend owns Groq and Tavily calls, schema validation, evidence processing, report persistence, PDF export, and provider error handling. Use environment-injected `GROQ_API_KEY` and `TAVILY_API_KEY`, never frontend variables or checked-in credentials. Select the available Groq model through runtime configuration rather than hardcoding a model identifier. Implement SQLite initially behind a repository boundary that can later support PostgreSQL. Managed server capability is necessary for protected provider credentials and API routes; use the requested SQLite implementation for application reports.

### Verification flow

1. Validate request text and extract independently verifiable factual claims with Groq. Split compound facts, preserve meaning, avoid adding facts, assign the requested category and temporal sensitivity, and create a targeted search query per claim.
2. Search Tavily for relevant preferably authoritative sources; retain returned title, URL, snippet/content, relevance and available dates. Extract page text only when useful. De-duplicate redundant searches where practical.
3. Ask Groq to evaluate each claim against retrieved evidence, returning source-linked support, contradiction, disagreement or insufficiency in structured output validated by Pydantic.
4. Classify CURRENT, STALE, CONTRADICTED, UNSUPPORTED, CONFLICTING or STABLE. Keep freshness separate from confidence; do not infer staleness merely from old publication dates or manufacture scientific certainty percentages.
5. Produce an evidence-grounded corrected answer with citations; do not invent sources, dates or unsupported facts.
6. Persist completed reports in SQLite and expose history/report retrieval, deletion and correction routes.

Expose `POST /api/extract-claims`, `POST /api/verify`, `POST /api/correct`, `GET /api/history`, `GET /api/report/{report_id}`, `DELETE /api/report/{report_id}`, and unauthenticated `GET /health`. Use timeouts, asynchronous I/O where appropriate, validation and actionable errors.

## Project structure

- `frontend/`: Vite React application, routes/pages, reusable components, API client, UI state, styles and frontend dependencies.
- `backend/app/main.py`: FastAPI setup, health check, routing and application lifecycle.
- `backend/app/routes/`: extraction, verification, correction and report history endpoints.
- `backend/app/services/`: Groq client/model discovery/configuration, Tavily search/extraction, claim/evidence analysis, freshness/confidence assessment and corrected-answer assembly.
- `backend/app/models/`: Pydantic request/response and persisted domain schemas.
- `backend/app/database/`: SQLite connection, schema/migrations and repository boundary.
- `evaluation/`: manually labelled benchmark fixture and metric/baseline evaluation harness.
- `docs/`: architecture, credential setup, development and deployment documentation.
- Root `Dockerfile`, `.gitignore`, README, lockfiles and runtime configuration: reproducible development and production entrypoints.

## Design direction

### Design Movement
Neo-Brutalist editorial intelligence: an investigative publication crossed with a working research instrument.

### Core Principles
- Evidence-first: source material and uncertainty remain visible beside verdicts.
- Tactile clarity: strong ink borders, hard shadows and concise labels make controls legible.
- Editorial asymmetry: layouts emphasize claims and reports rather than repeating generic dashboard cards.
- Honest motion: animation reflects actual request state and never implies work has completed prematurely.

### Color Philosophy
Warm paper cream `#F4F0E6` gives the experience a document-like base; near-black `#171717` anchors legibility; electric vermilion `#FF613D` marks investigation and urgency; acid lime `#D9F05A` signals supported/current findings. White panels, muted grey metadata, and distinct yellow/red/blue status treatments distinguish unsupported, contradicted and conflicting claims.

### Layout Paradigm
An asymmetric editorial canvas: oversized landing headline, broad input document offset against a narrow numbered investigation index, then varied-width evidence and feature compositions. Reports use a precise split investigation view rather than a centered SaaS dashboard grid.

### Signature Elements
- Oversized section numbers and IBM Plex Mono investigation/source identifiers.
- Thick black rules and offset black shadows on primary actions and selected panels.
- Vermilion claim marks with lime/blue/yellow verdict tabs.

### Interaction Philosophy
Direct, tactile controls; claims and source cards are actionable; filters and sorting expose the evidence instead of hiding it. The interface distinguishes retrieved evidence from model-authored explanations and gives clear uncertainty states.

### Animation
Use short, purposeful transitions for hover/press, claim selection, panel expansion and report reveal. An investigation timeline advances only as real request stages are observed. Use restrained progress movement and respect reduced-motion preferences; avoid glow, bounce and decorative motion.

### Typography System
Space Grotesk bold for uppercase editorial headlines, Inter for readable long-form body copy, and IBM Plex Mono for identifiers, timestamps, counts and technical metadata. Use compact supporting labels and generous headline scale.

### Brand Essence
An independent fact-and-freshness investigator for anyone relying on AI-generated answers; precise, skeptical, transparent.

### Brand Voice
Headlines are blunt questions; actions are direct; uncertainty is stated plainly. Examples: “AI CAN BE CONFIDENT. BUT IS IT CORRECT?” and “A source is not proof. Open the evidence.”

### Wordmark & Logo
A custom typographic VERITY wordmark paired with a small black-and-vermilion split-check/inspection mark, treated as a stamp rather than a default text logo.

### Signature Brand Color
Electric vermilion `#FF613D`.

## UX scope

Implement the landing page and all requested product destinations: verification workspace, results report, evidence explorer, history, About/How it Works, and Settings. Provide responsive desktop/mobile navigation without horizontal overflow. Landing includes the VERITY identity and requested tagline/headline, 12,000-character input with count/paste/clear/sample/investigate controls, 01 EXTRACT / 02 VERIFY / 03 CORRECT index, how-it-works, six named features, a clearly labelled report preview, transparency, final CTA and footer. Workspace has honest loading/progress/empty/error states and calls the backend. Results show report ID and verdict metrics, inline claim highlights, claim filters, sorting, selectable investigation detail, freshness/confidence, evidence/source dates and corrected-answer comparison/copy action. Evidence Explorer shows query, source domain/title/URL/excerpt/available dates and support classification with expandable comparisons and safe new-tab links. History supports search/filter/sort, reopen, confirmed deletion and PDF export. Include copy report link only where backed by a real route.

## Dependencies and serving

Pin Node/package-manager versions and commit lockfiles plus reviewed lifecycle-script policy before installing packages. Use the requested React/Vite/Tailwind/React Router/Lucide/Recharts/Axios choices and Python FastAPI/Uvicorn/Pydantic/Groq/Tavily/python-dotenv stack. Serve frontend and API through the FastAPI container in production, with a development setup that supports Vite and FastAPI. Runtime reads private credentials only from the environment. Persist reports through the SQLite repository for the initial implementation. Add a Dockerfile that installs dependencies, builds the frontend and starts the FastAPI listener honoring `PORT` (default 3000), with a public health endpoint. Keep a synchronized route manifest for website pages.

## Testing and documentation

Add pytest/HTTPX tests for API and freshness/confidence behavior, plus frontend checks where practical. Include an approximately 50–100 item manually labelled benchmark spanning current, stale, historical, contradicted, unsupported and conflicting claims, and evaluation of precision, recall, F1, accuracy, average latency and cost against a simple LLM-only baseline. Document setup, environment variables, architecture, limitations and deployment in README/docs. No real verification report may be fabricated; any preview sample must be explicitly marked as an illustrative example.