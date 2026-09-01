# Syllabus Calendar Project

A web app that turns a syllabus PDF into Google Calendar events and Google Tasks. It is
deployed and live: Docker Compose on a VPS behind an HTTPS reverse proxy, with per-user
Postgres-backed sessions and a Redis/arq worker so `/upload-syllabus` returns a `job_id`
immediately instead of blocking on OpenAI. The API contract described below (request/
response shapes) is stable and should not change unless a step specifically requires it.

### No Google-connection status endpoint

There is deliberately no "is Google connected" status endpoint: the frontend never checks
connection state up front. It just calls `/add-events`; a 401 (`not_authenticated`)
triggers the `/auth/google` popup automatically, and success retries the same call. That
401 check doubles as the connection check, so a separate status endpoint would have no
consumer.

## User flow (this is what the UI must support end to end)

1. User lands on the site.
2. User uploads a syllabus PDF.
3. User clicks an "upload"/"process" button, which sends the file to the backend
   (`POST /upload-syllabus`, multipart form with a `file` field, PDF or DOCX). The route
   validates the file, creates a `jobs` row, and enqueues the extraction as an arq job,
   returning `{"job_id": ...}` immediately rather than blocking on OpenAI.
4. The frontend polls `GET /jobs/{job_id}` (every couple seconds) until `status` is
   `"done"` (structured JSON matching the shape in `backend/format.json`, see below) or
   `"failed"`. Real syllabus PDF calls can take from several seconds to well over a
   minute — the UI must show a clear loading/processing state for the whole poll, not
   just a spinner with no feedback that something is still happening.
5. User reviews the returned data: class schedule, one-off calendar events, tasks,
   readings, cancellations, plus `missing_information` and `warnings`. User can edit
   names/dates/times, remove items they don't want, and (eventually) add new items.
6. User clicks "Add to Calendar". The (possibly edited) JSON is sent back to the backend
   (`POST /add-events`, JSON body = the same document shape) which creates the events/
   tasks in the user's Google Calendar and Google Tasks.
7. Before step 6 can succeed the user must have connected their Google account. This is
   handled reactively, not with an upfront status check: if `/add-events` returns 401
   (`not_authenticated`), the frontend opens `GET /auth/google` in a popup, which runs
   the OAuth flow, upserts the `users`/`google_tokens` rows, and posts a
   `google-auth-success` message back to the opener before closing itself; the opener's
   listener then retries the same `/add-events` call with the pending payload.

## Architecture

- `frontend/` — Vite + React 19 (JSX, not TypeScript despite `tsc` in the `dev`/`build`
  scripts — there is currently no actual TS source). API calls use relative URLs,
  proxied to the backend by Vite's dev server (`server.proxy` in `vite.config.js`) so
  the browser only ever talks to its own origin — see "Conventions / gotchas" below for
  why that matters for the session cookie.
- `backend/` — FastAPI, as an `app/` package (`backend/main.py` is a thin entrypoint,
  `from app.main import app`, kept only so `uvicorn main:app --reload` from `backend/`
  with the venv active still works as documented). One module per route group under
  `app/routers/`, the logic they call into under `app/services/`, and the Pydantic models
  in `app/schemas/extraction.py`. Uses OpenAI (model set by the `OPENAI_MODEL` env var)
  with Structured Outputs to extract data from the uploaded syllabus, and the Google
  Calendar/Tasks APIs to write events. CORS allows any `localhost`/`127.0.0.1` port in
  the 5170–5179 range, since Vite moves ports when 5173 is taken.
- The `SyllabusExtraction` Pydantic model in `app/schemas/extraction.py` **is** the data
  model — Structured Outputs guarantees the response matches it, so the schema is the
  contract, not something the prompt has to enforce. `backend/format.json` is a real
  example of that same shape, which `/add-events` accepts back. Top-level keys: `course`,
  `class_schedule` (recurring meetings), `class_cancellations`, `events`, `tasks`,
  `readings`, `missing_information`, `warnings`. Every extracted item carries a
  `confidence` (`high`/`medium`/`low`) and a `source_text` snippet — these are worth
  surfacing in the UI so users know what to double check.

### Why `events` and `tasks` rather than finer categories

The split is on **destination**, not vocabulary: `events` occupy a block of time and go
to Google Calendar; `tasks` have a deadline and go to Google Tasks. That is a structural
question the model answers reliably. Finer distinctions live in the `event_type` and
`task_type` enums, which Structured Outputs constrains to valid values for free.

This was tried the other way round (separate `tests`/`assignments`/`projects` arrays) and
reverted: choosing an array is an irreversible routing decision made before any content
is written, and "is a lab report a project or an assignment?" has no correct answer. Add
new distinctions as enum values, not as new top-level arrays.

Two consequences worth knowing:
- **Review tabs are filters, not arrays.** `TAB_CONFIG` in `ReviewModal.jsx` maps each
  tab to a `path` plus a `match` predicate, so Tests / Other Events / Assignments /
  Projects can be separate tabs over two arrays. Predicates sharing a path must stay
  complementary — an item no tab matches is unreachable for review but still synced.
- **Per-field guidance belongs in `Field(description=...)`**, not the prompt. Those
  descriptions ship to the model inside the schema. The prompt covers only which bucket
  an item belongs in; date formats, week-range inference, and `source_text` rules sit on
  the fields themselves.

Course codes are prefixed onto every title (`"CSC 242: Midterm 1"`) by `titled()` in
`app/services/titling.py`, not by the model — so it applies uniformly and cannot drift
with phrasing. The model is told to return bare titles.

## Conventions / gotchas

- The app's public URLs are env-driven, not hardcoded, via `app/config.py`:
  `ENVIRONMENT` (default `"development"`; anything else, including `"staging"`, is
  treated like production for security-relevant defaults — only `"development"` gets
  the insecure/local ones), `BACKEND_BASE_URL`, and `FRONTEND_BASE_URL`. These build the
  OAuth `redirect_uri`, the `CORS_ORIGIN_REGEX` default (an exact match on
  `FRONTEND_BASE_URL` outside development, the broad `5170-5179` localhost range inside
  it), and the `postMessage` origin checks between the OAuth popup and its opener on
  both sides — the backend side reads `FRONTEND_BASE_URL`, the frontend side reads its
  own `VITE_BACKEND_ORIGIN` from `frontend/.env` (a separate var since Vite bakes
  `VITE_`-prefixed vars in at build time, not runtime).
- Dates are `YYYY-MM-DD`, times are 24-hour `HH:MM`, both may be `null` when the source
  PDF didn't specify them — the UI needs to handle nulls gracefully (e.g. all-day
  events, tasks with no due time).
- `days_of_week` on recurring meetings is always full day names (`"Monday"`, not `"M"`).
- Secrets/credentials live in `backend/.env` and `backend/credentials.json` — never print
  or commit their contents. `DATABASE_URL` also comes from `.env` (falls back to the
  local `syllabus-postgres` container's credentials if unset).
