# Convert JSONField data to JSON from string
import json

from django.db import migrations


def convert_questionpart_options(apps, schema_editor):
    QuestionPart = apps.get_model("consultations", "QuestionPart")
    for qp in QuestionPart.objects.all():
        options = qp.options
        if options and isinstance(options, str):
            qp.options = json.loads(options)
        qp.save()


def convert_respondent_data(apps, schema_editor):
    Respondent = apps.get_model("consultations", "Respondent")
    for respondent in Respondent.objects.all():
        data = respondent.data
        if data and isinstance(data, str):
            respondent.data = json.loads(data)
        respondent.save()


def convert_answer_chosen_options(apps, schema_editor):
    Answer = apps.get_model("consultations", "Answer")
    for answer in Answer.objects.all():
        chosen_options = answer.chosen_options
        if chosen_options and isinstance(chosen_options, str):
            try:
                # without the following line, Django sees chosen_options as a function type
                update = json.loads(chosen_options)
                answer.chosen_options = update
                answer.save()
            except json.JSONDecodeError:  # some options are stored as one-word strings
                answer.chosen_options = json.loads(json.dumps([chosen_options]))
                answer.save()


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0042_respondent_themefinder_respondent_id"),
    ]

    operations = [
        migrations.RunPython(
            convert_questionpart_options, reverse_code=migrations.RunPython.noop, elidable=True
        ),
        migrations.RunPython(
            convert_respondent_data, reverse_code=migrations.RunPython.noop, elidable=True
        ),
        migrations.RunPython(
            convert_answer_chosen_options, reverse_code=migrations.RunPython.noop, elidable=True
        ),
    ]
