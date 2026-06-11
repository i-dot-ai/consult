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


def create_response_from_fixtures(respondents, index, question_object, response_data):
    response = Response.objects.create(
        respondent=respondents[index],
        question=question_object,
        free_text=response_data["free_text"] if "free_text" in response_data else None,
    )

    if "chosen_options" in response_data:
        response.chosen_options.set(
            MultiChoiceAnswer.objects.filter(
                question=question_object, text__in=response_data["chosen_options"]
            )
        )

    if "themes" in response_data:
        annotation = ResponseAnnotation.objects.create(
            response=response,
            evidence_rich=response_data.get("evidence_rich", False)
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


def create_question_from_fixtures(consultation_object, respondents, question_data):
    # Set theme_status to CONFIRMED if consultation is in analysis stage and has themes
    theme_status = Question.ThemeStatus.DRAFT
    if "themes" in question_data and consultation_object.stage == Consultation.Stage.ANALYSIS:
        theme_status = Question.ThemeStatus.CONFIRMED

    question_object = Question.objects.create(
        consultation=consultation_object,
        text=question_data["text"],
        number=question_data["number"],
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
                    question=question_object,
                    name=t["name"],
                    description=t["description"]
                )
                for t in question_data["candidate_themes"]
            ]
        )

    if "responses" in question_data:
        for i, response_data in enumerate(question_data["responses"]):
            create_response_from_fixtures(respondents, i, question_object, response_data)

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
            )

            consultations.append(consultation_object.id)

            for email in consultation_data.get("users", []):
                try:
                    consultation_object.users.add(User.objects.get(email=email))
                except User.DoesNotExist:
                    logger.warning(f"User {email} does not exist, skipping")

            respondents = create_respondents_from_fixtures(consultation_data, consultation_object)

            for question_data in consultation_data.get("questions", []):
                question_object = create_question_from_fixtures(consultation_object, respondents, question_data)
                questions.append(question_object.id)

            # Make sure that demographic response counts are updated after all responses have been created
            DemographicOption.update_response_counts(consultation_object)

    return {
        "consultation_ids": consultations,
        "question_ids": questions,
    }


def delete_data_from_fixtures(fixtures):
    if HostingEnvironment.is_deployed():
        raise RuntimeError("Fixture data should only be edited for tests")

    Consultation.objects.filter(id__in=fixtures.get("consultation_ids", [])).delete()
