# Pathos PR Opportunity Scoring Engine

A decision-support application for evaluating prospective PR opportunities before a consultancy commits time to pitching them. The future scoring engine will remain rules-based and explainable, with AI-assisted capabilities kept separate from the scoring core.

## Current foundation

The repository establishes the platform on which client, opportunity, scoring, angle, evidence, outcome, authentication, and AI/LLM domains can be built. It intentionally does **not** implement those product features yet.

- Django 6.1 provides the backend and a versioned API foundation.
- Next.js 16 (App Router) provides the frontend shell and reusable UI structure.
- Docker Compose runs the frontend and backend as separate services.
- SQLite remains the default development database; database settings are environment-driven.

## Architecture

```
Browser
  └── Next.js frontend (:3000)
        └── Django API (:8000)
              └── SQLite by default (or a configured Django database backend)
```

The backend domain packages live in `Backend/apps/`. HTTP views are deliberately thin; future business logic belongs in `Backend/services/`. The frontend keeps routes in `app/`, shared UI in `components/`, and API access in `lib/api/`.

## Repository structure

```
Backend/
  apps/             Domain packages and the API endpoint layer
  services/         Reusable business services
  myproject/        Django settings and root URLs
Frontend/pr_scoring_enginge/
  app/              Next.js App Router routes and boundaries
  components/       Shared application and UI components
  lib/api/          Reusable API client
docker-compose.yml  Local two-service orchestration
```

## Environment variables

Use the example files as a list of required values. Django loads `Backend/.env` for local development; deployment platforms should set the same values as environment variables. Next.js loads its local `.env` file. Do not commit either `.env` file.

```powershell
Copy-Item Backend/.env.example Backend/.env
Copy-Item Frontend/pr_scoring_enginge/.env.example Frontend/pr_scoring_enginge/.env
```

Backend variables:

- `DJANGO_DEBUG` — `true` for local development.
- `DJANGO_SECRET_KEY` — required when `DJANGO_DEBUG=false`.
- `DJANGO_ALLOWED_HOSTS` — comma-separated hostnames.
- `DJANGO_TIME_ZONE` — IANA timezone, default `UTC`.
- `DATABASE_ENGINE`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT` — standard Django database configuration. SQLite is the default; another backend also needs its Python driver installed.

- `GEMINI_API_KEY` — Gemini API key used only by Django for information extraction. Add it to `Backend/.env`; it must never have a `NEXT_PUBLIC_` prefix.
- `GEMINI_MODEL` — Gemini model used for extraction, default `gemini-2.5-flash`.

Frontend variables:

- `NEXT_PUBLIC_API_BASE_URL` — browser-visible base URL for the versioned API, default `http://localhost:8000/api/v1`.

## Run with Docker

```bash
docker compose up --build
```

Open `http://localhost:3000` for the frontend. Django is available at `http://localhost:8000`, and its backend container includes a health check. Stop services with `docker compose down`.

## Run locally

Backend (from `Backend/`):

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend (from `Frontend/pr_scoring_enginge/`):

```bash
npm ci
npm run dev
```

## Checks and tests

Backend (from `Backend/`):

```bash
python manage.py check
python manage.py test
```

Frontend (from `Frontend/pr_scoring_enginge/`):

```bash
npm run lint
npx tsc --noEmit
npm run build
```

## API foundation

The public API is versioned under `/api/v1/`. The unauthenticated health endpoint is also exposed at the stable deployment path below:

```http
GET /api/health/
GET /api/v1/health/
```

Both return a successful JSON response containing `"status": "ok"`. Backend API views should use `services.api_responses` for the standard success/error envelopes and keep validation, authorization hooks, and business rules out of views. The frontend centralizes authentication-token injection and API errors in `lib/api/client.ts`.

## Demo login accounts

Running `python manage.py migrate` seeds five development accounts for the login page. Each account uses the password `PathosDemo2026!`.

| Name | Email | Role |
| --- | --- | --- |
| Avery Admin | `admin@pathos.local` | Admin |
| Alex Consultant | `alex@pathos.local` | Consultant |
| Jamie Consultant | `jamie@pathos.local` | Consultant |
| Morgan Consultant | `morgan@pathos.local` | Consultant |
| Taylor Consultant | `taylor@pathos.local` | Consultant |

The admin can promote or demote other users and delete accounts from the dashboard. The last active admin cannot be demoted or deleted.
