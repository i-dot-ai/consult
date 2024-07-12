# Generated by Django 5.0.6 on 2024-07-12 11:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0024_consultationfile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="processingrun",
            name="consultation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="consultations.consultationfile",
            ),
        ),
    ]
