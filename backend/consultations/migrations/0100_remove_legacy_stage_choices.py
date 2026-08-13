from typing import ClassVar

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies: ClassVar[list] = [
        ("consultations", "0099_alter_consultation_stage_default"),
    ]

    operations: ClassVar[list] = [
        migrations.AlterField(
            model_name="consultation",
            name="stage",
            field=models.CharField(
                choices=[
                    ("setup", "Data Setup"),
                    ("finding_themes", "Finding Themes"),
                    ("finalising_themes", "Finalising Themes"),
                    ("assigning_themes", "Assigning Themes"),
                    ("analysis", "Analysis"),
                ],
                default="finalising_themes",
                max_length=32,
            ),
        ),
    ]
