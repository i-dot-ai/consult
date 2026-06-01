from django.conf import settings
from django.db import connection, migrations, models

logger = settings.LOGGER


def clean_empty_free_text(apps, schema_editor):
    """Normalise empty free text to NULL, delete useless responses, and remove orphaned theme assignments."""
    Response = apps.get_model("consultations", "Response")
    ResponseAnnotationTheme = apps.get_model("consultations", "ResponseAnnotationTheme")

    # Normalise all empty/placeholder free text to NULL (server-side, no memory issue)
    updated = Response.objects.filter(free_text__in=["", "Not Provided", "-"]).update(
        free_text=None
    )
    logger.info(f"Normalised {updated} empty free text values to NULL")

    # Delete responses with no free text AND no multi-choice options, in batches.
    BATCH_SIZE = 5000
    total_deleted = 0
    while True:
        batch_ids = list(
            Response.objects.filter(
                free_text__isnull=True, chosen_options__isnull=True
            ).values_list("id", flat=True)[:BATCH_SIZE]
        )
        if not batch_ids:
            break
        Response.objects.filter(id__in=batch_ids).delete()
        total_deleted += len(batch_ids)
        logger.info(f"Deleted {total_deleted} empty responses so far...")
    logger.info(f"Finished deleting {total_deleted} empty responses")

    # Remove orphaned theme assignments in batches
    total_deleted = 0
    while True:
        batch_ids = list(
            ResponseAnnotationTheme.objects.filter(
                response_annotation__response__free_text__isnull=True
            ).values_list("id", flat=True)[:BATCH_SIZE]
        )
        if not batch_ids:
            break
        ResponseAnnotationTheme.objects.filter(id__in=batch_ids).delete()
        total_deleted += len(batch_ids)
        logger.info(f"Deleted {total_deleted} orphaned theme assignments so far...")
    logger.info(f"Finished deleting {total_deleted} orphaned theme assignments")


def backfill_response_counts(apps, schema_editor):
    """Backfill all denormalised response count fields from existing data."""

    with connection.cursor() as cursor:
        # 1. Question.total_response_count (distinct respondents per question)
        cursor.execute("""
            UPDATE consultations_question AS q
            SET total_response_count = COALESCE(sub.c, 0)
            FROM (
                SELECT question_id, COUNT(DISTINCT respondent_id) AS c
                FROM consultations_response
                GROUP BY question_id
            ) sub
            WHERE q.id = sub.question_id
        """)

        # 2. Question.free_text_response_count
        cursor.execute("""
            UPDATE consultations_question AS q
            SET free_text_response_count = COALESCE(sub.c, 0)
            FROM (
                SELECT question_id, COUNT(*) AS c
                FROM consultations_response
                WHERE free_text IS NOT NULL
                GROUP BY question_id
            ) sub
            WHERE q.id = sub.question_id
        """)

        # 3. Question.multi_choice_response_count
        cursor.execute("""
            UPDATE consultations_question AS q
            SET multi_choice_response_count = COALESCE(sub.c, 0)
            FROM (
                SELECT r.question_id, COUNT(DISTINCT r.id) AS c
                FROM consultations_response r
                INNER JOIN consultations_response_chosen_options rco ON rco.response_id = r.id
                GROUP BY r.question_id
            ) sub
            WHERE q.id = sub.question_id
        """)

        # 4. MultiChoiceAnswer.response_count
        cursor.execute("""
            UPDATE consultations_multichoiceanswer AS mca
            SET response_count = COALESCE(sub.c, 0)
            FROM (
                SELECT multichoiceanswer_id, COUNT(*) AS c
                FROM consultations_response_chosen_options
                GROUP BY multichoiceanswer_id
            ) sub
            WHERE mca.id = sub.multichoiceanswer_id
        """)

        # 5. DemographicOption.response_count
        cursor.execute("""
            UPDATE consultations_demographicoption AS d
            SET response_count = COALESCE(sub.c, 0)
            FROM (
                SELECT demographicoption_id, COUNT(*) AS c
                FROM consultations_respondent_demographics
                GROUP BY demographicoption_id
            ) sub
            WHERE d.id = sub.demographicoption_id
        """)

        # 6. Ensure no NULLs remain before making columns non-nullable
        cursor.execute("""
            UPDATE consultations_question
            SET total_response_count = 0 WHERE total_response_count IS NULL
        """)
        cursor.execute("""
            UPDATE consultations_question
            SET free_text_response_count = 0 WHERE free_text_response_count IS NULL
        """)
        cursor.execute("""
            UPDATE consultations_question
            SET multi_choice_response_count = 0 WHERE multi_choice_response_count IS NULL
        """)


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0100_remove_legacy_stage_choices"),
    ]

    operations = [
        # Step 1: Rename existing field and add new fields (nullable initially)
        migrations.RenameField(
            model_name="question",
            old_name="total_responses",
            new_name="free_text_response_count",
        ),
        migrations.AddField(
            model_name="question",
            name="total_response_count",
            field=models.IntegerField(
                default=0,
                null=True,
                help_text="Number of respondents who answered this question (either part for hybrid questions)",
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="multi_choice_response_count",
            field=models.IntegerField(
                default=0,
                null=True,
                help_text="Number of respondents that selected at least one multi-choice option",
            ),
        ),
        migrations.AddField(
            model_name="multichoiceanswer",
            name="response_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="demographicoption",
            name="response_count",
            field=models.IntegerField(default=0),
        ),
        # Step 2: Clean empty free text (delete or normalise to NULL)
        migrations.RunPython(clean_empty_free_text, migrations.RunPython.noop),
        # Step 3: Backfill all counts (after cleanup so counts are correct)
        migrations.RunPython(backfill_response_counts, migrations.RunPython.noop),
        # Step 4: Make fields non-nullable
        migrations.AlterField(
            model_name="question",
            name="total_response_count",
            field=models.IntegerField(
                default=0,
                help_text="Number of respondents who answered this question (either part for hybrid questions)",
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="free_text_response_count",
            field=models.IntegerField(
                default=0,
                help_text="Number of responses where free text was submitted",
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="multi_choice_response_count",
            field=models.IntegerField(
                default=0,
                help_text="Number of respondents that selected at least one multi-choice option",
            ),
        ),
    ]
