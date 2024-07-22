# Populate slug field for existing ProcessingRuns

from django.db import migrations


def populate_processing_run_slug(apps, schema_editor):
    ProcessingRun = apps.get_model("consultations", "ProcessingRun")
    all_runs = ProcessingRun.objects.all()
    for run in all_runs:
        run.save()
        # Save should generate a unique slug


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0024_processingrun_finished_at_processingrun_slug_and_more"),
    ]

    operations = [
        migrations.RunPython(
            populate_processing_run_slug, reverse_code=migrations.RunPython.noop, elidable=True
        )
    ]
