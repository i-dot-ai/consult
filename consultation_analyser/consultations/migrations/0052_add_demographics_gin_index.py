# Generated manually to add GIN index for demographics JSONField

from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('consultations', '0051_consultation_question_respondent_response_theme_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='respondent',
            index=GinIndex(
                fields=['demographics'],
                name='respondent_demographics_gin'
            ),
        ),
    ]