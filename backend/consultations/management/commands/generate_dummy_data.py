from django.core.management.base import BaseCommand

from authentication.models import User
from consultations.dummy_data import create_dummy_consultation_from_yaml
from consultations.models import Consultation

ADMIN_USER_EMAIL = "admin@example.com"
POLICY_USER_EMAIL = "policy@example.com"


class Command(BaseCommand):
    help = (
        "Generate two dummy consultations, one at finalising themes stage and one at analysis stage. "
        "Generate two dummy users, one with admin (staff) privileges and one without."
    )

    def handle(self, *args, **options):
        self.stdout.write("Generating dummy data...")
        create_dummy_consultation_from_yaml(
            number_respondents=100, consultation_stage=Consultation.Stage.FINALISING_THEMES
        )
        analysis_consultation = create_dummy_consultation_from_yaml(
            number_respondents=100, consultation_stage=Consultation.Stage.ANALYSIS
        )

        # Admin user is not added to any consultation as they can act on all consultations
        _, created = User.objects.update_or_create(
            email=ADMIN_USER_EMAIL, defaults={"is_staff": True}
        )
        self.stdout.write(f"{'Created' if created else 'Updated'} admin user ({ADMIN_USER_EMAIL})")

        policy_user, created = User.objects.update_or_create(
            email=POLICY_USER_EMAIL, defaults={"is_staff": False}
        )
        analysis_consultation.users.add(policy_user)
        self.stdout.write(
            f"{'Created' if created else 'Updated'} policy user ({POLICY_USER_EMAIL})"
        )

        self.stdout.write("Done.")
