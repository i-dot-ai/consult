import os

from django.core.management import BaseCommand

from consultation_analyser.authentication.models import User


class Command(BaseCommand):
    help = "creates initial admin users who can add others"

    def handle(self, *args, **options):
        for email in os.environ.get("ADMIN_USERS", "").split(","):
            email = email.strip()
            try:
                user = User.objects.get(email=email)
                user.is_staff = True
                user.save()
            except User.DoesNotExist:
                User.objects.create(email=email, is_staff=True)
