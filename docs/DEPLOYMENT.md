# Deployment Guide

No hosting provider has been chosen yet, so this guide covers three
provider-neutral routes. **Nothing has been deployed.** Choose a host, create
the accounts and credentials yourself, and then follow the matching section.

| Route | Good for | You manage |
|---|---|---|
| A. Docker Compose on a VPS | One server, full control, lowest cost | OS updates, TLS, backups |
| B. VPS without Docker (nginx + Gunicorn + systemd) | Teams that prefer classic servers | Same as A |
| C. Managed platform (container or Python PaaS) + managed PostgreSQL | Least operations work | Env vars, domain |

---

## 1. Production environment variables

Start from [.env.example](../.env.example). Required or important values:

| Variable | Production value |
|---|---|
| `SECRET_KEY` | Long random string, unique per environment. Never reuse the dev key. |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `example.com,www.example.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://example.com,https://www.example.com` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | From your database |
| `DB_SSLMODE` | `require` (or `verify-full`) for managed/remote databases |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL` | SMTP provider credentials (password reset needs working email) |
| `USE_X_FORWARDED_PROTO` | `True` behind nginx / a PaaS router that sets `X-Forwarded-Proto` |
| `NUM_PROXIES` | Number of trusted proxies in front of the app (usually `1`) |
| `SECURE_HSTS_SECONDS` | Start at `3600`; raise to `31536000` once HTTPS is confirmed |
| `ADMIN_URL` | Optional: something less guessable than `admin/` |
| `MEDIA_ROOT` | Persistent directory for uploads (if using local disk) |

With `DEBUG=False` the following are on by default: HTTPS redirect, secure
session and CSRF cookies, HSTS, and the SMTP email backend. Leave them on
unless you have a specific reason.

Generate secrets:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
python -c "import secrets; print(secrets.token_urlsafe(32))"     # DB password
```

Store secrets in the host's secret/env-var manager or a root-readable
`.env` file (`chmod 600`). Never put them in Git.

---

## 2. Route A — Docker Compose on a VPS

Requirements: a Linux VPS with Docker Engine + Compose plugin, and a domain
pointing to the server (DNS `A`/`AAAA` records).

```bash
git clone <your-repo-url> /opt/django-cms && cd /opt/django-cms
cp .env.docker.example .env.docker && chmod 600 .env.docker
nano .env.docker
```

In `.env.docker`, set real secrets, `ALLOWED_HOSTS=example.com`,
`CSRF_TRUSTED_ORIGINS=https://example.com` and `HTTP_PORT=80`. **Delete the
four "LOCAL TRIAL" lines** so the secure defaults apply.

```bash
docker compose --env-file .env.docker up -d --build
docker compose --env-file .env.docker exec web python manage.py createsuperuser
docker compose --env-file .env.docker ps          # all services "healthy"/"running"
curl -H "Host: example.com" http://localhost/healthz/
```

The stack contains:

- `db`: PostgreSQL 18, data in the `postgres_data` volume.
- `web`: Gunicorn. It runs `migrate` and `createcachetable` on start; set
  `RUN_MIGRATIONS=0` if you run several replicas.
- `nginx`: serves `/media/` from the `media` volume and proxies everything
  else.

**HTTPS:** the bundled nginx listens on port 80 only. Choose one of these:

1. **Caddy in front** (simplest, automatic Let's Encrypt). Set nginx
   `HTTP_PORT=8080`, install Caddy on the host, and use this Caddyfile:
   ```
   example.com, www.example.com {
       reverse_proxy 127.0.0.1:8080
   }
   ```
   In `deploy/nginx.conf`, change `X-Forwarded-Proto $scheme` to
   `X-Forwarded-Proto $http_x_forwarded_proto`, and set `NUM_PROXIES=2`.
2. **Certbot inside nginx.** Add a `listen 443 ssl` server block with the
   certificate paths and mount `/etc/letsencrypt` read-only into the nginx
   container.
3. **Cloud load balancer** with a managed certificate in front of the VPS.

Updating to a new version:

```bash
git pull
docker compose --env-file .env.docker up -d --build    # migrations run automatically
```

## 3. Route B — VPS without Docker

On Ubuntu/Debian (as root or with sudo):

```bash
apt install python3 python3-venv postgresql nginx certbot python3-certbot-nginx
adduser --system --group --home /srv/django-cms django
```

1. **Database.** Run `sudo -u postgres psql` and create a role **without**
   `CREATEDB`:
   ```sql
   CREATE ROLE django_cms_user LOGIN PASSWORD '...' NOSUPERUSER NOCREATEROLE NOCREATEDB;
   CREATE DATABASE django_cms OWNER django_cms_user ENCODING 'UTF8' TEMPLATE template0;
   REVOKE CONNECT, TEMPORARY ON DATABASE django_cms FROM PUBLIC;
   ```
2. **Code.**
   ```bash
   cd /srv/django-cms && git clone <repo> app && cd app
   python3 -m venv venv && venv/bin/pip install -r requirements.txt
   cp .env.example .env && chmod 600 .env && nano .env   # MEDIA_ROOT=/srv/django-cms/media
   venv/bin/python manage.py migrate
   venv/bin/python manage.py createcachetable
   venv/bin/python manage.py collectstatic --noinput
   venv/bin/python manage.py check --deploy
   venv/bin/python manage.py createsuperuser
   chown -R django:django /srv/django-cms
   ```
3. **systemd unit** `/etc/systemd/system/django-cms.service`:
   ```ini
   [Unit]
   Description=Django CMS (Gunicorn)
   After=network.target postgresql.service

   [Service]
   User=django
   Group=django
   WorkingDirectory=/srv/django-cms/app
   Environment=PORT=8000
   ExecStart=/srv/django-cms/app/venv/bin/gunicorn config.wsgi:application --config gunicorn.conf.py --bind 127.0.0.1:8000
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```
   Then run `systemctl daemon-reload && systemctl enable --now django-cms`.
4. **nginx.** Copy `deploy/nginx.conf` to `/etc/nginx/sites-available/django-cms`.
   Change `server web:8000` to `server 127.0.0.1:8000`, `alias /srv/media/`
   to `alias /srv/django-cms/media/`, and `server_name _` to your domain.
   Enable the site, then run `certbot --nginx -d example.com -d www.example.com`.
   Certbot configures HTTPS and renewal.
5. In `.env`, set `USE_X_FORWARDED_PROTO=True` and `NUM_PROXIES=1`.

## 3a. Render (configured in `render.yaml`)

The repository has a Render Blueprint that creates a Docker web service and a
PostgreSQL database in Singapore. **Both are on the free plan.**

1. Sign in at https://dashboard.render.com, then click **New → Blueprint**.
2. Connect GitHub and pick the repository. Render reads `render.yaml`.
3. Fill in the three prompted values: `DJANGO_SUPERUSER_USERNAME`,
   `DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD` (use a strong
   password). This admin account is created automatically on start-up.
   `SECRET_KEY` is generated by Render.
4. Click **Apply**. The first build takes about 5–10 minutes. The site is then at
   `https://<service-name>.onrender.com/`, and the admin is at `/admin/`.
5. Every push to `main` redeploys automatically. Migrations run at start-up.

Free-plan limits (from Render's docs at the time of writing):

- The service sleeps after 15 minutes without traffic. The next visit takes
  about a minute.
- The free database **expires 30 days after creation**. After that there's a
  14-day grace period to upgrade before it is deleted. It has no backups.
- There's no persistent disk, so **uploaded images are lost on every
  redeploy or restart**. Images are served by Django (`SERVE_MEDIA=True`)
  because there's no nginx.
- There's no shell, so emails (password reset links) appear in **Logs** in
  the dashboard until you configure SMTP.

**Moving to production on Render:**

- Change the web service to a paid instance and the database to a paid plan.
- Add a **Disk** mounted at `/app/media` and set `MEDIA_ROOT=/app/media`.
- Set the `EMAIL_*` SMTP variables.
- Add your custom domain under **Settings → Custom Domains**. Render issues
  the TLS certificate. Add the domain to `ALLOWED_HOSTS` and to
  `CSRF_TRUSTED_ORIGINS` as `https://`.
- Check prices on Render's pricing page first.

## 4. Route C — Managed platforms

Any platform that runs a Dockerfile, or a Python app with a start command,
works. Examples include Render, Railway, Fly.io, DigitalOcean App Platform,
Heroku, Azure App Service and Google Cloud Run. Typical steps:

1. Create a managed PostgreSQL database and copy its host, port, name, user
   and password into the `DB_*` variables (`DB_SSLMODE=require`).
2. Create a web service from this repository using the **Dockerfile**. If
   you use a Python buildpack instead, the start command is
   `gunicorn config.wsgi:application --config gunicorn.conf.py`. The platform
   sets `PORT`, and `gunicorn.conf.py` reads it.
3. Set all variables from section 1, plus `USE_X_FORWARDED_PROTO=True`,
   `NUM_PROXIES=1` and `FORWARDED_ALLOW_IPS=*`. Only set the last one when
   the app is reachable solely through the platform router.
4. Release/pre-deploy command: `python manage.py migrate && python manage.py createcachetable`.
   With the Dockerfile, the entrypoint already does this.
5. Health check path: `/healthz/`.
6. Add your custom domain in the platform dashboard and point DNS as
   instructed. The platform issues and renews the TLS certificate.
7. **Media:** most platforms have ephemeral disks. Either attach a
   persistent volume at `MEDIA_ROOT`, or use object storage (see below).

Some of these platforms are paid. Check pricing before creating resources.

---

## 5. Static and media files

- **Static** (CSS/JS): `collectstatic` → served by WhiteNoise with long cache
  headers. No extra setup is needed. The Docker image collects at build time.
- **Media** (uploaded images): Django does **not** serve them when
  `DEBUG=False`. Options:
  - nginx `location /media/` (Compose and VPS routes above). Keep the
    `nosniff` and sandbox CSP headers from `deploy/nginx.conf`.
  - Persistent volume on the platform, served by nginx/the platform's static
    feature.
  - Object storage (S3, Cloudflare R2, DigitalOcean Spaces, Azure Blob).
    Add `django-storages`, then set `STORAGES["default"]` to its backend. This
    is a small settings change but needs testing with your provider.

Uploads are limited to JPG/PNG/WebP/GIF, validated as real images with Pillow,
size-limited (`MAX_UPLOAD_SIZE_MB`), and stored under random file names.

## 6. Logging

All logs (Django, Gunicorn access/error) go to stdout/stderr:

- Docker: `docker compose --env-file .env.docker logs -f web`
- systemd: `journalctl -u django-cms -f`
- PaaS: the platform's log viewer.

`LOG_LEVEL` controls verbosity. SQL queries and their parameters are never
logged, and Django masks passwords in error reports. Note: Gunicorn access
logs contain request paths, including one-time password-reset links. Restrict
who can read logs, and keep retention short (e.g. 14–30 days).

## 7. Health check

`GET /healthz/` returns `200 {"status": "ok", "database": "ok"}` or
`503` if the database is unreachable. It's exempt from the HTTPS redirect, but
the request's `Host` header must still be in `ALLOWED_HOSTS`. Point uptime
monitors and load balancers at it.

## 8. Backup and restore

**What to back up:** the PostgreSQL database **and** the media files.

Database:

```bash
# Backup (custom format, compressed)
pg_dump -Fc -h $DB_HOST -U $DB_USER $DB_NAME > backups/db-$(date +%F).dump

# Docker Compose
docker compose --env-file .env.docker exec -T db \
    sh -c 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"' > backups/db-$(date +%F).dump
```

Media:

```bash
tar czf backups/media-$(date +%F).tar.gz -C /srv/django-cms media
# Docker volume:
docker run --rm -v django-cms_media:/m -v "$PWD/backups":/b alpine tar czf /b/media-$(date +%F).tar.gz -C /m .
```

Restore (stop the app first so nothing writes during the restore):

```bash
pg_restore --clean --if-exists --no-owner -h $DB_HOST -U $DB_USER -d $DB_NAME backups/db-YYYY-MM-DD.dump
tar xzf backups/media-YYYY-MM-DD.tar.gz -C /srv/django-cms
# Docker:
docker compose --env-file .env.docker exec -T db \
    sh -c 'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backups/db-YYYY-MM-DD.dump
```

Recommendations:

- Back up daily via cron or the platform's automated backups.
- Keep copies off the server, and encrypt them because they contain personal
  data (emails, password hashes).
- **Test a restore** into a scratch database at least once per quarter.

## 9. Security notes for production

- Keep `DEBUG=False`. Never expose the dev `.env`.
- The app DB role should own only its database and have no superuser or
  `CREATEDB` rights. In the bundled Compose stack, the app connects as the
  container's initial user (a superuser inside that container). For stricter
  separation, create a limited role as in Route B.
- HSTS: once HTTPS works on every subdomain, consider
  `SECURE_HSTS_SECONDS=31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS=True` and,
  optionally, `SECURE_HSTS_PRELOAD=True`. `check --deploy` warns about the
  last two until you decide. They're intentionally off by default because
  they affect your whole domain.
- Rate limits use the database cache, shared by all Gunicorn workers. For
  high traffic, switch `CACHE_URL` to Redis (`rediscache://host:6379/1`).
- Run `pip list --outdated` and update Django patch releases regularly
  (5.2 LTS is supported until April 2028).
- These measures follow Django's deployment checklist, but they are not a
  substitute for a security review or penetration test before handling
  sensitive data.

---

## 10. Deployment checklist

Before go-live:

- [ ] Hosting provider and database chosen. Costs approved.
- [ ] Domain DNS points to the host.
- [ ] Production env vars set (section 1). New `SECRET_KEY`. `DEBUG=False`.
- [ ] `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` contain the real domain(s).
- [ ] Database created with a least-privilege role. `DB_SSLMODE` set for remote DBs.
- [ ] `python manage.py migrate` and `createcachetable` done.
- [ ] `python manage.py collectstatic` done (automatic in Docker).
- [ ] `python manage.py check --deploy` shows no unexpected warnings.
- [ ] HTTPS works. `http://` redirects to `https://`.
- [ ] Media storage is persistent and served (upload a test image and view it).
- [ ] SMTP configured. A password reset email arrives.
- [ ] Superuser created. Editors added to the **Editors** group.
- [ ] `/healthz/` returns 200 and is monitored.
- [ ] Backups scheduled. A test restore has succeeded.
- [ ] Log access is restricted and retention is set.
- [ ] Smoke test: home, content list/detail, contact form, register, login,
      logout, admin create/publish/unpublish.

## 11. Handover notes

- **Accounts to hand over:** hosting, DNS/registrar, database, SMTP provider,
  Git repository, and the initial superuser. Transfer each to the client's own
  email, and rotate passwords after handover.
- **Secrets inventory:** `SECRET_KEY`, DB password, SMTP password. These are
  stored only in the host's env-var manager / `.env` on the server.
- **Routine tasks:** check backups weekly, apply Django/OS security updates
  monthly, and review staff accounts quarterly.
- **Day-to-day use:** see [ADMIN_GUIDE.md](../ADMIN_GUIDE.md).
- **Developers:** see [README.md](../README.md) and [SPEC.md](SPEC.md).
  Run `pytest` before every change.
