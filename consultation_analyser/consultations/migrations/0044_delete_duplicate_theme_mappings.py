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

        # Keep the first entry
        theme_mapping_ids_to_keep = []
        for d in duplicates:
            theme_mapping_to_keep = (
                ThemeMapping.objects.filter(answer=d["answer"], theme=d["theme"])
                .order_by("created_at")
                .first()
            )
            theme_mapping_ids_to_keep.append(theme_mapping_to_keep.id)

        # Delete the duplicates that are not in the list of IDs to keep
        for d in duplicates:
            ThemeMapping.objects.filter(answer=d["answer"], theme=d["theme"]).exclude(
                id__in=theme_mapping_ids_to_keep
            ).delete()

    dependencies = [
        ("consultations", "0043_convert_jsonfield_data_to_json"),
    ]

    operations = [
        migrations.RunPython(
            delete_duplicate_theme_mappings, reverse_code=migrations.RunPython.noop, elidable=True
        ),
    ]
