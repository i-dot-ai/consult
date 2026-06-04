import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0101_clean_empty_responses_and_denormalise_counts"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name="response",
            name="read_by",
        ),
        migrations.CreateModel(
            name="ResponseReadBy",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "response",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.response",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("response", "user")},
            },
        ),
        migrations.AddField(
            model_name="response",
            name="read_by",
            field=models.ManyToManyField(
                blank=True,
                through="consultations.ResponseReadBy",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
