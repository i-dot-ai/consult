import os

from django.core.management import BaseCommand

from consultation_analyser.authentication.models import User

from django.conf import settings

logger = settings.LOGGER


class Command(BaseCommand):
    help = "creates initial admin users who can add others"

    def handle(self, *args, **options):
        for email in os.environ.get("ADMIN_USERS", "").split(","):
            user, created = User.objects.update_or_create(
                email=email.strip(), defaults={"is_staff": True}
            )
            if created:
                logger.info("created {email} as admin", email=user.email)
            else:
                logger.info("set {email} as admin", email=user.email)
