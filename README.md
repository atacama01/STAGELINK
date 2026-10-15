# STAGELINK — Internship Management Service (Member 4)

University internship management platform — the microservice that owns internships, lifecycle, supervisor assignment, final submissions, evaluations, notifications and audit history.

- Project spec: [`project.md`](project.md) (group-level)
- Service spec: [`service.md`](service.md) (this service — read first before coding)
- Team: 5 members, 1 service each
- Source docs: Cahier des charges fonctionnel (v1.1), Cahier des charges technique (v1.1), Django service quick guide (Member 4)

---

## What's inside

```
config/          # Django settings, URLs, WSGI (env-driven, nothing secret)
common/          # JWT validation, internal service token, permissions, pagination, uniform errors
internships/     # Internship model, lifecycle, supervisor, cancellation, audit
submissions/     # FinalSubmission, files, links, review, evaluation
notifications/   # Notification model and endpoints
audit/           # AuditEntry (append-only history)
tests/           # Per-area test modules (see service.md section 11)
media/           # Uploaded files (development only; persistent volume in deployment)
```

---

## To start (shared — copy `.env` for yourself, never commit it)

```bash
# 1. One-time setup (already done in this repo)
python -m venv .venv
.venv\Scripts\activate           # Linux/mac: source .venv/bin/activate
pip install -r requirements.txt

# 2. Your local copy of secrets (template is .env.example)
cp .env.example .env
# Edit .env: DJANGO_SECRET_KEY, POSTGRES_PASSWORD, JWT_SECRET,
# INTERNAL_SERVICE_TOKEN — coordinate these with Identity & Profiles.

# 3. Database
# PostgreSQL must be running and the `internship_db` database created.
# The shared server hosts all 3 service DBs (see project.md 3).
python manage.py migrate

# 4. Verify
python manage.py check
python manage.py test
```

---

## How to share / work in team

- **Repository**: this folder is the shared repo (monorepo per project.md item 8 — team can revisit if needed).
- **Environment**: `.env` is in `.gitignore`. Each teammate creates their own from `.env.example`. Secrets are coordinated with the group, not stored in source.
- **Service boundary**: this service NEVER reads another service's tables. References (`student_user_id`, `offer_id`, etc.) are plain fields (service.md 1, project.md 3).
- **API contract with Offers & Applications**: `POST /api/internal/internships/` (idempotent create) and `GET /api/internal/students/{id}/active-internship/` must be agreed by Milestone 1 (project.md 9 item 4 / service.md 5).
- **JWT / claims**: must match Identity & Profiles. Confirm claim names (`user_id` / `role`) and algorithm (RS256 vs HS256) with them before Milestone 2.

---

## Milestones (from service.md 10 / project.md 8)

| Milestone | Deadline | Your part (this service) |
|---|---|---|
| 1 Design | 25 Oct 2026 | Confirm lifecycle rules, internal API contract, JWT claims |
| 2 MVP | 22 Nov 2026 | Project skeleton, model + unique constraints, internal endpoints, JWT auth, permissions, submissions |
| 3 Validation | 6 Dec 2026 | Tests pass, README complete, API docs, `activate_internships` command |
| 4 Delivery | 13 Dec 2026 | Dockerfile, Docker Compose entry, deployment notes, backup procedure |

---

## Key rules to never break (service.md / project.md)

- A student can have at most one `CONFIRMED` or `IN_PROGRESS` internship — enforced by partial unique constraint on `student_user_id` plus application check (service.md 3, 5).
- Status is read-only through PATCH; changes go through dedicated endpoints only (service.md 4).
- Files: max 10 MB, extensions `.pdf` `.docx` `.pptx` `.jpg` `.png` `.csv`, check file signature not extension, never expose `MEDIA_ROOT` directly (service.md 8).
- Every protected endpoint enforces role/object permissions server-side. Hidden UI is not security (service.md 6.8).
- Audit entries are append-only — no update or delete endpoints (service.md 3).
- Internal endpoints use `X-Service-Token` header compared in constant time (service.md 5, common/internal_auth.py).
- Error responses always follow `{"error": {"code": "...", "message": "...", "fields": {...}}}` (service.md 9).

---

## Deployment (Milestone 4)

- Docker + Docker Compose on a Linux server, HTTPS at reverse proxy
- Persistent volumes for PostgreSQL data and `MEDIA_ROOT`
- `activate_internships` runs via cron or a scheduler container (service.md 4)
- `.env` values become Compose environment / secrets — never checked in

---

## Questions to settle with team (service.md 13 / project.md 9)

1. Internal token mechanism and env name — confirmed by `INTERNAL_SERVICE_TOKEN` here.
2. JWT algorithm / claim names — must match Identity & Profiles.
3. Should internship API return supervisor contact, or frontend fetch from Identity?
4. Can `CONFIRMED` internships submit? (Proposed: `IN_PROGRESS` only — service.md 4)
5. Can company see cancellation reasons? (Proposed default: no — project.md 5)
6. Notification recipients per event — service.md 6.6 / 7.
7. History visible to participants? (Proposed: supervisor + admin only)
8. Score precision (decimal 2 places proposed) and file/link limits (5 each proposed).
9. Repo layout — this repo is shared; revisiting per project.md 8.
