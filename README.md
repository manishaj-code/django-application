# Django CMS

A small, maintainable content-management website built with Django. Staff
publish content (articles, news, pages) through the Django admin. Visitors
browse it on a responsive public site and can create an account and use the
contact form.

- **Public site:** home, content listing with search, category filter and
  pagination, content detail pages, about page, contact form, and custom
  400/403/404/429/500 pages.
- **Accounts:** registration, sign-in/out, password change and reset by email,
  profile page, and rate limiting on sensitive forms.
- **Admin CMS:** create/edit/delete/publish/unpublish/schedule content,
  categories, image uploads, contact messages, users and permissions. An
  **Editors** group is created automatically.
- **Production:** PostgreSQL, Gunicorn, WhiteNoise, security headers, a
  health check, Docker image and Compose stack.

More documents:

- [docs/SPEC.md](docs/SPEC.md) — specification and assumptions
- [docs/PLAN.md](docs/PLAN.md) — implementation plan
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — deployment, backups, checklist and handover
- [ADMIN_GUIDE.md](ADMIN_GUIDE.md) — guide for site administrators

---

## Technology stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 (3.12 also supported) |
| Framework | Django 5.2 LTS |
| Database | PostgreSQL 14+ (developed on 18), driver psycopg 3 |
| Frontend | Django templates, Bootstrap 5.3 (bundled locally), a little vanilla JS |
| Static files | WhiteNoise |
| App server | Gunicorn (Linux / containers) |
| Tests | pytest + pytest-django |
| Containers | Docker, Docker Compose, nginx |

## Project layout

```
config/            settings.py, test_settings.py, urls.py, wsgi.py, asgi.py
accounts/          custom User model, registration, profile, auth views
content/           Category & Content models, admin, public views, demo-data command
core/              home/about/contact, health check, error pages, rate limiter, CSP middleware
templates/         base.html, partials/, registration/, accounts/, content/, errors/
static/            css/, js/, images/, vendor/bootstrap/
tests/             pytest test suite
scripts/           setup_local_db.py
deploy/            nginx.conf
Dockerfile, compose.yaml, docker-entrypoint.sh, gunicorn.conf.py
requirements.txt, requirements-dev.txt, .env.example, .env.docker.example
```

---

## Local installation (Windows, macOS, Linux)

### 1. Prerequisites

- Python 3.12 or 3.13: `python --version`
- PostgreSQL 14 or newer, installed and running
- Git

### 2. Virtual environment

```bash
python -m venv myenv
# Windows (PowerShell):  .\myenv\Scripts\Activate.ps1
# macOS / Linux:         source myenv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements-dev.txt     # includes test tools
# production servers only need:  pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Edit `.env` for local development:

```ini
DEBUG=True
SECRET_KEY=<generate one, see below>
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=django_cms
DB_USER=django_cms_user
DB_PASSWORD=<choose a strong password>
DB_HOST=localhost
DB_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

`.env` is git-ignored. Never commit it. Every setting is documented in
[.env.example](.env.example).

### 5. Create the PostgreSQL database and user

**Option A, the helper script.** It reads `DB_*` from `.env` and asks for the
`postgres` superuser password:

```bash
python scripts/setup_local_db.py
```

**Option B, by hand in `psql`.** Connect as the superuser (`psql -U postgres`)
and run:

```sql
CREATE ROLE django_cms_user LOGIN PASSWORD 'your-password' NOSUPERUSER NOCREATEROLE CREATEDB;
CREATE DATABASE django_cms OWNER django_cms_user ENCODING 'UTF8' TEMPLATE template0;
REVOKE CONNECT, TEMPORARY ON DATABASE django_cms FROM PUBLIC;
```

The app role owns only its own database and is not a superuser. `CREATEDB`
is there only so the test suite can create a temporary test database. Leave
it off in production.

### 6. Migrations, cache table and superuser

```bash
python manage.py migrate
python manage.py createcachetable      # needed by the rate limiter
python manage.py createsuperuser       # your admin account
python manage.py seed_demo_content     # optional: 15 sample items in 3 categories
```

### 7. Run the development server

```bash
python manage.py runserver
```

- Site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Health check: http://127.0.0.1:8000/healthz/

If port 8000 is already taken (for example by a Docker container), use
another one: `python manage.py runserver 8765`.

**Password-reset emails in development:** with the console email backend,
reset emails (including the link) are printed in the terminal running
`runserver`. To save them as files instead, set
`EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend`; they will
be written to `sent_emails/`.

---

## Running tests

```bash
pytest                         # fast: in-memory SQLite, no DB server needed
```

To run the same suite against PostgreSQL (needs the `CREATEDB` privilege):

```bash
# PowerShell:  $env:TEST_DATABASE="postgres"; pytest
TEST_DATABASE=postgres pytest
```

Other checks:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run    # no missing migrations
DEBUG=False python manage.py check --deploy          # production checklist
```

The tests cover registration, login/logout, password reset and change,
profiles, access control, admin CRUD and publish/unpublish actions,
categories, slug uniqueness, database constraints, image validation,
pagination, search, error pages, CSRF, rate limiting, security headers and
production defaults.

---

## Creating and managing content

All content is managed in the admin at `/admin/`. See
[ADMIN_GUIDE.md](ADMIN_GUIDE.md) for step-by-step instructions. In short:

1. Sign in at `/admin/` with a staff account.
2. **Content → Categories → Add** to create categories.
3. **Content → Content → Add** to write an item. Leave *Slug* empty to
   generate it from the title.
4. Set **Status** to *Published* and save. The publication date is filled in
   automatically. A future date schedules the item.
5. To give someone editing rights, tick **Staff status** on their user and
   add them to the **Editors** group.

The body is plain text: a blank line starts a new paragraph. HTML is shown
as text, not executed, so editors cannot inject scripts.

---

## Static files

```bash
python manage.py collectstatic --noinput
```

This collects files into `staticfiles/`. WhiteNoise then serves them
compressed and with cache-busting file names. The Docker image runs this step
during the build.

---

## Deployment

The full guide is in **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**. It covers
production environment variables, Docker Compose, a VPS with
nginx + Gunicorn + systemd, managed platforms, HTTPS and domains, media
storage, logging, health checks, backups and the deployment checklist.

Quick start with Docker:

```bash
cp .env.docker.example .env.docker        # then edit secrets
docker compose --env-file .env.docker up -d --build
docker compose --env-file .env.docker exec web python manage.py createsuperuser
# open http://localhost:8080/
```

## Backup and restore (summary)

```bash
pg_dump -Fc -h localhost -U django_cms_user django_cms > backup.dump
pg_restore --clean --if-exists --no-owner -h localhost -U django_cms_user -d django_cms backup.dump
```

Also back up the `media/` directory, which holds uploaded images. See
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#backup-and-restore).

---

## Troubleshooting

| Problem | Cause and fix |
|---|---|
| `ImproperlyConfigured: Set the SECRET_KEY environment variable` | `.env` is missing or has no `SECRET_KEY`. Copy `.env.example` to `.env` and fill it in. Same for `DB_NAME`, `DB_USER` and `DB_PASSWORD`. |
| `connection to server at "localhost" ... failed` | PostgreSQL is not running, or `DB_HOST`/`DB_PORT` is wrong. On Windows, start the `postgresql-x64-NN` service in *Services*. |
| `password authentication failed for user "django_cms_user"` | `DB_PASSWORD` in `.env` doesn't match the role. Reset it as superuser: `ALTER ROLE django_cms_user PASSWORD 'new';` |
| `permission denied to create database` (tests with Postgres) | `ALTER ROLE django_cms_user CREATEDB;`, or run tests on SQLite (the default). |
| `relation "django_cache" does not exist` | Run `python manage.py createcachetable`. |
| `400 Bad Request` | The host name is not in `ALLOWED_HOSTS`. |
| `403 "Session expired"` on a form | CSRF failure. Reload the page. In production, make sure `CSRF_TRUSTED_ORIGINS` contains `https://your-domain`. |
| "Too many attempts" (429) | The rate limit was hit. Wait for the window to pass, or adjust `RATELIMIT_*` in `.env`. |
| Pages unstyled in production | Run `collectstatic`. Make sure `DEBUG=False` builds used `collectstatic` and that `staticfiles/` exists. |
| Uploaded images 404 in production | Django doesn't serve media when `DEBUG=False`. Configure nginx or object storage (see deployment guide). |
| Infinite redirect loop behind a proxy | Set `USE_X_FORWARDED_PROTO=True` and make sure the proxy sends `X-Forwarded-Proto: https`. |
| `No module named 'fcntl'` when starting Gunicorn on Windows | Gunicorn runs on Linux/macOS only. Use `runserver` on Windows, or Docker. |
| Password-reset emails not arriving | In development they're printed in the console. In production check the `EMAIL_*` settings and `docker compose logs web` / app logs. |
