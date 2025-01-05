# Generated by Django 5.1.4 on 2025-01-05 21:56

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0027_new_consultation_models"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Answer",
            new_name="AnswerOld",
        ),
        migrations.RenameModel(
            old_name="Consultation",
            new_name="ConsultationOld",
        ),
        migrations.RenameModel(
            old_name="Question",
            new_name="QuestionOld",
        ),
        migrations.RenameModel(
            old_name="Theme",
            new_name="ThemeOld",
        ),
    ]
