import os

from django.core.management import BaseCommand

from consultation_analyser.authentication.models import User

class Command(BaseCommand):
    help = "creates initial admin users who can add others"

    def handle(self, *args, **options):
        for email in os.environ.get("ADMIN_USERS", "").split(","):
            User.objects.update_or_create(
                email=email.strip(),
                defaults={'is_staff': True}
            )
