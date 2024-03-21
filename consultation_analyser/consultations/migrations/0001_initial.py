# Generated by Django 5.0.3 on 2024-03-21 11:03

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Consultation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=256)),
                ("slug", models.CharField(max_length=256)),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Theme",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("label", models.CharField(blank=True, max_length=256)),
                ("summary", models.TextField(blank=True)),
                ("keywords", models.JSONField(default=list)),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ConsultationResponse",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "consultation",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="consultations.consultation"),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Section",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("name", models.TextField()),
                ("slug", models.CharField(max_length=256)),
                (
                    "consultation",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="consultations.consultation"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("text", models.CharField()),
                ("slug", models.CharField(max_length=256)),
                ("has_free_text", models.BooleanField(default=False)),
                ("multiple_choice_options", models.JSONField(null=True)),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="consultations.section")),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Answer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("multiple_choice_responses", models.JSONField(null=True)),
                ("free_text", models.TextField(null=True)),
                (
                    "consultation_response",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="consultations.consultationresponse"
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="consultations.question"),
                ),
                (
                    "theme",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="consultations.theme"),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.AddConstraint(
            model_name="section",
            constraint=models.UniqueConstraint(fields=("slug", "consultation"), name="unique_section_consultation"),
        ),
        migrations.AddConstraint(
            model_name="question",
            constraint=models.UniqueConstraint(fields=("slug", "section"), name="unique_question_section"),
        ),
    ]
