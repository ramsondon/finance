# Finance Full-Stack Application

A production-ready finance analytics platform with Django 6, DRF, React 18, Tailwind CSS, Celery, Redis, PostgreSQL, and AI-powered insights via Ollama.

**✨ Features a modern admin dashboard design with dark sidebar, gradient cards, and professional UI elements.**

## Features

✅ **Modern Admin Dashboard Design**
- Dark collapsible sidebar with smooth animations
- Gradient statistics cards with visual depth
- Professional navigation with icon-based menu
- Color-coded UI elements (income/expense/transfers)
- Hover effects and smooth transitions
- Responsive grid layouts

✅ **Full-Stack Architecture**
- Backend: Django 6 + Django REST Framework
- Frontend: React 18 + Tailwind CSS (SPA)
- Database: PostgreSQL 16
- Cache & Queue: Redis 7 + Celery
- AI: Ollama for financial insights
- Auth: Google OAuth with allowlist support

✅ **Banking & Analytics**
- Multi-account management with opening balance date support
- Transaction tracking with CSV/JSON import
- Rule-based auto-categorization
- Real-time analytics dashboard
- Income/expense breakdowns
- Monthly trends
- Balance calculations with reference date support

✅ **AI-Powered Insights**
- Pluggable AI provider system
- Default: Ollama (local LLM)
- Financial analysis and suggestions
- Spending pattern detection

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# 1) Start all services
docker compose -f deploy/docker-compose.yml --env-file deploy/.env.example up --build -d

# 2) Create superuser
docker compose -f deploy/docker-compose.yml exec web python manage.py createsuperuser

# 3) Pull an Ollama model (e.g., gemma2:2b)
docker compose exec ollama ollama pull gemma2:2b

# 3) Access the application
open http://localhost:8000
```

### Option 2: Local Development

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
npm run build

# Celery (separate terminal)
celery -A finance_project worker -l info &
celery -A finance_project beat -l info
```

## Application URLs

- **Main App**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs/
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/health

## Frontend Features

The React SPA provides:

- **Dashboard**: Overview of accounts, balances, income/expenses
- **Transactions**: Searchable, filterable transaction list
- **Import**: CSV file upload with background processing
- **Rules**: Auto-categorization rule management
- **AI Insights**: LLM-powered financial analysis

## API Endpoints

### Banking
- `GET/POST /api/banking/accounts/` - Bank account management
- `GET/POST /api/banking/transactions/` - Transaction CRUD
- `POST /api/banking/transactions/import-csv/` - CSV import
- `POST /api/banking/transactions/apply-rules/` - Apply categorization rules
- `GET/POST /api/banking/categories/` - Category management
- `GET/POST /api/banking/rules/` - Rule management

### Analytics
- `GET /api/analytics/overview` - Dashboard statistics

### AI
- `POST /api/ai/insights` - Generate financial insights

### Accounts
- `GET /api/accounts/profiles/` - User profiles
- `GET /api/accounts/allowlist/` - OAuth allowlist
- `GET /api/accounts/auth/me` - Auth status

## Configuration

### Environment Variables

Key settings in `deploy/.env.example`:

```bash
# Database
POSTGRES_DB=finance
POSTGRES_USER=finance
POSTGRES_PASSWORD=finance

# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
ALLOWLIST_ENABLED=False

# AI
OLLAMA_HOST=http://ollama:11434
ACTIVE_AI_PROVIDER=ollama

# Redis/Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
```

### Google OAuth Setup

**Important:** Google OAuth must be configured for the login to work properly.

#### Quick Setup (Recommended)

If you have Google OAuth credentials, add them to your `.env` file and the system will auto-configure:

```bash
# In deploy/.env (create from .env.example)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

Then start the services:

```bash
docker compose -f deploy/docker-compose.yml up -d
```

The `configure_google_oauth` command runs automatically on startup and configures everything.

#### Manual Setup Steps

1. **Get Google OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing
   - Enable "Google+ API"
   - Go to "APIs & Services" → "Credentials"
   - Create "OAuth client ID" (Web application)
   - Add authorized redirect URI: `http://localhost:8000/accounts/google/login/callback/`
   - Copy Client ID and Client Secret

2. **Configure in Application**

   **Option A: Environment Variables (Automatic)**
   ```bash
   # Add to deploy/.env
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   
   # Restart services
   docker compose -f deploy/docker-compose.yml restart web
   ```

   **Option B: Django Admin (Manual)**
   ```bash
   # Create superuser first
   docker compose -f deploy/docker-compose.yml exec web python manage.py createsuperuser
   
   # Go to http://localhost:8000/admin/
   # Navigate to "Social applications" → "Add social application"
   # - Provider: Google
   # - Name: Google OAuth
   # - Client id: (paste your Client ID)
   # - Secret key: (paste your Client Secret)
   # - Sites: Select "localhost:8000"
   # Click Save
   ```

3. **Verify Configuration**
   ```bash
   docker compose -f deploy/docker-compose.yml exec web python manage.py check_oauth
   ```

4. **Test Login**
   - Visit: http://localhost:8000/login
   - Click "Sign in with Google"
   - Should redirect to Google OAuth (not Django login page)

#### Troubleshooting Google OAuth

**Problem:** Clicking "Sign in with Google" shows Django's login page instead of redirecting to Google

**Solution:**
```bash
# 1. Check if credentials are set
docker compose -f deploy/docker-compose.yml exec web env | grep GOOGLE

# 2. Run configuration command manually
docker compose -f deploy/docker-compose.yml exec web python manage.py configure_google_oauth

# 3. Restart web service
docker compose -f deploy/docker-compose.yml restart web

# 4. Check admin for Social Application
open http://localhost:8000/admin/socialaccount/socialapp/
```

**Problem:** "redirect_uri_mismatch" error

**Solution:** In Google Cloud Console, ensure redirect URI exactly matches:
```
http://localhost:8000/accounts/google/login/callback/
```

#### Enable OAuth Allowlist (Optional)

To restrict login to specific Google accounts:

```bash
# 1. Enable in .env
ALLOWLIST_ENABLED=True

# 2. Add allowed emails in Django admin
# Go to: http://localhost:8000/admin/accounts/allowedgoogleuser/
# Add email addresses that should be allowed
```

### AI Provider Configuration

Default is Ollama. To change:

1. Set `ACTIVE_AI_PROVIDER` to your provider name
2. Implement new provider in `backend/finance_project/apps/ai/services/providers/`
3. Register in `insights_service.py`

## Development

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Watch mode (development)
npm run build:css -- --watch &
npm run build:js -- --watch
```

### Running Tests

```bash
# Python tests
docker compose -f deploy/docker-compose.yml exec web pytest

# Or locally
cd backend
pytest
```

### Database Migrations

```bash
# Create migration
docker compose -f deploy/docker-compose.yml exec web python manage.py makemigrations

# Apply migrations
docker compose -f deploy/docker-compose.yml exec web python manage.py migrate
```

## Architecture

### Backend Structure

```
backend/
├── manage.py
├── requirements.txt
├── finance_project/
│   ├── settings_base.py      # Base settings
│   ├── settings.py            # Settings loader
│   ├── urls.py                # URL routing
│   ├── celery.py              # Celery configuration
│   ├── templates/             # Django templates
│   ├── static/                # Built frontend assets
│   └── apps/
│       ├── accounts/          # User management & OAuth
│       ├── banking/           # Accounts, transactions, rules
│       ├── analytics/         # Statistics & insights
│       └── ai/                # AI provider abstraction
```

### Frontend Structure

```
frontend/
├── package.json
├── tailwind.config.js
└── src/
    ├── index.jsx              # App entry point
    └── components/
        ├── Dashboard.jsx
        ├── TransactionsTable.jsx
        ├── ImportCsvModal.jsx
        ├── RulesManager.jsx
        └── InsightsPanel.jsx
```

## Docker Services

- **web**: Django + Gunicorn (port 8000)
- **db**: PostgreSQL 16
- **redis**: Redis 7
- **celery-worker**: Background task processor
- **celery-beat**: Scheduled task scheduler
- **ollama**: AI/LLM service (port 11434)

## CSV Import Format

Expected CSV columns:

```csv
date,amount,description,type,category
2026-01-09,150.00,Salary,income,
2026-01-08,-50.00,Groceries,expense,Food
2026-01-07,-30.00,Gas,expense,Transportation
```

- **date**: YYYY-MM-DD or DD.MM.YYYY
- **amount**: Decimal number
- **description**: Text
- **type**: income, expense, or transfer
- **category**: Optional (will auto-categorize if rules exist)

## Opening Balance Date

When creating a bank account, you can optionally set an **opening_balance_date** to provide a reference point for balance calculations when you have partial transaction history:

**Use Case**: You want to track your account from a known balance point, but don't have all historical transactions. For example, you know your bank account balance was €5,000 two weeks ago.

**Example**:
1. You know your bank account balance was **€5,000** on **2026-01-02** (2 weeks ago)
2. You create the account with:
   - `opening_balance`: €5,000.00
   - `opening_balance_date`: 2026-01-02
3. You import transactions from 2026-01-02 until today (2026-01-10)
4. The system calculates:
   - **Real balance today** = Opening Balance (€5,000) + All transactions from 2026-01-02 to today
   - **Example**: €5,000 + €200 (income) - €150 (expense) = €5,050

**How It Works**:
- **With opening_balance_date**: 
  - Balance calculations use the opening_balance as the baseline for the reference date
  - Only transactions on or after this date are added/subtracted
  - Formula: `Current Balance = opening_balance + SUM(transactions from opening_balance_date to today)`
  
- **Without opening_balance_date**: 
  - Balance assumes you have complete history
  - Calculation includes all transactions from the first transaction onwards
  - Formula: `Current Balance = SUM(all transactions)`

**Key Difference**:
- Use **opening_balance_date** when you have a known historical balance point but incomplete transaction history
- Leave it **empty** when you have all transaction history from day one

## Troubleshooting

### Services won't start

```bash
docker compose -f deploy/docker-compose.yml build web
docker compose -f deploy/docker-compose.yml up -d --force-recreate web

# Check logs
docker compose -f deploy/docker-compose.yml logs web

# Rebuild from scratch
docker compose -f deploy/docker-compose.yml down -v
docker compose -f deploy/docker-compose.yml up --build
```

### Frontend not loading

```bash
# Verify static files exist
docker compose -f deploy/docker-compose.yml exec web ls -la /app/backend/finance_project/static/

# Rebuild frontend
cd frontend && npm run build
```
d
### Database issues

```bash
# Reset database
docker compose -f deploy/docker-compose.yml down -v
docker compose -f deploy/docker-compose.yml up -d
```

## Production Deployment

For production:

1. Set `DJANGO_DEBUG=False`
2. Generate secure `DJANGO_SECRET_KEY`
3. Configure proper `ALLOWED_HOSTS`
4. Set up SSL/HTTPS
5. Use strong database passwords
6. Configure proper CORS origins
7. Set up monitoring and logging
8. Use production-grade WSGI server settings
9. Set up regular database backups
10. Configure proper static file serving (CDN recommended)

## License

This is a scaffold/template project. Customize as needed for your use case.

## Support

For issues or questions:
- Check Docker logs: `docker compose logs [service]`
- Verify environment variables in `.env`
- Ensure all services are healthy: `docker compose ps`
- Run verification script: `./verify-app.sh`

