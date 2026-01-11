#!/bin/bash
# Google OAuth Quick Configuration Script

set -e

echo "=== Google OAuth Configuration Helper ==="
echo ""

# Check if we're in the right directory
if [ ! -f "deploy/docker-compose.yml" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Check if services are running
if ! docker compose -f deploy/docker-compose.yml ps web | grep -q "Up"; then
    echo "Starting services..."
    docker compose -f deploy/docker-compose.yml up -d
    echo "Waiting for services to be ready..."
    sleep 15
fi

echo "Step 1: Checking current OAuth configuration..."
docker compose -f deploy/docker-compose.yml exec web python manage.py check_oauth

echo ""
echo "Step 2: Would you like to configure Google OAuth now? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please enter your Google OAuth credentials:"
    echo ""

    echo "Google Client ID:"
    read -r client_id

    echo "Google Client Secret:"
    read -r client_secret

    if [ -z "$client_id" ] || [ -z "$client_secret" ]; then
        echo "Error: Both Client ID and Secret are required"
        exit 1
    fi

    echo ""
    echo "Configuring OAuth..."

    # Update .env file
    if [ ! -f "deploy/.env" ]; then
        cp deploy/.env.example deploy/.env
        echo "Created deploy/.env from example"
    fi

    # Update or add Google OAuth credentials
    if grep -q "GOOGLE_CLIENT_ID=" deploy/.env; then
        sed -i.bak "s/GOOGLE_CLIENT_ID=.*/GOOGLE_CLIENT_ID=$client_id/" deploy/.env
        sed -i.bak "s/GOOGLE_CLIENT_SECRET=.*/GOOGLE_CLIENT_SECRET=$client_secret/" deploy/.env
        rm deploy/.env.bak
    else
        echo "" >> deploy/.env
        echo "# Google OAuth" >> deploy/.env
        echo "GOOGLE_CLIENT_ID=$client_id" >> deploy/.env
        echo "GOOGLE_CLIENT_SECRET=$client_secret" >> deploy/.env
    fi

    echo "✓ Updated deploy/.env with credentials"

    # Restart web service to pick up new environment
    echo "Restarting web service..."
    docker compose -f deploy/docker-compose.yml restart web

    echo "Waiting for service to restart..."
    sleep 10

    # Run configuration command
    echo "Running configuration..."
    docker compose -f deploy/docker-compose.yml exec web python manage.py configure_google_oauth

    echo ""
    echo "=== Configuration Complete! ==="
    echo ""
    echo "✓ OAuth credentials saved to deploy/.env"
    echo "✓ Social application configured in database"
    echo "✓ Site configured as localhost:8000"
    echo ""
    echo "Next steps:"
    echo "1. Ensure your Google Cloud Console has this redirect URI:"
    echo "   http://localhost:8000/accounts/google/login/callback/"
    echo ""
    echo "2. Test the login:"
    echo "   open http://localhost:8000/login"
    echo ""
    echo "3. Click 'Sign in with Google' - you should be redirected to Google"
    echo ""
else
    echo ""
    echo "Configuration skipped. To configure manually:"
    echo ""
    echo "1. Add credentials to deploy/.env:"
    echo "   GOOGLE_CLIENT_ID=your-client-id"
    echo "   GOOGLE_CLIENT_SECRET=your-client-secret"
    echo ""
    echo "2. Restart services:"
    echo "   docker compose -f deploy/docker-compose.yml restart web"
    echo ""
    echo "3. Or configure via Django admin:"
    echo "   http://localhost:8000/admin/socialaccount/socialapp/"
    echo ""
fi

