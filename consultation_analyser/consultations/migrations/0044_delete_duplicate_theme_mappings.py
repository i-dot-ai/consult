# Delete the second duplicate theme mapping for each (answer, theme) pair

from django.db import migrations
from django.db.models import Count


class Migration(migrations.Migration):
    def delete_duplicate_theme_mappings(apps, schema_editor):
        ThemeMapping = apps.get_model("consultations", "ThemeMapping")

        # Identify duplicates by grouping and counting entries
        duplicates = (
            ThemeMapping.objects.values("answer", "theme")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        # Keep the first entry and delete the rest
        for d in duplicates:
            theme_mappings = ThemeMapping.objects.filter(
                answer=d["answer"], theme=d["theme"]
            ).order_by("created_at")
            theme_mappings[1:].delete()

    dependencies = [
        ("consultations", "0043_convert_jsonfield_data_to_json"),
    ]

    operations = [
        migrations.RunPython(
            delete_duplicate_theme_mappings, reverse_code=migrations.RunPython.noop, elidable=True
        ),
    ]
