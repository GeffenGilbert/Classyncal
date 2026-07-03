# Syllabus Calendar Project

A web app that turns a syllabus PDF into Google Calendar events and Google Tasks. The
current session's focus is rebuilding the frontend into something clean, professional,
and aesthetic — the backend flow and API contract are already working and should be
treated as stable unless a frontend change requires a small backend adjustment.

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
- `backend/` — FastAPI (`backend/main.py`), single file. Uses OpenAI (`gpt-5-mini`) to
  extract structured data from the uploaded PDF, and the Google Calendar/Tasks APIs to
  write events. Run via `uvicorn main:app --reload` from `backend/` with the venv active
  (see comment at top of `main.py`). CORS is currently locked to
  `http://localhost:5173`.
- `backend/format.json` is a real example of the JSON shape the backend returns from
  `/upload-syllabus` and expects back for `/add-events` — treat it as the source of
  truth for the data model. Top-level keys: `course`, `class_schedule` (recurring
  meetings), `class_cancellations`, `calendar_events` (exams/quizzes/etc, one-off),
  `tasks` (homework/assignments/projects), `readings`, `missing_information`,
  `warnings`. Every extracted item carries a `confidence` (`high`/`medium`/`low`) and a
  `source_text` snippet — these are worth surfacing in the UI so users know what to
  double check.

## Frontend state today

`frontend/src/App.jsx` is a single-component, functionality-only prototype (inline
styles, no componentization, no styling system wired up) — this is what we're
replacing. Notable existing behavior worth preserving as we rebuild:
- File select → `uploadFile()` → stores the raw backend JSON in `backendMessage` state.
- `connectGoogle()` opens the OAuth popup and listens for the `google-auth-success`
  `postMessage`.
- `addEvents()` POSTs `backendMessage` back to `/add-events`.
- `DisplayClassSchedule` / `DisplayTasks` are minimal read-only renderers — no editing,
  no removal, no support for `calendar_events`/`readings`/`class_cancellations` yet.

Styling/UI dependencies already installed in `frontend/package.json` but **not yet wired
up**: `tailwindcss` + `@tailwindcss/vite`, `@base-ui/react`, `shadcn`, `lucide-react`,
`class-variance-authority`, `tailwind-merge`, `tw-animate-css`. `vite.config.js` has no
Tailwind plugin yet and `index.css`/`App.css` are still the default Vite template
styles/animation (`App.css`'s `.hero` rotation is unused boilerplate). Setting up
Tailwind + shadcn is likely one of the first steps in rebuilding the UI.

## Conventions / gotchas

- Backend base URL is hardcoded as `http://localhost:8000` in the frontend and CORS on
  the backend only allows `http://localhost:5173` — keep both in sync if ports change.
- Dates are `YYYY-MM-DD`, times are 24-hour `HH:MM`, both may be `null` when the source
  PDF didn't specify them — the UI needs to handle nulls gracefully (e.g. all-day
  events, tasks with no due time).
- `days_of_week` on recurring meetings is always full day names (`"Monday"`, not `"M"`).
- Secrets/credentials live in `backend/.env`, `backend/credentials.json`,
  `backend/token.json` — never print or commit their contents.
