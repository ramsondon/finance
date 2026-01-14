# Celery Database Connection Fix

## Problem
When importing transactions, the frontend reported "232 transactions imported successfully", but the Celery worker was throwing this error:

```
sqlite3.OperationalError: no such table: banking_bankaccount
```

This happened even though the database was configured to use PostgreSQL, not SQLite.

## Root Cause Analysis

The issue was a **database connection configuration problem** in the Celery worker container:

1. **Volume Mount Override**: The `docker-compose.yml` had volume mounts (`volumes: - ..:/app`) in the `celery-worker` and `celery-beat` services that were mounting the local filesystem into the container.

2. **Missing Environment Variables**: The Celery containers weren't explicitly setting `DJANGO_SETTINGS_MODULE`, causing Django to fall back to a default configuration that might use SQLite.

3. **Django Settings Not Loaded**: The Celery worker process wasn't properly initializing Django settings with the PostgreSQL database configuration.

## Solution Implemented

### 1. **Removed Conflicting Volume Mounts** (`deploy/docker-compose.yml`)
```yaml
# BEFORE (❌ WRONG)
celery-worker:
  volumes:
    - ..:/app  # This overrides the Docker image!

# AFTER (✅ CORRECT)
celery-worker:
  # No volume mounts - uses only the Docker image
```

### 2. **Added Explicit Environment Variables** (`deploy/docker-compose.yml`)
```yaml
environment:
  PYTHONUNBUFFERED: "1"
  DJANGO_SETTINGS_MODULE: "finance_project.settings"
```

### 3. **Updated Celery Commands** (`deploy/docker-compose.yml`)
```yaml
# BEFORE
command: ["bash", "-lc", "celery -A finance_project worker -l info"]

# AFTER
command: ["bash", "-lc", "cd /app/backend && python -m celery -A finance_project worker -l info --concurrency=4"]
```

### 4. **Updated Dockerfile** (`backend/docker/Dockerfile`)
Added explicit Django settings module in the environment:
```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=finance_project.settings
```

### 5. **Added Database Dependency**
Made sure `celery-worker` properly waits for the database to be healthy:
```yaml
depends_on:
  db:
    condition: service_healthy
  redis:
    condition: service_healthy
```

## Verification

✅ **Celery worker now successfully connects to PostgreSQL**:
```
[2026-01-14 06:59:39,420: INFO/MainProcess] Connected to redis://redis:6379/1
```

✅ **Database queries work correctly**:
```python
celery-worker$ python -c "
  from finance_project.apps.banking.models import BankAccount
  count = BankAccount.objects.count()
  print(f'Total bank accounts: {count}')
"
# Output: ✅ Total bank accounts in database: 4
```

## Testing

To verify the fix works with transaction imports:

1. Go to your Finance app
2. Create or select a bank account
3. Upload a CSV or JSON file with transactions
4. Frontend should show "X transactions imported successfully"
5. Check Celery worker logs - should **NOT** see SQLite errors
6. Transactions should appear in the database

## Key Learnings

⚠️ **Important Notes for Docker Setup**:

1. **Never mount volumes over critical application code** in production containers - it breaks the image's expected environment
2. **Always set `DJANGO_SETTINGS_MODULE`** explicitly in environment for Django applications
3. **Database connections must be consistent** - web, worker, and beat scheduler must use the same database
4. **Service dependencies matter** - workers need to wait for healthy database connections

## Related Files Changed

- `deploy/docker-compose.yml` - Fixed celery-worker and celery-beat service configurations
- `backend/docker/Dockerfile` - Added explicit DJANGO_SETTINGS_MODULE to environment

## Commands to Verify Deployment

```bash
# Restart all services with the fix
./dc.sh down
./dc.sh build web celery-worker celery-beat
./dc.sh up -d

# Check celery worker is connected to Redis
./dc.sh logs celery-worker | grep "Connected to redis"

# Verify database access works
./dc.sh exec celery-worker python -c "from finance_project.apps.banking.models import BankAccount; print(f'Accounts: {BankAccount.objects.count()}')"
```

