# Django CMS — Specification

Derived from `start.md`. This document records *what* is built and the
assumptions made where the brief was open-ended.

## 1. Scope

A server-rendered Django monolith that lets staff publish generic content
(articles, news, pages — any "titled item with a body") and lets the public
read it. Visitors may register an account; registered users get a profile.
Administration happens in Django Admin.

Out of scope (not requested): comments, likes, user-authored content,
multi-language, REST API, WYSIWYG editor, social login.

## 2. Stack

| Concern | Choice | Notes |
|---|---|---|
| Language | Python 3.13 (3.12+ supported) | |
| Framework | Django 5.2 LTS | Supported until April 2028 |
| Database | PostgreSQL 14+ (tested on 18) via psycopg 3 | SQLite only for the isolated test run |
| Config | django-environ, `.env` | No secrets in code |
| Static files | WhiteNoise (compressed, hashed) | |
| Images | Pillow (`ImageField`) | |
| Frontend | Django templates + Bootstrap 5.3 (vendored, no CDN) | No JS framework |
| App server | Gunicorn | Linux/containers |
| Tests | pytest + pytest-django | |
| Containers | Dockerfile + compose.yaml (db, web, nginx) | Optional |

## 3. Apps

- **core** — home, about, contact, health check, error pages, security
  middleware, rate-limit helper. (Added to the suggested layout: these pages
  don't belong to accounts or content.)
- **accounts** — custom `User` model, registration, profile, auth templates.
- **content** — `Category`, `Content`, public list/detail, admin.

## 4. Data model

### accounts.User (extends `AbstractUser`)
- `email` required; unique case-insensitively (`UniqueConstraint(Lower("email"))`).
- A custom user model is set from day one so it can be extended later
  without a painful migration.

### content.Category
| Field | Type | Rules |
|---|---|---|
| name | char(100) | unique |
| slug | slug(120) | unique, auto-generated from name if blank |
| description | text | optional |
| created_at / updated_at | datetime | automatic |

### content.Content
| Field | Type | Rules |
|---|---|---|
| title | char(200) | required |
| slug | slug(220) | unique; auto-generated from title, de-duplicated (`-2`, `-3`…) |
| summary | char(300) | optional, shown on cards |
| body | text | required, rendered as escaped text with line breaks (no raw HTML → no stored XSS) |
| category | FK Category | optional, `SET_NULL` on category delete |
| featured_image | image | optional; jpg/jpeg/png/webp/gif; ≤ `MAX_UPLOAD_SIZE_MB` (default 5) |
| status | `draft` / `published` | DB check constraint |
| published_at | datetime | set automatically on first publish; DB check: published ⇒ not null; future date = scheduled |
| created_by | FK User | `SET_NULL`, set by admin on create, read-only |
| created_at / updated_at | datetime | automatic, read-only |

Indexes: `(status, published_at)` for the public listing; slug unique index.

**Publicly visible** = `status == published AND published_at <= now`.

### core.ContactMessage
`name, email, subject, message, created_at, is_read` — contact submissions
are stored and visible in admin; optionally also emailed to
`CONTACT_RECIPIENT_EMAIL`.

## 5. URLs

| URL | View | Access |
|---|---|---|
| `/` | Home: latest 6 published items | public |
| `/content/` | List, paginated (9/page), `?q=` search, `?category=` filter | public |
| `/content/<slug>/` | Detail | public if visible; staff may preview drafts |
| `/about/` | About | public |
| `/contact/` | Contact form | public, rate-limited |
| `/accounts/register/` | Sign-up | anonymous, rate-limited |
| `/accounts/login/`, `/accounts/logout/` (POST) | Django auth | login rate-limited |
| `/accounts/password-reset/…` | Django password reset flow | reset POST rate-limited |
| `/accounts/password-change/…` | Django password change | login required |
| `/accounts/profile/`, `/accounts/profile/edit/` | Profile | login required |
| `/admin/` (configurable via `ADMIN_URL`) | Django Admin | `is_staff` only |
| `/healthz/` | JSON health incl. DB ping | public, no HTTPS redirect |

## 6. Roles and permissions

- **Anonymous** — read published content, register, contact.
- **Registered user** — plus profile, password change. Never staff;
  registration form exposes no privilege fields.
- **Editor** — `is_staff` + member of the auto-created **Editors** group
  (CRUD on Content and Category, view on contact messages).
- **Superuser** — everything, including users and permissions.

## 7. Security

- Django password hashing (PBKDF2 default), validators enabled.
- CSRF on every POST; logout is POST-only.
- Rate limiting (cache-backed, per IP) on login, registration, password reset,
  contact → HTTP 429.
- Production (`DEBUG=False`): HTTPS redirect, secure + HttpOnly cookies, HSTS
  (configurable), `X-Frame-Options: DENY`, nosniff, referrer policy, COOP,
  Content-Security-Policy on public pages (all assets self-hosted).
- `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` from env; `SECRET_KEY` required.
- Uploads: extension + Pillow content validation + size limit; random-free
  date-based paths; served by nginx/object storage, not Django, in production.
- Logs to stdout; sensitive POST params are masked by Django.
- App DB role owns only its database (no superuser).

## 8. Assumptions

1. "Content" is generic; body is plain text with paragraphs (safe by default).
   A rich-text editor can be added later if the client wants one.
2. Category is optional on content.
3. Scheduling falls out of `published_at`: a published item with a future date
   is hidden until then.
4. Hosting provider not yet chosen → deliverables are a provider-neutral
   container + VPS/PaaS instructions. Nothing is deployed.
