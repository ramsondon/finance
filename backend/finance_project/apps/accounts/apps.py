from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "finance_project.apps.accounts"
    label = "accounts"

    def ready(self):
        """
        Register signal handlers when the app is ready.

        Signals:
        - post_save(User) → create_user_profile: Auto-creates UserProfile for new users
        """
        from django.db.models.signals import post_save
        from django.dispatch import receiver
        from django.contrib.auth.models import User
        from .models import UserProfile

        @receiver(post_save, sender=User)
        def create_user_profile(sender, instance, created, **kwargs):
            """
            Automatically create a UserProfile when a new User is created.

            This ensures:
            - Every user has a profile with default preferences
            - Consistent behavior across all endpoints
            - No "profile not found" errors
            - Default preferences available immediately

            Args:
                sender: User model
                instance: The User instance being saved
                created: Boolean indicating if instance was created
                **kwargs: Additional signal arguments
            """
            if created:
                UserProfile.objects.get_or_create(user=instance)

