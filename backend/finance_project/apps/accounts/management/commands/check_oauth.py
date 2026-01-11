"""Management command to setup Google OAuth"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Check and setup Google OAuth configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Google OAuth Configuration Check ===\n'))

        # Check environment variables
        client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
        allowlist_enabled = os.environ.get('ALLOWLIST_ENABLED', 'False')

        self.stdout.write('1. Environment Variables:')
        if client_id:
            self.stdout.write(self.style.SUCCESS(f'   ✓ GOOGLE_CLIENT_ID: {client_id[:20]}...'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ GOOGLE_CLIENT_ID: Not set'))

        if client_secret:
            self.stdout.write(self.style.SUCCESS(f'   ✓ GOOGLE_CLIENT_SECRET: {client_secret[:10]}...'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ GOOGLE_CLIENT_SECRET: Not set'))

        self.stdout.write(f'   • ALLOWLIST_ENABLED: {allowlist_enabled}')
        self.stdout.write('')

        # Check Site configuration
        self.stdout.write('2. Site Configuration:')
        try:
            site = Site.objects.get(pk=settings.SITE_ID)
            self.stdout.write(self.style.SUCCESS(f'   ✓ Site exists: {site.domain} ({site.name})'))

            if site.domain in ['example.com', '127.0.0.1']:
                self.stdout.write(self.style.WARNING('   ⚠ Site domain should be updated to "localhost:8000"'))
                self.stdout.write('   Run: python manage.py setup_site')
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR('   ✗ Site not found'))
            self.stdout.write('   Run: python manage.py setup_site')
        self.stdout.write('')

        # Check SocialApp
        self.stdout.write('3. Google Social Application:')
        google_apps = SocialApp.objects.filter(provider='google')
        if google_apps.exists():
            for app in google_apps:
                self.stdout.write(self.style.SUCCESS(f'   ✓ Found: {app.name}'))
                self.stdout.write(f'     - Client ID: {app.client_id[:20]}...')
                self.stdout.write(f'     - Sites: {", ".join([s.domain for s in app.sites.all()])}')
        else:
            self.stdout.write(self.style.ERROR('   ✗ No Google social application found'))
            self.stdout.write('   Create one in Django admin at /admin/socialaccount/socialapp/')
        self.stdout.write('')

        # Check allauth configuration
        self.stdout.write('4. Allauth Configuration:')
        self.stdout.write(f'   • LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}')
        self.stdout.write(f'   • ACCOUNT_EMAIL_VERIFICATION: {settings.ACCOUNT_EMAIL_VERIFICATION}')
        self.stdout.write(f'   • SOCIALACCOUNT_ADAPTER: {settings.SOCIALACCOUNT_ADAPTER}')
        self.stdout.write('')

        # Check installed apps
        self.stdout.write('5. Required Apps:')
        required_apps = [
            'django.contrib.sites',
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
            'allauth.socialaccount.providers.google',
        ]
        for app in required_apps:
            if app in settings.INSTALLED_APPS:
                self.stdout.write(self.style.SUCCESS(f'   ✓ {app}'))
            else:
                self.stdout.write(self.style.ERROR(f'   ✗ {app}'))
        self.stdout.write('')

        # Final recommendations
        self.stdout.write(self.style.SUCCESS('=== Setup Instructions ===\n'))

        if not client_id or not client_secret:
            self.stdout.write(self.style.WARNING('1. Set up Google OAuth credentials:'))
            self.stdout.write('   - Visit https://console.cloud.google.com/')
            self.stdout.write('   - Create OAuth credentials')
            self.stdout.write('   - Add redirect URI: http://localhost:8000/accounts/google/login/callback/')
            self.stdout.write('   - Update .env file with GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET')
            self.stdout.write('   - Restart Docker services\n')

        if not google_apps.exists():
            self.stdout.write(self.style.WARNING('2. Create Social Application:'))
            self.stdout.write('   - Go to http://localhost:8000/admin/')
            self.stdout.write('   - Navigate to "Social accounts" → "Social applications"')
            self.stdout.write('   - Add new application with Provider: Google')
            self.stdout.write('   - Fill in Client ID and Secret from Google Cloud Console')
            self.stdout.write('   - Select site in "Chosen sites"\n')

        self.stdout.write(self.style.SUCCESS('3. Test the login:'))
        self.stdout.write('   - Visit http://localhost:8000/accounts/google/login/')
        self.stdout.write('   - You should be redirected to Google\n')

        if allowlist_enabled.lower() in ['true', '1', 'yes']:
            self.stdout.write(self.style.WARNING('4. Allowlist is ENABLED:'))
            self.stdout.write('   - Add allowed emails in Django admin')
            self.stdout.write('   - Go to "Accounts" → "Allowed Google Users"\n')

