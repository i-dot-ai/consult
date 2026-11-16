from typing import ClassVar

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies: ClassVar[list] = [
        ("consultations", "0113_question_dashboard_role"),
    ]

    operations: ClassVar[list] = [
        migrations.AddField(
            model_name="consultation",
            name="is_v1",
            field=models.BooleanField(
                default=True,
                help_text="whether this consultation's data was created by the legacy V1 pipeline "
                "setup rather than the V2 survey import flow",
            ),
        ),
        migrations.AddField(
            model_name="consultation",
            name="migrated_at",
            field=models.DateTimeField(
                blank=True,
                default=None,
                help_text="when this consultation was migrated from the V1 schema to the V2 schema",
                null=True,
            ),
        ),
    ]
