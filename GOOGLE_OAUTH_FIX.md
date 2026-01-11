# 🔧 Google OAuth Redirect Issue - SOLVED

## Problem

When clicking "Sign in with Google" on `/login`, users were redirected to:
```
http://localhost:8000/accounts/google/login/?next=/
```

Instead of being sent directly to Google's OAuth page.

## Root Cause

Django-allauth requires a **SocialApp** (Social Application) to be configured in the database with Google OAuth credentials. When this is missing or credentials are incorrect, allauth shows its own login page instead of redirecting to Google.

## Solution Implemented

I've created an **automatic configuration system** that:

1. ✅ Reads Google OAuth credentials from environment variables
2. ✅ Automatically configures the Site model
3. ✅ Automatically creates/updates the SocialApp in the database
4. ✅ Runs on every container startup
5. ✅ Provides helper commands for manual configuration

## Files Created/Modified

### 1. Management Command
**File:** `backend/finance_project/apps/accounts/management/commands/configure_google_oauth.py`

**Purpose:** Automatically configures Google OAuth from environment variables

**What it does:**
- Reads `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` from environment
- Creates or updates Site to `localhost:8000`
- Creates or updates Google SocialApp with credentials
- Associates SocialApp with the Site
- Displays configuration status

### 2. Docker Compose Update
**File:** `deploy/docker-compose.yml`

**Changed:** Added `configure_google_oauth` to startup command:
```yaml
command: ["bash", "-lc", "python manage.py makemigrations && python manage.py migrate && python manage.py configure_google_oauth && python manage.py collectstatic --noinput && gunicorn finance_project.wsgi:application -b 0.0.0.0:8000"]
```

### 3. Configuration Script
**File:** `configure-oauth.sh`

**Purpose:** Interactive script to help users configure OAuth

**Usage:**
```bash
./configure-oauth.sh
# Prompts for Client ID and Secret
# Updates .env file
# Restarts services
# Configures OAuth automatically
```

### 4. README Update
**File:** `README.md`

**Added:** Comprehensive Google OAuth Setup section with:
- Quick setup instructions
- Manual setup steps
- Troubleshooting guide
- Environment variable configuration

## How to Use

### Option 1: Environment Variables (Recommended)

1. **Get Google OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create OAuth 2.0 Client ID
   - Add redirect URI: `http://localhost:8000/accounts/google/login/callback/`

2. **Add to Environment File**
   ```bash
   # Create/edit deploy/.env
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

3. **Start/Restart Services**
   ```bash
   docker compose -f deploy/docker-compose.yml up -d
   # OR
   docker compose -f deploy/docker-compose.yml restart web
   ```

4. **Test**
   - Visit: `http://localhost:8000/login`
   - Click "Sign in with Google"
   - **Should now redirect directly to Google OAuth!**

### Option 2: Interactive Script

```bash
./configure-oauth.sh
# Follow the prompts
# Enter Client ID and Secret
# Script handles everything
```

### Option 3: Manual Command

```bash
# Export credentials
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"

# Run configuration
docker compose exec web python manage.py configure_google_oauth

# Restart
docker compose restart web
```

### Option 4: Django Admin

```bash
# Create superuser
docker compose exec web python manage.py createsuperuser

# Visit admin
open http://localhost:8000/admin/socialaccount/socialapp/

# Add Social Application:
# - Provider: Google
# - Client ID: (paste)
# - Secret: (paste)
# - Sites: Select "localhost:8000"
```

## Verification

### Check if OAuth is Configured

```bash
docker compose -f deploy/docker-compose.yml exec web python manage.py check_oauth
```

**Expected Output:**
```
=== Google OAuth Configuration Check ===

1. Environment Variables:
   ✓ GOOGLE_CLIENT_ID: abc123...
   ✓ GOOGLE_CLIENT_SECRET: xyz789...

2. Site Configuration:
   ✓ Site exists: localhost:8000 (Finance App)

3. Google Social Application:
   ✓ Found: Google OAuth
     - Client ID: abc123...
     - Sites: localhost:8000

...
```

### Check Environment Variables

```bash
docker compose exec web env | grep GOOGLE
```

Should show:
```
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Test the Login Flow

1. Visit: `http://localhost:8000/login`
2. Click "Sign in with Google"
3. **Should redirect to:** `https://accounts.google.com/o/oauth2/v2/auth?...`
4. Authenticate with Google
5. Redirect back to: `http://localhost:8000/` (dashboard)

## Troubleshooting

### Still Shows Django Login Page

**Check 1: Environment Variables**
```bash
docker compose exec web env | grep GOOGLE
```

If empty, credentials not loaded.

**Solution:**
```bash
# Add to deploy/.env
GOOGLE_CLIENT_ID=your-id
GOOGLE_CLIENT_SECRET=your-secret

# Restart
docker compose restart web
```

**Check 2: Social Application**
```bash
docker compose exec web python manage.py shell
>>> from allauth.socialaccount.models import SocialApp
>>> SocialApp.objects.all()
```

If empty, run:
```bash
docker compose exec web python manage.py configure_google_oauth
```

**Check 3: Site Configuration**
```bash
docker compose exec web python manage.py shell
>>> from django.contrib.sites.models import Site
>>> Site.objects.get(pk=1)
```

Should show: `localhost:8000`

### "redirect_uri_mismatch" Error

**Problem:** Google says redirect URI doesn't match

**Solution:** In Google Cloud Console, add exactly:
```
http://localhost:8000/accounts/google/login/callback/
```

Note the trailing slash!

### Configuration Doesn't Persist

**Problem:** Configuration lost after container restart

**Solution:** 
- SocialApp is stored in database (persists with db volume)
- Environment variables must be in `.env` file (not just shell)
- Check: `deploy/.env` exists and contains credentials

## How It Works

### Startup Flow

```
Container starts
    ↓
Run migrations
    ↓
Run configure_google_oauth command
    ↓
Check for GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET
    ↓
If found:
    - Create/update Site (localhost:8000)
    - Create/update SocialApp (Google)
    - Link SocialApp to Site
    - Display configuration status
    ↓
Start Gunicorn
    ↓
Ready to handle requests
```

### Login Flow (When Configured)

```
User clicks "Sign in with Google"
    ↓
POST to /accounts/google/login/?next=/
    ↓
Django allauth checks for SocialApp
    ↓
✓ Found! Build OAuth URL
    ↓
Redirect to: https://accounts.google.com/o/oauth2/v2/auth?
    client_id=...
    redirect_uri=http://localhost:8000/accounts/google/login/callback/
    scope=email profile
    state=...
    ↓
User authenticates with Google
    ↓
Google redirects to: /accounts/google/login/callback/?code=...&state=...
    ↓
Allauth exchanges code for tokens
    ↓
Create/update Django user
    ↓
Create session
    ↓
Redirect to: / (next parameter)
    ↓
Show Dashboard
```

## Benefits

✅ **Automatic Configuration** - Set env vars, it just works  
✅ **Idempotent** - Safe to run multiple times  
✅ **Startup Integration** - Configures on every container start  
✅ **Helper Scripts** - Interactive and CLI tools  
✅ **Documentation** - Clear instructions in README  
✅ **Troubleshooting** - Built-in check command  

## Environment Variables

Add these to `deploy/.env`:

```bash
# Required for Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Optional - restrict to specific users
ALLOWLIST_ENABLED=False
```

## Commands Reference

```bash
# Configure OAuth
docker compose exec web python manage.py configure_google_oauth

# Check OAuth status
docker compose exec web python manage.py check_oauth

# Setup site
docker compose exec web python manage.py setup_site

# Interactive configuration
./configure-oauth.sh

# Start services
docker compose -f deploy/docker-compose.yml up -d

# Restart web service
docker compose -f deploy/docker-compose.yml restart web

# View logs
docker compose -f deploy/docker-compose.yml logs web
```

## Summary

The issue is now **completely solved**:

1. ✅ **Automatic configuration** from environment variables
2. ✅ **Runs on container startup** (no manual steps needed)
3. ✅ **Helper scripts** for easy setup
4. ✅ **Comprehensive documentation** in README
5. ✅ **Troubleshooting commands** built-in

**To fix your current setup:**

```bash
# 1. Add credentials to deploy/.env
echo "GOOGLE_CLIENT_ID=your-id" >> deploy/.env
echo "GOOGLE_CLIENT_SECRET=your-secret" >> deploy/.env

# 2. Restart web service
docker compose -f deploy/docker-compose.yml restart web

# 3. Test
open http://localhost:8000/login
```

**Now when you click "Sign in with Google", you'll be redirected directly to Google OAuth!** 🎉

