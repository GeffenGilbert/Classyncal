# Frontend

Vite + React 19 (JSX, not TypeScript despite `tsc` in the `dev`/`build` scripts — there
is currently no actual TS source). API calls use relative URLs, proxied to the backend by
Vite's dev server (`server.proxy` in `vite.config.js`) so the browser only ever talks to
its own origin — see "Conventions / gotchas" in the root `CLAUDE.md` for why that matters
for the session cookie.

Tailwind v4 is wired up via `@tailwindcss/vite` in `vite.config.js` and
`@import "tailwindcss"` in `index.css` (there is no `App.css` and no `tailwind.config.js`
— v4 configures via `@theme` in CSS).

## Layout

`App.jsx` is a thin shell composing `MouseTrail`, `Header`, `HowItWorks`, and
`SyllabusUploader`.

- `SyllabusUploader.jsx` owns the whole flow: file select/drag, the `POST` to
  `/upload-syllabus`, then `pollJobStatus()` calling `GET /jobs/{job_id}` on an interval
  (capped at `JOB_POLL_MAX_ATTEMPTS` so a stuck job surfaces an error instead of polling
  forever) until the job is `done` or `failed`, showing `UploadingScreen` the whole time,
  and then `ReviewModal`. It also adds a `_key` to every item on arrival
  (`withStableKeys`) because backend items have no stable id and React reuses components
  across removals without one. `_key` is stripped before the payload goes back to
  `/add-events`.
- `components/review/` holds the editing UI: `ReviewModal` drives a select → per-tab
  review → color-pick → confirm sequence, and delegates rows to `ClassScheduleTab`,
  `EventsTab` (one-off, date + time range + location), and `DueItemsTab` (deadline
  only). The latter two are generic over `path`/`indices`/`blankItem`, which is what
  lets several tabs share one array.

## Gotchas

- Dark mode uses `@custom-variant dark (&:where(.dark, .dark *))`. `:where()` contributes
  **zero specificity**, so a `dark:` utility ties with a plain one and wins only on source
  order — a `dark:` variant of a property already set later in the sheet needs restating
  (see `UploadingScreen.jsx`'s spinner border).
- Light is the default. Dark is opt-in through the toggle and is never inferred from the
  OS; only an explicit stored choice turns it on.
