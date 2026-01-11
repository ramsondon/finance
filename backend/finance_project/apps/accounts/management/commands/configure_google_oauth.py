"""Management command to configure Google OAuth automatically from environment variables"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Configure Google OAuth from environment variables'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Configuring Google OAuth ===\n'))

        # Get credentials from environment
        client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR('✗ Google OAuth credentials not found in environment'))
            self.stdout.write('\nPlease set the following environment variables:')
            self.stdout.write('  GOOGLE_CLIENT_ID=your-client-id')
            self.stdout.write('  GOOGLE_CLIENT_SECRET=your-client-secret')
            self.stdout.write('\nOr configure them in Django admin:')
            self.stdout.write('  http://localhost:8000/admin/socialaccount/socialapp/\n')
            return

        # Ensure site exists
        try:
            site = Site.objects.get(pk=settings.SITE_ID)
            if site.domain in ['example.com', '127.0.0.1']:
                site.domain = 'localhost:8000'
                site.name = 'Finance App'
                site.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Updated site: {site.domain}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ Site already configured: {site.domain}'))
        except Site.DoesNotExist:
            site = Site.objects.create(
                pk=settings.SITE_ID,
                domain='localhost:8000',
                name='Finance App'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created site: {site.domain}'))

        # Create or update Google SocialApp
        social_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth',
                'client_id': client_id,
                'secret': client_secret,
            }
        )

        if not created:
            # Update existing
            social_app.client_id = client_id
            social_app.secret = client_secret
            social_app.save()
            self.stdout.write(self.style.SUCCESS('✓ Updated existing Google OAuth app'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Created new Google OAuth app'))

        # Add site to social app
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            self.stdout.write(self.style.SUCCESS(f'✓ Added site {site.domain} to Google OAuth'))

        # Display configuration
        self.stdout.write('\n=== Configuration Complete ===\n')
        self.stdout.write(f'Provider: {social_app.provider}')
        self.stdout.write(f'Name: {social_app.name}')
        self.stdout.write(f'Client ID: {social_app.client_id[:20]}...')
        self.stdout.write(f'Sites: {", ".join([s.domain for s in social_app.sites.all()])}')

        self.stdout.write('\n=== Next Steps ===\n')
        self.stdout.write('1. Make sure redirect URI is configured in Google Cloud Console:')
        self.stdout.write('   http://localhost:8000/accounts/google/login/callback/')
        self.stdout.write('\n2. Test the login:')
        self.stdout.write('   http://localhost:8000/login')
        self.stdout.write('\n3. Click "Sign in with Google" - you should be redirected to Google\n')

