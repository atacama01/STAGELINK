# STAGELINK: Project Overview

University internship management platform for one university.

- Institution: M'hamed Bougara University, Boumerdès. Faculty of Sciences, Computer Science Department
- Academic year: 2026–2027
- Team: 5 members, one service each
- Source documents: Cahier des charges fonctionnel (v1.1), Cahier des charges technique (v1.1), Django service quick guide (Member 4)

---

## 1. Purpose

Internship administration is currently spread across email, paper forms and spreadsheets. STAGELINK centralizes it:

- Companies publish internship offers and manage applications to their own offers.
- Students browse offers, apply, track their applications, and confirm at most one internship at a time.
- University administration manages accounts and manually assigns supervisors to confirmed internships. It does not decide company applications.
- Students submit a final report (files and/or links). Supervisors review it and give a score out of 20.
- Role-specific dashboards, individual in-app notifications and an auditable history of important actions.

Out of scope for v1: internal chat, email notifications, advanced statistics, calendar integration, automatic reminders, multi-university support.

---

## 2. Actors

| Actor | Main permissions |
|---|---|
| Guest | Browse public pages and offers. No applications, no offers. |
| Student | Manage profile, browse, apply, confirm or decline company offers, request cancellation, submit final work, view supervisor, feedback, evaluation and notifications. |
| Company | Manage profile, publish/edit/close own offers, accept or reject applications (reason required for rejection), request cancellation or termination of an ongoing internship. |
| University administration | Manage student and supervisor accounts, manually assign supervisors to confirmed internships, decide cancellation requests. Does not accept or reject applications. |
| Supervisor | See assigned students only, review final submissions (approve, or reject with reason), evaluate with a score out of 20 and an optional comment. |
| Platform administrator | Create university and company accounts, manually verify companies before activation. |

---

## 3. Architecture

Frontend: React (role-specific dashboards and user workflows).

Backend: Django and Django REST Framework, split into three microservices:

| Service | Owns |
|---|---|
| Identity & Profiles | Users, roles, authentication and JWT issuing (refresh), student/company/supervisor profiles, university/department/specialty reference data, company verification status |
| Offers & Applications | Internship offers, applications, application status history, company decisions, student confirmation/decline, automatic Withdrawn rule |
| Internship Management | Internships and lifecycle, cancellation requests, supervisor assignment, final submissions and file metadata, reviews, evaluations, notifications, audit/history |

Rules shared by all services:

- Each service has its own Django project and its own PostgreSQL database. One PostgreSQL server hosts all of them.
- Services never read each other's tables. No cross-service joins or foreign keys. Other services' IDs are stored as plain fields.
- Services communicate only through documented synchronous REST APIs. No message broker in v1.
- Each service validates the JWT access token locally and enforces role and object permissions itself.
- Secrets and environment-specific settings come from environment variables and never go into source control.
- Each service has migrations and tests.

Simplified view:

```
            React frontend
                  |  REST + JWT
    +-------------+-------------------+
    |             |                   |
Identity &    Offers &          Internship
Profiles      Applications      Management
    ^             |   ^               |
    |             |   |  create       |
    |             |   |  internship,  |
    |             |   |  active check |
    |             +---+               |
    |                                 |
    +---- notifications, both ways ---+
```

Deployment: Docker Compose on one Linux server, HTTPS terminated at a reverse proxy, persistent volumes for PostgreSQL data and uploaded files.

---

## 4. Core business rules

1. A student may apply to many offers but may confirm only one internship at a time.
2. A student with an active internship (status Confirmed or In progress) cannot submit a new application.
3. Only companies accept or reject applications to their own offers. A rejection requires a reason.
4. When a student confirms an application, the student's other applications still Submitted or Accepted by company become Withdrawn, and those companies are notified.
5. University administration manually assigns a supervisor to each confirmed internship.
6. Supervisors only access internships and students assigned to them.
7. Supervisor rejection of a submission requires a reason. The student must resubmit.
8. Contact between users uses the email and/or phone they provided. No internal chat.

---

## 5. Statuses

Application statuses (Offers & Applications):

```
Submitted ──► Accepted by company ──► Confirmed
    │                 │
    │                 └──────────────► Declined by student
    └────────────────► Rejected by company

Withdrawn: set automatically when the student confirms another internship
(from Submitted or Accepted by company).
Rejected by company, Declined by student, Confirmed and Withdrawn are final.
```

Internship lifecycle (Internship Management):

```
Confirmed ──► In progress ──► Completed
    │              │
    └──────┬───────┘
           ▼
       Cancelled   (only via an approved cancellation request)
```

- Confirmed: created when the student confirms. Supervisor is assigned at this stage.
- In progress: set automatically on the internship start date.
- Completed: set when the supervisor records the evaluation, which requires an approved final submission.
- Cancelled: reached only through an approved cancellation request.

Cancellation requests are separate from the lifecycle. A student or company submits one with a mandatory reason. University administration approves or rejects it. On approval the internship becomes Cancelled and the student can apply again.

Final submission statuses: Submitted → Approved, or Submitted → Rejected (with reason) → Submitted again (resubmission).

---

## 6. Main workflow

1. Company account is created, stays inactive until the platform administrator verifies it.
2. Company completes its profile and publishes an offer.
3. Student browses and applies.
4. Company accepts or rejects (reason required).
5. Student accepts or declines the company's offer.
6. Student confirmation creates the internship. Other applications are set to Withdrawn.
7. University administration assigns a supervisor.
8. During the internship, the status is tracked automatically.
9. At the end, the student submits the final report and files or links.
10. Supervisor approves, or rejects with reason and requests resubmission.
11. Supervisor records a score out of 20 and an optional comment. The internship is marked Completed.

---

## 7. Non-functional requirements

- Interface usable by every role, on current desktop and mobile browsers.
- Role-based access on every protected operation, checked server-side.
- Student records, submissions and evaluations are never public.
- Uploaded files: 10 MB maximum per file. Accepted types: PDF, DOCX, PPTX, JPG/JPEG, PNG, CSV.
- Common dashboard and search API requests complete within 2 seconds on the test dataset, excluding uploads.
- Backup and recovery procedure for database dumps and the file volume.
- Credentials stored securely (hashed passwords only).

---

## 8. Milestones

| Milestone | Deliverable | Deadline |
|---|---|---|
| 1. Framing / Design | Validated functional specs, technology choices, architecture, service boundaries, API approach | 25 October 2026 |
| 2. Prototype / MVP | Working core workflows with initial tests | 22 November 2026 |
| 3. Validation | Finalized code, tests run, defects fixed, setup documented | 6 December 2026 |
| 4. Closure / Delivery | Deployable app, source, migrations, technical docs, demo and oral presentation | 13 December 2026 |

---

## 9. Open decisions for the team

These are not settled in the specifications. Each one affects more than one service, so decide them together early.

1. JWT signing: RS256 with a public key shared with all services, or HS256 with a shared secret. Who distributes it, and through which environment variable?
2. JWT claims: exact names for user ID, role and possibly company or supervisor flags.
3. Service-to-service authentication for `/api/internal/` endpoints: shared service token in a header, or service-level JWTs. Proposed: a shared `INTERNAL_SERVICE_TOKEN` header, compared in constant time.
4. Contact information: should the internship API return supervisor contact details, or should the frontend fetch them from Identity & Profiles?
5. Whether companies may see final submission files. The spec limits companies to application information for their own offers, so the default here is no.
6. Evaluation score type: integer or decimal (for example 14.5). Proposed: decimal with 2 places, range 0 to 20.
7. Maximum number of files and links per submission (not specified). Proposed: 5 files and 5 links.
8. Repository layout: one monorepo or one repository per service. The spec requires a shared repository workflow.
9. Exact library versions (React, Django, DRF, PostgreSQL) to record in the README once chosen.
10. Cover-page placeholders still to complete: group member names and supervisor name.
