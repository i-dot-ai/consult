from typing import Any

from django.conf import settings
from django.db import transaction

from authentication.models import User
from consultations.models import (
    CandidateTheme,
    Consultation,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    SelectedTheme,
)
from hosting_environment import HostingEnvironment

logger = settings.LOGGER


def create_response_from_fixtures(
    respondents, index, question_object, response_data, demographic_questions: dict
):
    free_text = response_data.get("free_text", None)
    response = Response.objects.create(
        respondent=respondents[index],
        question=question_object,
        free_text=free_text,
        text=free_text or None,
    )

    if "chosen_options" in response_data:
        response.chosen_options.set(
            MultiChoiceAnswer.objects.filter(
                question=question_object, text__in=response_data["chosen_options"]
            )
        )

    if "themes" in response_data:
        annotation = ResponseAnnotation.objects.create(
            response=response, evidence_rich=response_data.get("evidence_rich", False)
        )
        annotation.add_original_ai_themes(
            SelectedTheme.objects.filter(question=question_object, key__in=response_data["themes"])
        )

    if "demographics" in response_data:
        for key, value in response_data["demographics"].items():
            option, _ = DemographicOption.objects.get_or_create(
                consultation=question_object.consultation,
                field_name=key,
                field_value=value,
            )
            respondents[index].demographics.add(option)

            demographic_question = demographic_questions[(question_object.consultation.id, key)]
            Response.objects.create(
                respondent=respondents[index],
                question=demographic_question,
                free_text=value,
                text=value,
            )


def _collect_demographic_fields(consultation_data):
    """Demographic field names used anywhere in the fixture's responses."""
    fields = []
    for question in consultation_data.get("questions", []):
        for response in question.get("responses", []):
            for key in response.get("demographics", {}):
                if key not in fields:
                    fields.append(key)
    return fields


def _create_demographic_questions(consultation_object, consultation_data, demographic_questions):
    """Create the v2 demographic-type questions for the fixture's demographic fields.

    Fixtures carry demographics as respondent attributes (the v1 shape); under
    the v2 schema they are responses on `type="demographic"` questions, one
    question per field. Numbered after the fixture's own questions so no
    numbering is stolen from questions seeded later.
    """
    next_number = max(q["number"] for q in consultation_data.get("questions", []))
    for field_name in _collect_demographic_fields(consultation_data):
        next_number += 1
        demographic_questions[(consultation_object.id, field_name)] = Question.objects.create(
            consultation=consultation_object,
            text=field_name,
            number=next_number,
            type=Question.QuestionType.DEMOGRAPHIC,
            has_free_text=False,
            has_multiple_choice=False,
        )


def create_question_from_fixtures(
    consultation_object,
    respondents,
    question_data,
    demographic_questions: dict,
):
    # Use explicit theme_status if provided, otherwise default to DRAFT
    theme_status = Question.ThemeStatus.DRAFT
    if "theme_status" in question_data:
        # Map string values to enum
        status_map = {
            "draft": Question.ThemeStatus.DRAFT,
            "configured": Question.ThemeStatus.CONFIGURED,
            "finalising_themes": Question.ThemeStatus.FINALISING_THEMES,
            "confirmed": Question.ThemeStatus.CONFIRMED,
        }
        theme_status = status_map.get(question_data["theme_status"], Question.ThemeStatus.DRAFT)

    question_object = Question.objects.create(
        consultation=consultation_object,
        text=question_data["text"],
        number=question_data["number"],
        type=(
            Question.QuestionType.OPEN
            if question_data["has_free_text"]
            else Question.QuestionType.CLOSED
        ),
        has_free_text=question_data["has_free_text"],
        has_multiple_choice=question_data["has_multiple_choice"],
        theme_status=theme_status,
    )

    if "multiple_choice_options" in question_data:
        MultiChoiceAnswer.objects.bulk_create(
            MultiChoiceAnswer(question=question_object, text=t)
            for t in question_data["multiple_choice_options"]
        )

    if "themes" in question_data:
        SelectedTheme.objects.bulk_create(
            [
                SelectedTheme(
                    question=question_object,
                    name=t["name"],
                    description=t["description"],
                    key=t["key"],
                )
                for t in question_data["themes"]
            ]
        )

    if "candidate_themes" in question_data:
        CandidateTheme.objects.bulk_create(
            [
                CandidateTheme(
                    question=question_object, name=t["name"], description=t["description"]
                )
                for t in question_data["candidate_themes"]
            ]
        )

    if "responses" in question_data:
        for i, response_data in enumerate(question_data["responses"]):
            create_response_from_fixtures(
                respondents, i, question_object, response_data, demographic_questions
            )

    question_object.update_response_counts()
    MultiChoiceAnswer.update_response_counts(question_object)

    return question_object


def create_respondents_from_fixtures(consultation_data, consultation_object):
    max_respondents = max(
        (len(q.get("responses", [])) for q in consultation_data.get("questions", [])),
        default=0,
    )

    return Respondent.objects.bulk_create(
        [
            Respondent(
                consultation=consultation_object,
                themefinder_id=i + 1,
            )
            for i in range(max_respondents)
        ]
    )


def create_data_from_fixtures(fixtures):
    if HostingEnvironment.is_deployed():
        raise RuntimeError("Fixture data should only be ingested for tests")

    consultations = []
    questions = []

    for consultation_data in fixtures.get("consultations", []):
        with transaction.atomic():
            consultation_object = Consultation.objects.create(
                title=consultation_data["title"],
                stage=consultation_data["stage"],
                code=consultation_data.get("code", ""),
            )

            consultations.append(consultation_object.id)

            for email in consultation_data.get("users", []):
                try:
                    consultation_object.users.add(User.objects.get(email=email))
                except User.DoesNotExist:
                    logger.warning("User {email} does not exist, skipping", email=email)

            respondents = create_respondents_from_fixtures(consultation_data, consultation_object)

            demographic_questions: dict[tuple[Any, str], Question] = {}
            _create_demographic_questions(
                consultation_object, consultation_data, demographic_questions
            )
            for question_data in consultation_data.get("questions", []):
                question_object = create_question_from_fixtures(
                    consultation_object, respondents, question_data, demographic_questions
                )
                questions.append(question_object.id)

            # Make sure that demographic response counts are updated after all responses have been created
            DemographicOption.update_response_counts(consultation_object)
            for demographic_question in demographic_questions.values():
                demographic_question.update_response_counts()

    return {
        "consultation_ids": consultations,
        "question_ids": questions,
    }


def delete_data_from_fixtures(fixtures):
    if HostingEnvironment.is_deployed():
        raise RuntimeError("Fixture data should only be edited for tests")

    Consultation.objects.filter(id__in=fixtures.get("consultation_ids", [])).delete()
