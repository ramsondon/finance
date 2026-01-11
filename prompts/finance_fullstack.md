Role
You are an expert full-stack generator for finance software. Your goal is to scaffold a production-ready application per the spec below, with a secure, maintainable architecture and runnable Docker-based setup.

High-Level Goals
- Build a web app to analyze bank accounts and transactions.
- Provide Google OAuth login with configurable allowlist vs any Google user.
- Support multiple accounts per user, transactions per account, CSV import, rule-based auto-categorization.
- Show statistics: total balance, income vs expenses, monthly trends.
- Provide an AI Insights Service abstraction with default Ollama provider; easily swap AI providers.
- Modern, responsive UI using React rendered via Django templates with Django 6 partials and Tailwind.
- Use Docker Compose for all services: web (Django), db (Postgres), redis, celery worker/beat, ollama.
- Separate settings_local.py (gitignored) to override secrets.

Architecture
- Backend: Python 3.13, Django 6.x, Django REST Framework (DRF), PostgreSQL, Celery + Redis.
- Frontend: React components mounted via Django templates and Django 6 partials; TailwindCSS for styling.
- Auth: Google OAuth2 via django-allauth or social-auth-app-django; enforce configurable allowlist.
- AI: InsightsService abstraction with provider interface; default provider uses Ollama (dev: localhost; prod: Docker container). HTTP-based communication, pluggable providers.
- Background tasks: CSV parsing, categorization rules application, scheduled stats computation.
- Configuration: settings_base.py + settings_local.py (gitignored) + environment variables; 12-Factor style.

Deliverables the AI must generate
- Repository structure with minimal runnable stubs and docs.
- Dockerfiles, docker-compose.yml with web, db, redis, celery worker/beat, ollama.
- Django project and apps (accounts, banking, analytics, ai).
- DRF serializers, viewsets, URLs; React components and Django templates/partials; Tailwind setup.
- Google OAuth configuration with allowlist setting and admin controls.
- CSV import endpoints and background processing with Celery.
- Rule engine for auto-categorization (user-configurable rules stored in DB).
- InsightsService abstraction with Ollama provider and provider registry.
- Tests (unit + integration), basic GitHub Actions CI, README with setup commands.

File/Folder Structure
- backend/
  - manage.py
  - requirements.txt (pin Django 6.x, djangorestframework, django-allauth or social-auth-app-django, psycopg2-binary, celery, redis, python-dotenv, whitenoise, gunicorn, drf-spectacular, django-environ, pandas or python-csv libs, requests)
  - docker/Dockerfile
  - finance_project/
    - settings_base.py
    - settings_local.py (gitignored)
    - settings.py (loads base + local if present)
    - urls.py
    - asgi.py
    - wsgi.py
    - templates/
      - base.html
      - partials/
        - ReactBankDashboard.partial.html (mount point for React dashboard)
    - static/
      - tailwind.css (built via tailwind CLI)
    - apps/
      - accounts/ (users + OAuth settings)
        - models.py (UserProfile, AllowedGoogleUser)
        - admin.py
        - serializers.py
        - views.py
        - urls.py
      - banking/
        - models.py (BankAccount, Transaction, Category, Rule)
        - admin.py
        - serializers.py
        - views.py (ViewSets + CSV import endpoint)
        - urls.py
        - services/
          - csv_importer.py (parse CSV to transactions)
          - rule_engine.py (apply categorization rules)
      - analytics/
        - services/
          - stats_service.py (balances, income vs expenses, monthly trends)
        - views.py (stats endpoints)
        - serializers.py
        - urls.py
      - ai/
        - services/
          - insights_service.py (abstract base: interface + registry)
          - providers/
            - ollama_provider.py (HTTP calls to Ollama; configurable host)
            - mock_provider.py (for tests)
        - views.py (endpoint to request insights)
        - serializers.py
        - urls.py
- frontend/
  - package.json (React + Tailwind + build scripts)
  - src/
    - index.jsx
    - components/
      - Dashboard.jsx (account overview, stats cards)
      - TransactionsTable.jsx
      - ImportCsvModal.jsx
      - RulesManager.jsx
      - InsightsPanel.jsx
  - tailwind.config.js
  - postcss.config.js
- deploy/
  - docker-compose.yml
  - .env.example
- .gitignore (includes backend/finance_project/settings_local.py, env files, node_modules)
- README.md
- .github/workflows/ci.yml (lint, tests)

Data Models (Django ORM)
- UserProfile: user (OneToOne), currency_preference, preferences.
- AllowedGoogleUser: email (unique), active.
- BankAccount: user (FK to auth.User), name, institution, currency, opening_balance, created_at.
- Transaction: account (FK), date, amount (decimal), description, category (FK nullable), type (income/expense/transfer), meta (JSON), created_at.
- Category: user (FK), name, color.
- Rule: user (FK), name, conditions (JSON; e.g., description contains, amount ranges, date ranges), category (FK), priority, active.

API Contracts (DRF)
- Auth: Google OAuth login endpoint + callback; setting allowlist_enabled (bool) to restrict by AllowedGoogleUser.
- Accounts: CRUD for BankAccount; list filtered by current user.
- Transactions: CRUD; bulk import; pagination; filtering by date range, amount, category.
- Categories: CRUD; list.
- Rules: CRUD; apply rules to uncategorized transactions via background task.
- Analytics: GET /stats/overview -> { total_balance, income_expense_breakdown, monthly_trends } per user.
- AI Insights: POST /ai/insights -> { suggestions: [string], analysis: string }; input: timeframe, categories of interest.
- Error format: consistent JSON with code, message, details.
- OpenAPI schema via drf-spectacular.

Rule Engine
- Conditions support: substring match in description, amount range, date range, category presence, transaction type.
- Priority order; first match applies; idempotent behavior.
- Background task: apply rules to newly imported transactions; retries with exponential backoff on transient errors.

CSV Import
- Endpoint accepts CSV file with headers: date, amount, description, type, category (optional).
- Parsing: handle common date formats (YYYY-MM-DD, DD.MM.YYYY), decimal separators; configurable via settings.
- Validation: reject malformed rows, collect errors; enqueue valid rows to Celery task for persistence and rule application.

AI Insights Service
- insights_service.py defines Provider interface: generate_insights(user_id, context) -> InsightsResult.
- Default provider: OllamaProvider with configurable host (env OLLAMA_HOST); dev default http://localhost:11434; prod internal service name http://ollama:11434.
- Provider registry keyed by provider name; settings include ACTIVE_AI_PROVIDER.
- Resilient: timeouts, retries, circuit-breaker-like simple failover to mock provider for tests.

Security, Scalability, Maintainability
- Use Django security middleware, secure cookies, CSRF protection, HTTPS in prod, allowed hosts.
- Separate settings for dev/prod; secrets via env loaded in settings_local.py.
- DB migrations; indexes on Transaction(date, amount, account_id) and Category; query optimization.
- Celery worker/beat with concurrency tuned by env; retry policies.
- Logging: structured logs, request IDs.
- Pagination and rate limiting via DRF.

Docker/Compose
- Services: web (Django + gunicorn), db (Postgres), redis, celery-worker, celery-beat, ollama.
- Healthchecks for db/redis/web.
- Volumes for db data; bind mounts for dev.
- Environment: .env with secrets; web reads settings_local.py and env.
- Dev: web runs collectstatic, tailwind build; uses local Ollama.
- Prod: web connects to ollama service; static served via whitenoise.

Settings
- settings_base.py: base config, installed apps, middleware, DRF, Celery, Tailwind static config.
- settings_local.py: overrides sensitive values (DB creds, Google OAuth client ID/secret, OLLAMA_HOST, ACTIVE_AI_PROVIDER, allowlist_enabled).
- settings.py: load base, then attempt to import local overrides.

Testing and CI
- Tests: models, serializers, views, rule engine, CSV importer, insights service (mock provider), analytics computations.
- GitHub Actions: Python setup, pip install, run flake8/black/isort, pytest with coverage; node setup for frontend lint/build.

Commands the AI must include in README
- Dev run:
  - Docker: docker compose up --build
  - Django: python backend/manage.py migrate && python backend/manage.py runserver
  - Celery: celery -A finance_project worker -l info & celery -A finance_project beat -l info
  - Frontend build: npm --prefix frontend install && npm --prefix frontend run build
- Create superuser and add AllowedGoogleUser if allowlist is enabled.

Acceptance Criteria
- Docker compose boots all services; web reachable; /health endpoint returns OK.
- Google OAuth login works; allowlist respected when enabled.
- User can create accounts, import transactions via CSV, see categorized transactions.
- Stats endpoints return correct aggregates; React dashboard renders stats via Django partial.
- AI insights endpoint returns suggestions using Ollama in dev and container in prod.
- Tests pass in CI; README explains setup.

Instructions
- Generate the full scaffold and minimal runnable code with stubs sufficient to start containers and hit basic endpoints.
- Use pinned, stable versions for dependencies.
- Keep the code modular and documented with brief docstrings.
- Ensure the app can talk to Ollama both at localhost:11434 and via the Docker service name.

