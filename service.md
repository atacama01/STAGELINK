# Internship Management Service

Member 4's service in the STAGELINK microservices architecture. Full project context is in `project.md`.

---

## 1. Purpose and boundaries

Creates and manages official internships. An internship exists only after a student confirms an application that the company has accepted.

### This service owns

- Internship records, their lifecycle status, and their dates.
- The unique source application ID, which prevents duplicate internships.
- Cancellation requests and their decisions.
- Supervisor assignment (current supervisor and assignment history).
- Final submissions: reports, file metadata, external links, review decisions and resubmissions.
- Evaluations: score out of 20 and optional comment.
- In-app notifications and their individual read state.
- The audit history of important internship events.

### This service does not own

- Offers and applications, and the company decisions on them (Offers & Applications).
- Users, roles, JWT issuing, profiles and company verification (Identity & Profiles).

Stored references to other services' data are plain IDs (`student_user_id`, `company_user_id`, `offer_id`, `supervisor_user_id`, `source_application_id`). There are no foreign keys across services.

---

## 2. Technology and setup

- Python, Django, Django REST Framework
- PostgreSQL, database name `internship_db`, on the shared server
- JWT validation: local, using the same key or secret as Identity & Profiles
- Files: local directory in development, persistent volume in deployment

### Install

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install django djangorestframework psycopg[binary] django-environ
pip install djangorestframework-simplejwt PyJWT   # JWT validation (adjust to team decision)
django-admin startproject config .
python manage.py startapp internships
python manage.py startapp submissions
python manage.py startapp notifications
python manage.py startapp audit
```

### Project layout

```
internship_service/
├── config/
│   ├── settings.py          # reads env vars with django-environ
│   ├── urls.py
│   └── wsgi.py
├── common/
│   ├── permissions.py       # role and object permission classes
│   ├── jwt_auth.py          # local JWT validation
│   ├── internal_auth.py     # service-to-service token check
│   └── pagination.py
├── internships/             # Internship model, lifecycle, create, supervisor, cancellations
├── submissions/             # FinalSubmission, files, links, reviews, evaluation
├── notifications/           # Notification model and endpoints
├── audit/                   # AuditEntry model and history endpoint
├── tests/
│   ├── test_internal_create.py
│   ├── test_permissions.py
│   ├── test_lifecycle.py
│   ├── test_cancellation.py
│   ├── test_submissions.py
│   ├── test_evaluation.py
│   └── test_notifications.py
├── Dockerfile
├── requirements.txt
└── README.md
```

Splitting domain logic into apps keeps the code reviewable. The guide's `api` app can hold the URL routing if the team prefers it.

### Environment variables (never committed)

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret |
| `DJANGO_DEBUG` | `False` in deployment |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts |
| `POSTGRES_DB` | `internship_db` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database credentials |
| `POSTGRES_HOST`, `POSTGRES_PORT` | Database address |
| `JWT_ALGORITHM` | `RS256` or `HS256` (team decision) |
| `JWT_PUBLIC_KEY` or `JWT_SECRET` | Verification key, depending on algorithm |
| `INTERNAL_SERVICE_TOKEN` | Shared token for `/api/internal/` calls |
| `MEDIA_ROOT` | Path to the persistent file volume |
| `MAX_UPLOAD_SIZE_BYTES` | `10485760` (10 MB) |

---

## 3. Data model

All primary keys are UUIDs. Timestamps are `created_at` and `updated_at` unless noted.

### Internship

| Field | Type | Notes |
|---|---|---|
| `source_application_id` | UUID | **Unique.** Idempotency key from Offers & Applications |
| `student_user_id` | UUID | Plain reference to Identity |
| `company_user_id` | UUID | Plain reference to Identity |
| `offer_id` | UUID | Plain reference to Offers & Applications |
| `supervisor_user_id` | UUID, nullable | Set by university administration |
| `start_date`, `end_date` | Date | |
| `status` | Choice | `CONFIRMED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` |
| `completed_at`, `cancelled_at` | DateTime, nullable | |

Database constraints:

```python
class Internship(models.Model):
    class Meta:
        constraints = [
            # A student can have at most one active internship at database level.
            models.UniqueConstraint(
                fields=["student_user_id"],
                condition=Q(status__in=["CONFIRMED", "IN_PROGRESS"]),
                name="one_active_internship_per_student",
            ),
        ]
```

The partial unique constraint enforces the single-active-internship rule even if two requests arrive at the same moment. The application code checks first, and the constraint is the final guard.

### CancellationRequest

| Field | Type | Notes |
|---|---|---|
| `internship` | FK | Within this service |
| `requested_by_user_id`, `requested_by_role` | UUID, Choice | `STUDENT` or `COMPANY` |
| `reason` | Text | Required, non-blank |
| `status` | Choice | `PENDING`, `APPROVED`, `REJECTED` |
| `decided_by_user_id` | UUID, nullable | University administration |
| `decision_reason` | Text, nullable | Required when rejected |
| `decided_at` | DateTime, nullable | |

Constraint: at most one `PENDING` request per internship.

### FinalSubmission

| Field | Type | Notes |
|---|---|---|
| `internship` | FK | |
| `attempt_number` | Integer | 1, 2, 3... for resubmissions |
| `status` | Choice | `SUBMITTED`, `APPROVED`, `REJECTED` |
| `submitted_by_user_id` | UUID | Student |
| `submitted_at` | DateTime | |
| `reviewed_by_user_id` | UUID, nullable | Assigned supervisor |
| `reviewed_at` | DateTime, nullable | |
| `review_reason` | Text, nullable | Required when rejected |

Constraint: unique on `(internship, attempt_number)`.

### SubmissionFile

| Field | Type | Notes |
|---|---|---|
| `submission` | FK | |
| `original_name` | String | Display name only, never used on disk |
| `stored_path` | String | Server-generated path, see section 8 |
| `content_type` | String | Verified type, not the client header |
| `size_bytes` | Integer | |
| `sha256` | String | For integrity and backup checks |

### SubmissionLink

| Field | Type | Notes |
|---|---|---|
| `submission` | FK | |
| `url` | URL | Must be `https://` |
| `label` | String | Optional, for example "GitHub repository" |

### Evaluation

| Field | Type | Notes |
|---|---|---|
| `internship` | OneToOne | One evaluation per internship |
| `score` | Decimal(4,2) | 0.00 to 20.00 (team decision, see project.md) |
| `comment` | Text, blank allowed | |
| `evaluated_by_user_id` | UUID | Assigned supervisor |

### Notification

| Field | Type | Notes |
|---|---|---|
| `recipient_user_id` | UUID | |
| `event_type` | String | For example `APPLICATION_WITHDRAWN`, `SUBMISSION_REJECTED` |
| `title`, `message` | String, Text | |
| `related_type`, `related_id` | String, UUID | Points to the related record |
| `is_read` | Boolean | Default `False` |
| `read_at` | DateTime, nullable | |

### AuditEntry (append-only)

| Field | Type | Notes |
|---|---|---|
| `internship` | FK, nullable | |
| `action` | String | See section 6.9 |
| `actor_user_id`, `actor_role` | UUID, String | From the JWT, or `SYSTEM` for automatic actions |
| `details` | JSON | Old and new values, reasons, IDs |
| `created_at` | DateTime | |

No update or delete endpoints exist for audit entries.

---

## 4. Lifecycle rules

### Transitions

| From | To | Trigger | Who |
|---|---|---|---|
| (none) | CONFIRMED | Internal create call | Offers & Applications (service token) |
| CONFIRMED | IN_PROGRESS | `start_date` reached | System job, see below |
| IN_PROGRESS | COMPLETED | Evaluation recorded, submission approved | Assigned supervisor |
| CONFIRMED or IN_PROGRESS | CANCELLED | Cancellation request approved | University administration |

Any other transition is rejected with `409 Conflict`. Terminal states are `COMPLETED` and `CANCELLED`.

### Automatic start (`CONFIRMED` → `IN_PROGRESS`)

There is no message broker and no task queue in v1, so use a Django management command:

```bash
python manage.py activate_internships
```

It updates every `CONFIRMED` internship whose `start_date <= today` and writes an audit entry with actor `SYSTEM`. It must be idempotent. Run it once a day with cron, or with a small scheduler container in Docker Compose. Team decision: confirm this approach with the group.

### Status field in PATCH

Status is read-only through the API. Changes happen only through the actions in the table above. This is the reading of the guide's "update only permitted lifecycle fields": PATCH covers dates only, and status changes go through dedicated endpoints.

---

## 5. Create flow (idempotent, called by Offers & Applications)

```
POST /api/internal/internships/
  1. Check INTERNAL_SERVICE_TOKEN header. Missing or wrong → 401.
  2. Validate body. Invalid → 400.
  3. Open a transaction.
  4. If an Internship with this source_application_id exists:
       return 200 with the existing internship (retry-safe, no duplicate).
  5. If the student already has a CONFIRMED or IN_PROGRESS internship:
       return 409 Conflict (this is a different application).
  6. Create the Internship with status CONFIRMED.
  7. Write AuditEntry (action INTERNSHIP_CREATED, actor SYSTEM).
  8. Create Notification rows for the student and the company.
  9. Commit. Return 201 with the internship.
  If a database IntegrityError happens at step 6 because a parallel request won,
  roll back and repeat steps 4 and 5.
```

Important: step 4 must come before step 5. A retry for the same application must return the existing internship, not a conflict.

Response codes:

| Case | Code |
|---|---|
| Created | 201 |
| Same `source_application_id` already exists | 200 with existing record |
| Student already has an active internship | 409 |
| Missing or invalid service token | 401 |
| Invalid payload | 400 |

### Active-internship check (called by Offers & Applications)

```
GET /api/internal/students/{student_user_id}/active-internship/
→ 200 {"active": true, "internship_id": "..."}
→ 200 {"active": false, "internship_id": null}
```

Offers & Applications calls this before it accepts a new application.

---

## 6. Endpoint reference

Base path: `/api/`. All protected endpoints require a valid JWT access token. Roles below are checked server-side on every request.

### 6.1 Internal (service-to-service)

| Method | Path | Caller | Purpose |
|---|---|---|---|
| POST | `/api/internal/internships/` | Offers & Applications | Create internship, idempotent per `source_application_id` |
| GET | `/api/internal/students/{id}/active-internship/` | Offers & Applications | Check for an active internship |
| POST | `/api/internal/notifications/` | Any trusted service | Create notification(s) for a recipient |

### 6.2 Internships

| Method | Path | Who | Behaviour |
|---|---|---|---|
| GET | `/api/internships/` | Student, company, supervisor, university admin | Lists only what the caller may see: own (student or company), assigned (supervisor), all (university admin) |
| GET | `/api/internships/{id}/` | Participant, assigned supervisor, university admin | Detail. Other callers get `404`, not `403`, to avoid revealing existence |
| PATCH | `/api/internships/{id}/` | University admin | Edit `start_date` and `end_date` while `CONFIRMED` only. `status` is read-only |
| POST | `/api/internships/{id}/supervisor/` | University admin | Body `{"supervisor_user_id": "..."}`. Assign or reassign. Allowed while `CONFIRMED` or `IN_PROGRESS`. Writes audit entry |

### 6.3 Cancellations

| Method | Path | Who | Behaviour |
|---|---|---|---|
| POST | `/api/internships/{id}/cancellation-requests/` | Student or company of this internship | Body `{"reason": "..."}`. Needs an active internship and no pending request. Notifies university admin |
| GET | `/api/cancellation-requests/` | University admin: all. Student or company: own internships only | Filter by `status` |
| POST | `/api/cancellation-requests/{id}/decision/` | University admin | Body `{"decision": "APPROVE" \| "REJECT", "reason": "..."}`. Reason required for reject. Approve sets internship to `CANCELLED`. Notifies both parties |

### 6.4 Final submissions

| Method | Path | Who | Behaviour |
|---|---|---|---|
| POST | `/api/internships/{id}/submissions/` | Student of this internship | Multipart: `files[]`, `links[]`, optional `note`. Allowed only when the internship is `IN_PROGRESS` and there is no submission or the last one is `REJECTED`. Creates a new `attempt_number` |
| GET | `/api/internships/{id}/submissions/` | Student, assigned supervisor | Lists submissions with metadata. Not visible to company |
| GET | `/api/submissions/{id}/` | Student, assigned supervisor | Detail with files and links |
| GET | `/api/submissions/{id}/files/{file_id}/` | Student, assigned supervisor | Streams the file. Never a public URL (see section 8) |
| POST | `/api/submissions/{id}/review/` | Assigned supervisor | Body `{"decision": "APPROVE" \| "REJECT", "reason": "..."}`. Reason required for reject. Only for `SUBMITTED` submissions |

### 6.5 Evaluation

| Method | Path | Who | Behaviour |
|---|---|---|---|
| POST | `/api/internships/{id}/evaluation/` | Assigned supervisor | Body `{"score": 16.5, "comment": "..."}`. Requires latest submission `APPROVED`. Once only. Sets internship to `COMPLETED` in the same transaction |
| GET | `/api/internships/{id}/evaluation/` | Student (own), assigned supervisor, university admin | Returns evaluation or `404` if none yet |

### 6.6 Notifications

| Method | Path | Who | Behaviour |
|---|---|---|---|
| GET | `/api/notifications/` | Any authenticated user | Own notifications only. Filter by `is_read` |
| POST | `/api/notifications/{id}/read/` | Recipient only | Marks this one notification as read. There is no bulk "mark all" endpoint, as the spec requires |

The frontend calls `/read/` when the user opens a single notification. Opening the list must not change read state.

### 6.7 History

| Method | Path | Who | Behaviour |
|---|---|---|---|
| GET | `/api/internships/{id}/history/` | University admin, assigned supervisor | Chronological audit entries for the internship. Read-only |

### 6.8 Permission matrix (summary)

| Action | Student (own) | Company (own) | Supervisor (assigned) | University admin | Guest |
|---|---|---|---|---|---|
| Read internship | Yes | Yes | Yes | Yes | No |
| Edit dates | No | No | No | Yes | No |
| Assign supervisor | No | No | No | Yes | No |
| Request cancellation | Yes | Yes | No | No | No |
| Decide cancellation | No | No | No | Yes | No |
| Submit final work | Yes | No | No | No | No |
| View submission and files | Yes | No | Yes | No | No |
| Review submission | No | No | Yes | No | No |
| Evaluate | No | No | Yes | No | No |
| View evaluation | Yes | No | Yes | Yes | No |
| View history | No | No | Yes | Yes | No |
| Read own notifications | Yes | Yes | Yes | Yes | No |

The matrix is enforced in code through permission classes and queryset filtering. Hidden UI elements are not a security control.

### 6.9 Audit action names

`INTERNSHIP_CREATED`, `INTERNSHIP_STATUS_CHANGED`, `INTERNSHIP_DATES_UPDATED`, `SUPERVISOR_ASSIGNED`, `SUPERVISOR_REASSIGNED`, `CANCELLATION_REQUESTED`, `CANCELLATION_APPROVED`, `CANCELLATION_REJECTED`, `SUBMISSION_CREATED`, `SUBMISSION_APPROVED`, `SUBMISSION_REJECTED`, `EVALUATION_RECORDED`.

---

## 7. Business logic details

### Cancellation

1. Student or company posts a reason. The internship must be `CONFIRMED` or `IN_PROGRESS`, and no request may be `PENDING`.
2. University admin decides.
3. Approve: internship becomes `CANCELLED` and `cancelled_at` is set. The student is free to apply again, because the active-internship check no longer matches. Both parties get a notification. Audit entry written.
4. Reject: the internship keeps its status. Reason stored. Requester notified.

### Final submission and review

1. A student can submit only when `IN_PROGRESS`. Each new attempt needs the previous one to be `REJECTED`, or to have none.
2. Submission is stored with its files and links, in one transaction. Files are validated before anything is saved (section 8).
3. Supervisor reviews. Approve → `APPROVED`. Reject → `REJECTED` with reason. The student is notified.
4. An `APPROVED` submission is final. Nothing else can be submitted after it.

### Evaluation

1. Requires the latest submission to be `APPROVED`.
2. Score must be between 0 and 20. Comment is optional.
3. Saved, and the internship becomes `COMPLETED` in the same transaction. Completed is terminal.
4. Once an evaluation exists, it cannot be edited through the API in v1.

### Notifications

Services create notifications through `POST /api/internal/notifications/`. Each one has a single recipient. Read state is per notification.

---

## 8. File handling

Rules from the specs: validate type and size, serve only through authorized endpoints, persistent storage in deployment, backups.

- Maximum 10 MB per file, checked before reading the whole body.
- Accepted extensions: `.pdf`, `.docx`, `.pptx`, `.jpg`, `.jpeg`, `.png`, `.csv`.
- The extension alone is not trusted. Check the file signature:
  - PDF: starts with `%PDF`
  - DOCX and PPTX: ZIP container (`PK\x03\x04`) with the expected internal parts
  - JPG: `FF D8 FF`; PNG: `89 50 4E 47 0D 0A 1A 0A`
  - CSV: decodable as UTF-8 text with no binary bytes
- Files are stored under a server-generated name, for example `MEDIA_ROOT/submissions/{internship_id}/{submission_id}/{uuid}.{ext}`. The original name is kept only in the database.
- Downloads go through `/api/submissions/{id}/files/{file_id}/` with an authorization check on every request. Responses use `Content-Disposition: attachment` and `X-Content-Type-Options: nosniff`.
- Do not expose `MEDIA_ROOT` through the web server.
- Links must be `https://` URLs, with a length limit.
- Limit the number of files and links per submission (team decision, proposed 5 each).

---

## 9. Error handling conventions

| Situation | Code |
|---|---|
| Not authenticated | 401 |
| Authenticated, not permitted, object exists | 403 |
| Object not visible to caller | 404 |
| Invalid input | 400 with field errors |
| Invalid transition, conflict, duplicate | 409 |
| File too large or wrong type | 400 or 413 with clear message |

Responses are JSON. Errors use one shape: `{"error": {"code": "...", "message": "...", "fields": {...}}}`.

---

## 10. Build order and milestones

### Milestone 1 (25 October 2026): design

- Agree the lifecycle rules and the transition table with the team (section 4).
- Agree the internal API contract with Offers & Applications: create payload, active-check response, notification payload, service token.
- Decide JWT algorithm and claim names with Identity & Profiles.
- Finalize this document and record the team decisions in `project.md`.

### Milestone 2 (22 November 2026): MVP

1. Project skeleton, settings with environment variables, PostgreSQL connection, migrations.
2. Internship model with unique `source_application_id` and partial unique constraint on active students.
3. Internal create endpoint with idempotency and conflict handling. Active-check endpoint.
4. Local JWT authentication and the permission classes.
5. Participant-scoped internship list and detail. Supervisor assignment.
6. Cancellation requests and decisions.
7. Final submissions with file validation, links, and authorized download.
8. Review and evaluation, with the transition to `COMPLETED`.
9. Notifications: create, list, read one.
10. Audit entries and history endpoint.
11. `activate_internships` management command.

### Milestone 3 (6 December 2026): validation

- Test suite (section 11). Fix defects found.
- Concurrency test for the single-active-internship rule.
- README: setup, env variables, migrations, how to run, how to test.
- API documentation for each endpoint.

### Milestone 4 (13 December 2026): delivery

- Dockerfile and service entry in Docker Compose.
- Deployment notes and environment examples without secrets.
- Backup procedure for the database and the file volume.
- Demo of the internship part of the workflow.

---

## 11. Testing plan

| Area | What to test |
|---|---|
| Unit | Transition rules, cancellation logic, file signature checks, score range |
| Internal create | First call creates; repeated call returns the same record; second application for an active student gets 409; wrong token gets 401 |
| Concurrency | Two parallel creates for the same student: exactly one succeeds |
| Permissions | Each role on each endpoint: allowed, forbidden, not visible (404). Students cannot read another student's submission. Supervisor cannot read unassigned internships. Company cannot read submissions |
| Lifecycle | `CONFIRMED` → `IN_PROGRESS` by the command, run twice; evaluation → `COMPLETED`; invalid transitions rejected |
| Cancellation | Request needs a reason; one pending at a time; approve cancels; reject keeps status; student can apply again after approval |
| Submissions | Accepted and rejected file types; 10 MB boundary; wrong content with right extension rejected; links must be `https`; resubmission after rejection; no submission after approval |
| Downloads | Authorized user gets the file; others get 403 or 404; response headers present |
| Notifications | Recipient targeting; opening one marks only that one; no bulk read endpoint |
| History | Every listed action writes an entry; entries cannot be edited or deleted through the API |

Commands:

```bash
python manage.py test
python manage.py test tests.test_internal_create
```

---

## 12. Definition of done

- Only trusted internal calls can create internships. A repeated create for the same application returns the existing internship.
- A student cannot have two active internships, verified at both application and database level.
- Every protected endpoint enforces role and object permissions server-side, with tests.
- Files are validated, stored under generated names, and served only through authorized endpoints.
- Status changes follow the transition table, and every important action is recorded in the audit history.
- Migrations are committed. Tests pass. The README explains setup and deployment without any secrets in the repository.

---

## 13. Questions to settle with the team

1. Service token mechanism for `/api/internal/` (shared header proposed) and its environment variable name.
2. JWT algorithm, key distribution, and claim names (must match Identity & Profiles).
3. Whether the internship API returns supervisor contact details or the frontend fetches them from Identity.
4. Whether `Confirmed` should allow a submission, or only `In progress` (current proposal: `In progress` only).
5. Whether the company can see the cancellation reason written by the student, and the reverse.
6. Who receives notifications for each event (proposal: the event list in section 6.6 and section 7).
7. Whether history should be visible to participants as well (current proposal: supervisor and university admin only).
8. Evaluation score precision (decimal with 2 places proposed) and file and link limits (5 each proposed).
