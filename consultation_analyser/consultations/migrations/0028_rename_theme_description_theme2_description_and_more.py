# Generated by Django 5.1.4 on 2025-01-05 21:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0027_answer2_executionrun_consultation2_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="theme2",
            old_name="theme_description",
            new_name="description",
        ),
        migrations.RenameField(
            model_name="theme2",
            old_name="theme_name",
            new_name="name",
        ),
    ]
