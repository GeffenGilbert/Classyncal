# Backend

FastAPI as an `app/` package. `backend/main.py` is a thin entrypoint (`from app.main
import app`), kept only so `uvicorn main:app --reload` from `backend/` with the venv
active still works as documented.

## Database layer

Local dev Postgres runs as a Docker container (`syllabus-postgres`, image `postgres:16`,
port 5432, database/user/password all `syllabus`), with a named volume
(`syllabus-postgres-data`) so data survives container restarts — start it with
`docker start syllabus-postgres` if it's not running. `app/db/base.py` has the
SQLAlchemy `engine`, `SessionLocal` factory, `Base` (the declarative base every model
inherits from, and what Alembic reads via `Base.metadata`), and `get_db()`, a generator-
based FastAPI dependency that yields a session and closes it in a `finally` block after
the request completes.

`app/db/models.py` — four tables, all in one file (not a folder-per-model; not worth the
split at this size, and a folder means every model needs an explicit re-import somewhere
or Alembic's autogenerate silently misses it):
- `users` — `user_id` (PK), `google_sub` (unique — the real stable identity from
  Google's ID token, looked up on every login; never a self-generated id), `created_at`.
  No `email` column — nothing in the app reads it, so it isn't stored.
- `google_tokens` — `token_id` (PK), `user_id` (FK, unique — one row per user, updated
  in place on refresh, never accumulated), `access_token`, `refresh_token`,
  `expires_at`, `updated_at`.
- `sessions` — `session_id` (PK, the actual browser cookie value), `user_id` (FK,
  nullable — a session exists *before* login, to carry state across the redirect to
  Google and back), `oauth_state` (nullable, CSRF value for an in-flight login),
  `created_at`, `expires_at`.
- `jobs` — `job_id` (PK, UUID — exposed in a polling URL, so it must not be sequential/
  guessable), `session_id` (FK to `sessions`, **not** `users`, since uploading and
  processing a syllabus never requires being logged in — only "Add to Calendar" does),
  `status` (plain string, not a Postgres enum, so adding a new status later doesn't need
  its own migration), `result_json`, `created_at`, `updated_at`.

All timestamp columns are `DateTime(timezone=True)` — compare against
`datetime.now(timezone.utc)`, never naive `datetime.now()`/`utcnow()`.

Migrations live in `alembic/` (config in `alembic.ini`); `alembic/env.py` is wired to
import `app.db.models` (so every model registers on `Base.metadata` before autogenerate
runs) and pulls the connection string from `app.config.DATABASE_URL` rather than
duplicating it in `alembic.ini`.

## Gotchas

- `SessionCookieMiddleware` (`app/services/session.py`) exists so a fresh session's
  cookie survives routes that return a `Response` subclass directly instead of a plain
  value — without it those routes drop the cookie.
- `extract_syllabus()` in `app/services/openai_extraction.py` is `async` (via
  `AsyncOpenAI`) so multiple users' extractions run concurrently on one worker process
  rather than serializing. Keep it async.
- Expired `sessions` rows and old `jobs` rows aren't left to accumulate:
  `app/services/cleanup.py` (`cleanup_expired_sessions`, `cleanup_old_jobs`) is
  registered as hourly `cron_jobs` on `WorkerSettings` in `app/worker.py`, so it runs
  inside the worker process with no OS-level scheduling. `cleanup_expired_sessions`
  deletes an expired session's `jobs` rows *before* the session itself, since
  `jobs.session_id` is a FK with no `ON DELETE` behaviour and would otherwise block the
  delete. A synchronous check-on-every-request isn't worth it — most expired sessions
  belong to visitors who never come back to trigger one.
- `app.db.models.Session` (a browser session row) and `sqlalchemy.orm.Session` (a
  database session/connection) are unrelated classes with the same name — files that
  need both import one under an alias (`from app.db.models import Session as
  BrowserSession`, `from sqlalchemy.orm import Session as DBSession`).
