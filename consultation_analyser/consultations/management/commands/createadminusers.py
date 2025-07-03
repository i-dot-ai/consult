import os

from django.core.management import BaseCommand

from consultation_analyser.authentication.models import User

from logging import getLogger

logger = getLogger(__file__)

class Command(BaseCommand):
    help = "creates initial admin users who can add others"

    def handle(self, *args, **options):
        for email in os.environ.get("ADMIN_USERS", "").split(","):
            user, created = User.objects.update_or_create(
                email=email.strip(),
                defaults={'is_staff': True}
            )
            if created:
                logger.info("created %s as admin", user.email)
            else:
                logger.info("set %s as admin", user.email)
