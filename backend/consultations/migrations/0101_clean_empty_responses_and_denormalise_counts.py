from django.db import migrations, models


def clean_empty_free_text(apps, schema_editor):
    """Normalise empty free text to NULL, delete useless responses, and remove orphaned theme assignments."""
    from django.db import connection

    with connection.cursor() as cursor:
        # Normalise all empty/placeholder free text to NULL
        cursor.execute("""
            UPDATE consultations_response
            SET free_text = NULL
            WHERE free_text IN ('', 'Not Provided', '-')
        """)

        # Delete responses with no free text AND no multi-choice options (nothing useful).
        # Cascades to annotations and theme assignments.
        cursor.execute("""
            DELETE FROM consultations_response
            WHERE free_text IS NULL
              AND id NOT IN (
                SELECT response_id FROM consultations_response_chosen_options
              )
        """)

        # Remove theme assignments from responses with no free text
        cursor.execute("""
            DELETE FROM consultations_responseannotationtheme
            WHERE response_annotation_id IN (
                SELECT ra.id FROM consultations_responseannotation ra
                JOIN consultations_response r ON ra.response_id = r.id
                WHERE r.free_text IS NULL
            )
        """)


def backfill_response_counts(apps, schema_editor):
    """Backfill all denormalised response count fields from existing data."""
    from django.db import connection

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
