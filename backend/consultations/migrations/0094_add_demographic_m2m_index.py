# Generated manually for performance optimization

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0093_consultation_model_name"),
    ]

    operations = [
        # Add composite index on the M2M table between Respondent and DemographicOption
        # This optimizes the reverse lookup: DemographicOption -> Respondent
        # which is used in demographic aggregations queries
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS consultations_respondent_demographics_composite
            ON consultations_respondent_demographics (demographicoption_id, respondent_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS consultations_respondent_demographics_composite;
            """,
        ),
        # Add index on respondent_id for faster filtering in aggregation queries
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS consultations_respondent_demographics_respondent
            ON consultations_respondent_demographics (respondent_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS consultations_respondent_demographics_respondent;
            """,
        ),
    ]
