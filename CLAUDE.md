# Syllabus Calendar Project

A web app that turns a syllabus PDF into Google Calendar events and Google Tasks. The
frontend was already rebuilt into something clean, professional, and aesthetic. The
current focus is deploying the app (VPS + Docker Compose, targeting up to ~100
concurrent users): moving off the single-file `token.json` OAuth storage to per-user
Postgres-backed sessions, moving the synchronous OpenAI call onto a Redis/arq background
worker so `/upload-syllabus` returns a `job_id` immediately, and containerizing the
whole stack behind an HTTPS reverse proxy. The API contract described below (request/
response shapes) is stable and should not change as part of this work unless a step
specifically requires it.

## User flow (this is what the UI must support end to end)

1. User lands on the site.
2. User uploads a syllabus PDF.
3. User clicks an "upload"/"process" button, which sends the file to the backend
   (`POST /upload-syllabus`, multipart form with a `file` field, PDF only).
4. Backend runs the PDF through OpenAI and returns structured JSON matching the shape
   in `backend/format.json` (see below). This can take a while (real syllabus PDF calls
   can take from several seconds to well over a minute) — the UI must show a clear
   loading/processing state, not just a spinner with no feedback that something is
   still happening.
5. User reviews the returned data: class schedule, one-off calendar events, tasks,
   readings, cancellations, plus `missing_information` and `warnings`. User can edit
   names/dates/times, remove items they don't want, and (eventually) add new items.
6. User clicks "Add to Calendar". The (possibly edited) JSON is sent back to the backend
   (`POST /add-events`, JSON body = the same document shape) which creates the events/
   tasks in the user's Google Calendar and Google Tasks.
7. Before step 6 can succeed the user must have connected their Google account
   (`GET /auth/google` opens a popup OAuth flow; backend stores `token.json` and the
   popup posts a `google-auth-success` message back to the opener, then closes itself).
   The UI should make it obvious whether Google is connected yet.

## Architecture

- `frontend/` — Vite + React 19 (JSX, not TypeScript despite `tsc` in the `dev`/`build`
  scripts — there is currently no actual TS source). Talks to the backend at
  `http://localhost:8000` (hardcoded absolute URLs today).
- `backend/` — FastAPI, as an `app/` package (`backend/main.py` is a thin entrypoint,
  `from app.main import app`, kept only so `uvicorn main:app --reload` from `backend/`
  with the venv active still works as documented). Layout: `app/main.py` builds the
  `FastAPI()` instance, sets up CORS, and registers routers; `app/config.py` holds env
  vars and `.env` loading; `app/routers/` has one module per route group (`health`,
  `auth`, `syllabus`, `events`); `app/services/` holds the logic each router calls into
  (`dedupe.py`, `titling.py`, `document_parsing.py`, `openai_extraction.py`,
  `google_sync.py`); `app/schemas/extraction.py` holds the Pydantic models. Uses OpenAI
  (model set by the `OPENAI_MODEL` env var) with Structured Outputs to extract data from
  the uploaded syllabus, and the Google Calendar/Tasks APIs to write events. CORS allows
  any `localhost`/`127.0.0.1` port in the 5170–5179 range, since Vite moves ports when
  5173 is taken.
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

## Frontend layout

The prototype has been replaced. `App.jsx` is now a thin shell composing `MouseTrail`,
`Header`, `HowItWorks`, and `SyllabusUploader`. Tailwind v4 is wired up via
`@tailwindcss/vite` in `vite.config.js` and `@import "tailwindcss"` in `index.css`
(there is no `App.css` and no `tailwind.config.js` — v4 configures via `@theme` in CSS).

- `SyllabusUploader.jsx` owns the whole flow: file select/drag, the `POST` to
  `/upload-syllabus`, the `UploadingScreen` while it runs, and then `ReviewModal`. It
  also adds a `_key` to every item on arrival (`withStableKeys`) because backend items
  have no stable id and React reuses components across removals without one. `_key` is
  stripped before the payload goes back to `/add-events`.
- `components/review/` holds the editing UI: `ReviewModal` drives a select → per-tab
  review → color-pick → confirm sequence, and delegates rows to `ClassScheduleTab`,
  `EventsTab` (one-off, date + time range + location), and `DueItemsTab` (deadline
  only). The latter two are generic over `path`/`indices`/`blankItem`, which is what
  lets several tabs share one array.

## Conventions / gotchas

- Backend base URL is hardcoded as `http://localhost:8000` in the frontend; the backend
  accepts any localhost port in 5170–5179 — keep both in sync if ports change.
- Dates are `YYYY-MM-DD`, times are 24-hour `HH:MM`, both may be `null` when the source
  PDF didn't specify them — the UI needs to handle nulls gracefully (e.g. all-day
  events, tasks with no due time).
- `days_of_week` on recurring meetings is always full day names (`"Monday"`, not `"M"`).
- Secrets/credentials live in `backend/.env`, `backend/credentials.json`,
  `backend/token.json` — never print or commit their contents.
