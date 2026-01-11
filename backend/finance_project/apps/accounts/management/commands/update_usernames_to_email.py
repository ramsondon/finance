"""Management command to update existing users' usernames to their email addresses"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F


class Command(BaseCommand):
    help = 'Update existing user usernames to match their email addresses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if there might be conflicts',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(self.style.SUCCESS('\n=== Update Usernames to Email ===\n'))

        # Find users with email but username doesn't match
        users_to_update = User.objects.filter(
            email__isnull=False
        ).exclude(
            email=''
        ).exclude(
            username=F('email')
        )

        total_users = users_to_update.count()

        if total_users == 0:
            self.stdout.write(self.style.SUCCESS('✓ All users already have email as username!'))
            return

        self.stdout.write(f'Found {total_users} users to update:\n')

        # Check for potential conflicts
        conflicts = []
        for user in users_to_update:
            if User.objects.filter(username=user.email).exclude(pk=user.pk).exists():
                conflicts.append((user, user.email))

        if conflicts:
            self.stdout.write(self.style.WARNING(f'\n⚠ Found {len(conflicts)} potential conflicts:'))
            for user, email in conflicts:
                existing = User.objects.get(username=email)
                self.stdout.write(f'   - Email "{email}" is already used as username by user ID {existing.pk}')

            if not force:
                self.stdout.write(self.style.ERROR('\n✗ Conflicts detected. Use --force to proceed anyway (not recommended)'))
                return
            else:
                self.stdout.write(self.style.WARNING('\n⚠ Proceeding with --force flag'))

        # Display what will be updated
        for user in users_to_update:
            self.stdout.write(f'  {user.pk}: {user.username} → {user.email}')

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n--dry-run mode: No changes made'))
            self.stdout.write(f'Run without --dry-run to apply changes')
            return

        # Confirm before proceeding
        if not force:
            self.stdout.write(self.style.WARNING(f'\nAbout to update {total_users} users.'))
            confirm = input('Continue? (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write('Cancelled.')
                return

        # Update users
        updated = 0
        failed = []

        with transaction.atomic():
            for user in users_to_update:
                try:
                    old_username = user.username
                    user.username = user.email
                    user.save()
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Updated user {user.pk}: {old_username} → {user.email}'))
                except Exception as e:
                    failed.append((user, str(e)))
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to update user {user.pk}: {e}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✓ Successfully updated {updated} users'))

        if failed:
            self.stdout.write(self.style.ERROR(f'✗ Failed to update {len(failed)} users:'))
            for user, error in failed:
                self.stdout.write(f'   - User {user.pk} ({user.username}): {error}')

        self.stdout.write('')
        self.stdout.write('Done!')

