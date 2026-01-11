#!/bin/bash
# Quick Google OAuth Setup Helper

echo "=== Google OAuth Setup Helper ==="
echo ""
echo "What would you like to do?"
echo ""
echo "1) Check current OAuth configuration"
echo "2) Update Google credentials in database"
echo "3) Create superuser"
echo "4) Open Django admin in browser"
echo "5) Test login URL"
echo "6) Show environment variables"
echo "7) Full setup guide"
echo ""
read -p "Enter choice [1-7]: " choice

case $choice in
  1)
    echo ""
    echo "Checking OAuth configuration..."
    docker compose -f /Users/matthiasschmid/Projects/finance/deploy/docker-compose.yml exec web python manage.py check_oauth
    ;;
  2)
    echo ""
    echo "Enter your Google OAuth credentials from Google Cloud Console"
    echo ""
    read -p "Client ID: " client_id
    read -p "Client Secret: " client_secret

    docker compose -f /Users/matthiasschmid/Projects/finance/deploy/docker-compose.yml exec web python manage.py shell << EOF
from allauth.socialaccount.models import SocialApp
app = SocialApp.objects.get(provider='google')
app.client_id = '$client_id'
app.secret = '$client_secret'
app.save()
print('✓ Updated Social Application')
print(f'  Client ID: {app.client_id[:30]}...')
EOF

    echo ""
    echo "✓ Credentials updated!"
    echo "Now restart services: docker compose restart web"
    ;;
  3)
    echo ""
    echo "Creating superuser..."
    docker compose -f /Users/matthiasschmid/Projects/finance/deploy/docker-compose.yml exec web python manage.py createsuperuser
    ;;
  4)
    echo ""
    echo "Opening Django admin..."
    open http://localhost:8000/admin/
    ;;
  5)
    echo ""
    echo "Testing login URL..."
    curl -I http://localhost:8000/accounts/google/login/
    echo ""
    echo "Opening in browser..."
    open http://localhost:8000/accounts/google/login/
    ;;
  6)
    echo ""
    echo "Environment variables:"
    docker compose -f /Users/matthiasschmid/Projects/finance/deploy/docker-compose.yml exec web env | grep -E "GOOGLE|ALLOWLIST"
    ;;
  7)
    cat << 'GUIDE'

=== Google OAuth Setup Guide ===

Step 1: Get Google OAuth Credentials
  1. Go to https://console.cloud.google.com/
  2. Create new project or select existing
  3. Enable Google+ API
  4. Configure OAuth consent screen (External, add test users)
  5. Create OAuth client ID (Web application)
  6. Add authorized redirect URI:
     http://localhost:8000/accounts/google/login/callback/
  7. Copy Client ID and Client Secret

Step 2: Update .env file
  cd /Users/matthiasschmid/Projects/finance/deploy
  nano .env  # or use your editor

  Add:
  GOOGLE_CLIENT_ID=your-client-id-here
  GOOGLE_CLIENT_SECRET=your-client-secret-here

Step 3: Update Social Application
  Run option 2 from this menu to update credentials

Step 4: Restart services
  docker compose restart web

Step 5: Test
  Visit: http://localhost:8000/accounts/google/login/

For detailed help, see:
  /Users/matthiasschmid/Projects/finance/google-auth-status-and-setup.md

GUIDE
    ;;
  *)
    echo "Invalid choice"
    ;;
esac

echo ""

