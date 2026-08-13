# Generated manually to handle M2M to through model conversion

from typing import ClassVar

from django.db import migrations


class Migration(migrations.Migration):
    dependencies: ClassVar[list] = [
        ("consultations", "0052_demographicoption_and_more"),
    ]

    operations: ClassVar[list] = [
        migrations.RemoveField(
            model_name="responseannotation",
            name="themes",
        ),
    ]
