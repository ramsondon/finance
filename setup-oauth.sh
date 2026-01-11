#!/bin/bash
# Quick setup script for Google OAuth

set -e

echo "=== Google OAuth Quick Setup ==="
echo ""

# Check if running in Docker
if [ -f "/.dockerenv" ]; then
    echo "✓ Running inside Docker container"
    PYTHON_CMD="python"
else
    echo "✓ Running on host machine"
    PYTHON_CMD="docker compose -f /Users/matthiasschmid/Projects/finance/deploy/docker-compose.yml exec web python"
fi

echo ""
echo "Step 1: Setting up Site configuration..."
$PYTHON_CMD manage.py setup_site --domain=localhost:8000 --name="Finance App"

echo ""
echo "Step 2: Checking OAuth configuration..."
$PYTHON_CMD manage.py check_oauth

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Get Google OAuth credentials from:"
echo "   https://console.cloud.google.com/apis/credentials"
echo ""
echo "2. Update your .env file with:"
echo "   GOOGLE_CLIENT_ID=your-client-id"
echo "   GOOGLE_CLIENT_SECRET=your-client-secret"
echo ""
echo "3. Restart services:"
echo "   docker compose -f deploy/docker-compose.yml restart web"
echo ""
echo "4. Create a superuser (if not done):"
echo "   docker compose -f deploy/docker-compose.yml exec web python manage.py createsuperuser"
echo ""
echo "5. Login to admin and add Social Application:"
echo "   http://localhost:8000/admin/socialaccount/socialapp/add/"
echo "   - Provider: Google"
echo "   - Client ID: (paste from Google)"
echo "   - Secret: (paste from Google)"
echo "   - Sites: Select 'localhost:8000'"
echo ""
echo "6. Test login:"
echo "   http://localhost:8000/accounts/google/login/"
echo ""

