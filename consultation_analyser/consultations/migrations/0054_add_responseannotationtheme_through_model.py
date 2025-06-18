# Generated manually to add ResponseAnnotationTheme through model

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0053_remove_themes_field"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ResponseAnnotationTheme",
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
                ("is_original_ai_assignment", models.BooleanField(default=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "response_annotation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.responseannotation",
                    ),
                ),
                (
                    "theme",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.theme",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="responseannotation",
            name="themes",
            field=models.ManyToManyField(
                blank=True,
                through="consultations.ResponseAnnotationTheme",
                to="consultations.theme",
            ),
        ),
        migrations.AddIndex(
            model_name="responseannotationtheme",
            index=models.Index(
                fields=["response_annotation", "is_original_ai_assignment"],
                name="consultatio_respons_cfc7ac_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="responseannotationtheme",
            index=models.Index(
                fields=["theme", "is_original_ai_assignment"],
                name="consultatio_theme_i_16a421_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="responseannotationtheme",
            constraint=models.UniqueConstraint(
                fields=("response_annotation", "theme", "is_original_ai_assignment"),
                name="unique_theme_assignment",
            ),
        ),
    ]
