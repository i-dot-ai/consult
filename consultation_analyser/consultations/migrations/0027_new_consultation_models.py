# Generated by Django 5.1.4 on 2025-01-05 21:28

import uuid

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0026_processingrun_unique_slug_consultation"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Answer2",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("text", models.TextField()),
                ("chosen_options", models.JSONField(default=list)),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ExecutionRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("sentiment_analysis", "Sentiment Analysis"),
                            ("theme_generation", "Theme Generation"),
                            ("theme_mapping", "Theme Mapping"),
                        ],
                        max_length=32,
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Consultation2",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("text", models.CharField(max_length=256)),
                ("slug", models.SlugField(editable=False, max_length=256)),
                ("users", models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="HistoricalExecutionRun",
            fields=[
                (
                    "id",
                    models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
                ),
                ("created_at", models.DateTimeField(blank=True, editable=False)),
                ("modified_at", models.DateTimeField(blank=True, editable=False)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("sentiment_analysis", "Sentiment Analysis"),
                            ("theme_generation", "Theme Generation"),
                            ("theme_mapping", "Theme Mapping"),
                        ],
                        max_length=32,
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical execution run",
                "verbose_name_plural": "historical execution runs",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalSentimentMapping",
            fields=[
                (
                    "id",
                    models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
                ),
                ("created_at", models.DateTimeField(blank=True, editable=False)),
                ("modified_at", models.DateTimeField(blank=True, editable=False)),
                (
                    "position",
                    models.CharField(
                        choices=[
                            ("Agree", "Agree"),
                            ("Disagree", "Disagree"),
                            ("Unclear", "Unclear"),
                        ],
                        max_length=16,
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "answer",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="consultations.answer2",
                    ),
                ),
                (
                    "execution_run",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="consultations.executionrun",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical sentiment mapping",
                "verbose_name_plural": "historical sentiment mappings",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="Question2",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField(editable=False, max_length=256)),
                ("text", models.TextField()),
                ("order", models.IntegerField(null=True)),
                (
                    "consultation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.consultation2",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="QuestionPart",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("text", models.TextField()),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("free_text", "Free Text"),
                            ("single_option", "Single Option"),
                            ("multiple_options", "Multiple Options"),
                        ],
                        max_length=16,
                    ),
                ),
                ("options", models.JSONField(default=list)),
                ("order", models.IntegerField(null=True)),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.question2",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Framework",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("change_reason", models.CharField(max_length=256)),
                (
                    "execution_run",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.executionrun",
                    ),
                ),
                (
                    "precursor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.framework",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "question_part",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.questionpart",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="answer2",
            name="question_part",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="consultations.questionpart",
            ),
        ),
        migrations.CreateModel(
            name="Respondent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("data", models.JSONField(default=dict)),
                (
                    "consultation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.consultation2",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="answer2",
            name="respondent",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="consultations.respondent",
            ),
        ),
        migrations.CreateModel(
            name="SentimentMapping",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "position",
                    models.CharField(
                        choices=[
                            ("Agree", "Agree"),
                            ("Disagree", "Disagree"),
                            ("Unclear", "Unclear"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "answer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.answer2",
                    ),
                ),
                (
                    "execution_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.executionrun",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Theme2",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=256)),
                ("description", models.TextField()),
                (
                    "framework",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.framework",
                    ),
                ),
                (
                    "precursor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.theme2",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="HistoricalThemeMapping",
            fields=[
                (
                    "id",
                    models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
                ),
                ("created_at", models.DateTimeField(blank=True, editable=False)),
                ("modified_at", models.DateTimeField(blank=True, editable=False)),
                ("reason", models.TextField()),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "answer",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="consultations.answer2",
                    ),
                ),
                (
                    "execution_run",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="consultations.executionrun",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "theme",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="consultations.theme2",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical theme mapping",
                "verbose_name_plural": "historical theme mappings",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="ThemeMapping",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("reason", models.TextField()),
                (
                    "answer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.answer2",
                    ),
                ),
                (
                    "execution_run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.executionrun",
                    ),
                ),
                (
                    "theme",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.theme2",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.AddConstraint(
            model_name="consultation2",
            constraint=models.UniqueConstraint(fields=("slug",), name="unique_consult_slug"),
        ),
        migrations.AddConstraint(
            model_name="question2",
            constraint=models.UniqueConstraint(fields=("slug",), name="unique_q_slug"),
        ),
    ]
