from django.db import migrations


def migrate_legacy_stages(apps, schema_editor):
    Consultation = apps.get_model("consultations", "Consultation")
    Consultation.objects.filter(stage="theme_sign_off").update(stage="finalising_themes")
    Consultation.objects.filter(stage="theme_mapping").update(stage="assigning_themes")


def reverse_migrate_legacy_stages(apps, schema_editor):
    Consultation = apps.get_model("consultations", "Consultation")
    Consultation.objects.filter(stage="finalising_themes").update(stage="theme_sign_off")
    Consultation.objects.filter(stage="assigning_themes").update(stage="theme_mapping")


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0097_candidatethemeresponse"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_stages, reverse_code=reverse_migrate_legacy_stages),
    ]
