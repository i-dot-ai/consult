# Generated by Django 5.1.5 on 2025-01-28 16:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0036_alter_historicalthememapping_stance_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="answer",
            name="is_theme_mapping_audited",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="thememapping",
            name="execution_run",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="consultations.executionrun",
            ),
        ),
    ]
