# Generated by Django 5.1.4 on 2025-01-17 13:58

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0033_remove_historicalexecutionrun_history_user_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="consultation",
            old_name="text",
            new_name="title",
        ),
    ]
