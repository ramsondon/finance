"""Management command to setup Site for Google OAuth"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup Site configuration for Google OAuth'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            default='localhost:8000',
            help='Domain name for the site (default: localhost:8000)'
        )
        parser.add_argument(
            '--name',
            default='Finance App',
            help='Display name for the site (default: Finance App)'
        )

    def handle(self, *args, **options):
        domain = options['domain']
        name = options['name']

        try:
            site = Site.objects.get(pk=settings.SITE_ID)
            old_domain = site.domain
            old_name = site.name

            site.domain = domain
            site.name = name
            site.save()

            self.stdout.write(self.style.SUCCESS(
                f'✓ Updated Site (ID={site.pk})'
            ))
            self.stdout.write(f'  Old: {old_domain} ({old_name})')
            self.stdout.write(f'  New: {site.domain} ({site.name})')

        except Site.DoesNotExist:
            site = Site.objects.create(
                pk=settings.SITE_ID,
                domain=domain,
                name=name
            )
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created Site (ID={site.pk}): {site.domain} ({site.name})'
            ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Next steps:'))
        self.stdout.write('1. Create a superuser if needed:')
        self.stdout.write('   python manage.py createsuperuser')
        self.stdout.write('')
        self.stdout.write('2. Login to admin and add Social Application:')
        self.stdout.write('   http://localhost:8000/admin/')
        self.stdout.write('')
        self.stdout.write('3. Go to "Social accounts" → "Social applications" → "Add"')
        self.stdout.write('   - Provider: Google')
        self.stdout.write('   - Name: Google OAuth')
        self.stdout.write('   - Client ID: (from Google Cloud Console)')
        self.stdout.write('   - Secret: (from Google Cloud Console)')
        self.stdout.write(f'   - Sites: Select "{site.domain}"')

