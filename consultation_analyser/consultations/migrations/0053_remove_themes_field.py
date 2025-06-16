# Generated manually to handle M2M to through model conversion

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0052_demographicoption_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="responseannotation",
            name="themes",
        ),
    ]