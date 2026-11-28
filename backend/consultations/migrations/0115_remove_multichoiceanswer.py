from typing import ClassVar

from django.db import migrations


def carry_selected_options_to_rows(apps, schema_editor):
    """Give every selected option its Response row on the closed question that holds
    the answers (the question itself, or an open question's closed sibling) before the
    tables that record it go. Options on a question with no such target cannot be
    carried over, so their presence stops the migration."""
    Consultation = apps.get_model("consultations", "Consultation")
    Question = apps.get_model("consultations", "Question")
    Response = apps.get_model("consultations", "Response")
    selected_options = Response.chosen_options.through.objects

    orphaned = 0
    filled_question_ids = set()
    for consultation_id in Consultation.objects.values_list("id", flat=True):
        targets = {}
        for question_id, question_type, closed_question_id in Question.objects.filter(
            consultation_id=consultation_id
        ).values_list("id", "type", "closed_question_id"):
            if question_type == "closed":
                targets[question_id] = question_id
            elif question_type == "open" and closed_question_id:
                targets[question_id] = closed_question_id

        existing_rows = set(
            Response.objects.filter(
                question__consultation_id=consultation_id, question__type="closed"
            ).values_list("question_id", "respondent_id", "text")
        )
        rows = []
        links = (
            selected_options.filter(response__question__consultation_id=consultation_id)
            .values_list(
                "response__question_id", "response__respondent_id", "multichoiceanswer__text"
            )
            .iterator(chunk_size=1000)
        )
        for source_question_id, respondent_id, option_text in links:
            if not option_text:
                continue
            target_id = targets.get(source_question_id)
            if target_id is None:
                orphaned += 1
                continue
            key = (target_id, respondent_id, option_text)
            if key in existing_rows:
                continue
            existing_rows.add(key)
            filled_question_ids.add(target_id)
            rows.append(
                Response(question_id=target_id, respondent_id=respondent_id, text=option_text)
            )
            if len(rows) == 1000:
                Response.objects.bulk_create(rows)
                rows = []
        if rows:
            Response.objects.bulk_create(rows)

    if orphaned:
        raise RuntimeError(
            f"{orphaned} selected options sit on questions with no closed question to hold "
            "them; run migrate_v1_consultations to type those questions, then migrate again"
        )
    refresh_counts(Question, Response, filled_question_ids)


def refresh_counts(Question, Response, filled_question_ids):
    """Recount the questions that received rows and the open questions they answer for,
    the way Question.calculate_response_counts does."""

    def respondents_with_answers(question_id):
        return set(
            Response.objects.filter(question_id=question_id)
            .exclude(text__isnull=True)
            .exclude(text="")
            .values_list("respondent_id", flat=True)
        )

    filled = list(Question.objects.filter(id__in=filled_question_ids))
    for question in filled:
        answering = respondents_with_answers(question.id)
        question.total_response_count = len(answering)
        question.multi_choice_response_count = len(answering)

    answered_through = list(Question.objects.filter(closed_question_id__in=filled_question_ids))
    for question in answered_through:
        answering = respondents_with_answers(question.closed_question_id)
        own = set(
            Response.objects.filter(question_id=question.id).values_list("respondent_id", flat=True)
        )
        question.total_response_count = len(own | answering)
        question.multi_choice_response_count = len(answering)

    Question.objects.bulk_update(
        filled + answered_through, ["total_response_count", "multi_choice_response_count"]
    )


class Migration(migrations.Migration):
    dependencies: ClassVar[list] = [
        ("consultations", "0114_consultation_is_v1_and_migrated_at"),
    ]

    operations: ClassVar[list] = [
        migrations.RunPython(carry_selected_options_to_rows, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="response",
            name="chosen_options",
        ),
        migrations.DeleteModel(
            name="MultiChoiceAnswer",
        ),
    ]
