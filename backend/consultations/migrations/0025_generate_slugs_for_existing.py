# Populate slug field for existing ProcessingRuns

import faker as _faker
from django.db import migrations

faker = _faker.Faker()


def populate_processing_run_slug(apps, schema_editor):
    ProcessingRun = apps.get_model("consultations", "ProcessingRun")
    for run in ProcessingRun.objects.all():
        if not run.slug:
            generated_slug = faker.slug()
            while ProcessingRun.objects.filter(
                slug=generated_slug, consultation=run.consultation
            ).exists():
                generated_slug = faker.slug()
            run.slug = generated_slug
        run.save()


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0024_processingrun_finished_at_processingrun_slug_and_more"),
    ]

    operations = [
        migrations.RunPython(
            populate_processing_run_slug, reverse_code=migrations.RunPython.noop, elidable=True
        )
    ]
