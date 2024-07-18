# Populate slug field for existing ProcessingRuns

from django.db import migrations
from wonderwords import RandomWord


def generate_random_slug():
    word1 = RandomWord().word().lower()
    word2 = RandomWord().word().lower()
    slug = f"{word1}-{word2}"
    return slug


def populate_processing_run_slug(apps, schema_editor):
    ProcessingRun = apps.get_model("consultations", "ProcessingRun")
    all_runs = ProcessingRun.objects.all()
    number_runs = all_runs.count()
    slugs = set()
    while len(slugs) < number_runs:
        slug = generate_random_slug()
        slugs.add(slug)

    for z in zip(all_runs, slug):
        z[0].slug = z[1]
        z[0].save()


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0024_processingrun_finished_at_processingrun_slug_and_more"),
    ]

    operations = [
        migrations.RunPython(
            populate_processing_run_slug, reverse_code=migrations.RunPython.noop, elidable=True
        )
    ]
