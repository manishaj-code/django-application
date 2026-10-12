# Implementation Plan

Phases follow `start.md` §8. Each phase ends with commands run and results
checked before moving on. Status is updated as work completes (✅ = done and verified).

## Phase 1 — ✅ Foundation
- Reuse existing venv `myenv` (Python 3.13.5).
- `requirements.txt` (runtime) and `requirements-dev.txt` (tests), pinned.
- Django project `config/` with env-driven `settings.py`, `test_settings.py`.
- `.env.example` (placeholders), local `.env` (git-ignored), `.gitignore`.
- Local PostgreSQL database `django_cms` + least-privilege role `django_cms_user`
  (`scripts/setup_local_db.py`).
- Verify: `manage.py check`, DB connection, dev server responds.

## Phase 2 — ✅ Data model and admin
- `accounts.User`, `content.Category`, `content.Content`, `core.ContactMessage`.
- Slug generation, constraints, indexes, upload validators.
- Admin: list displays, filters, search, date hierarchy, publish/unpublish
  actions, read-only timestamps, image preview, `created_by` auto-set.
- Editors group created on `post_migrate`.
- Verify: `makemigrations --check`, `migrate` on PostgreSQL.

## Phase 3 — ✅ Authentication
- Registration (no privilege fields), login/logout, password change/reset,
  profile + edit, rate limiting, sensitive-parameter masking.
- Console email backend in development.

## Phase 4 — ✅ Frontend
- `base.html` + partials (navbar, footer, messages, pagination, content card,
  form field); pages for every view; error pages 403/404/429/500/CSRF.
- Vendored Bootstrap 5.3, small `site.css`/`site.js`; no inline JS/CSS (CSP).

## Phase 5 — ✅ Tests
- pytest suites for every item in `start.md` §5; run against SQLite and
  PostgreSQL; `check --deploy` with production env.

## Phase 6 — ✅ Deployment
- Production security settings, `gunicorn.conf.py`, `Dockerfile`,
  `docker-entrypoint.sh`, `compose.yaml` (postgres + web + nginx),
  `/healthz/`, logging, backup/restore scripts guidance.

## Phase 7 — ✅ Documentation
- `README.md`, `ADMIN_GUIDE.md`, `docs/DEPLOYMENT.md` with checklist and
  handover notes.
