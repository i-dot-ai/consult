"""
As we change to the new relationships between models, we have to create ProcessingRun and
TopicModel intermediate objects for existing Themes.

For these, blank ProcessingRun and TopicModel will be sufficient.

Also, delete the existing themes that are no longer linked to any Answer.
"""

from django.db import migrations


def add_topic_model_to_themes_for_question(apps, schema_editor, processing_run, question):
    Theme = apps.get_model("consultations", "Theme")
    TopicModel = apps.get_model("consultations", "TopicModel")
    # Only get themes that are attached to existing answers
    answers_for_q = question.answer_set.all()
    corresponding_theme_ids = set(answers_for_q.values_list("theme_id", flat=True))
    # Create a blank topic model to make relationship work between processing run and theme
    topic_model_for_question = TopicModel(question=question, processing_run=processing_run)
    topic_model_for_question.save()
    for id in corresponding_theme_ids:
        theme = Theme.objects.get(id=id)
        theme.topic_model = topic_model_for_question
        theme.save()


def add_processing_run_to_consultation(apps, schema_editor, consultation_id):
    ProcessingRun = apps.get_model("consultations", "ProcessingRun")
    Question = apps.get_model("consultations", "Question")
    processing_run = ProcessingRun(consultation_id=consultation_id)
    processing_run.save()
    free_text_questions = Question.objects.filter(section__consultation_id=consultation_id).filter(
        has_free_text=True
    )
    for question in free_text_questions:
        add_topic_model_to_themes_for_question(apps, schema_editor, processing_run, question)


def add_relationships_for_existing_themes(apps, schema_editor):
    Theme = apps.get_model("consultations", "Theme")
    Answer = apps.get_model("consultations", "Answer")
    all_theme_ids = set(Theme.objects.all().values_list("id", flat=True))
    # Get only themes that are linked to existing answers
    linked_theme_ids = set(Answer.objects.all().values_list("theme_id", flat=True))
    unlinked_theme_ids = all_theme_ids.difference(linked_theme_ids)
    # Consultations we want to update themes on
    consultation_ids = set(
        Theme.objects.filter(id__in=linked_theme_ids).values_list(
            "question__section__consultation", flat=True
        )
    )
    for id in consultation_ids:
        add_processing_run_to_consultation(apps, schema_editor, id)
    # Delete unlinked themes
    Theme.objects.filter(id__in=unlinked_theme_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        (
            "consultations",
            "0018_remove_theme_unique_up_to_question_theme_topic_model_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            add_relationships_for_existing_themes, reverse_code=migrations.RunPython.noop
        ),
    ]
