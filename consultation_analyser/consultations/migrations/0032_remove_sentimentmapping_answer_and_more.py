# Generated by Django 5.1.4 on 2025-01-07 14:18

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0031_remove_consultationold_users_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sentimentmapping",
            name="answer",
        ),
        migrations.RemoveField(
            model_name="sentimentmapping",
            name="execution_run",
        ),
        migrations.DeleteModel(
            name="HistoricalSentimentMapping",
        ),
        migrations.DeleteModel(
            name="SentimentMapping",
        ),
    ]
