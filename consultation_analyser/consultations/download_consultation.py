import json

from django.forms.models import model_to_dict

from consultation_analyser.consultations.public_schema import (
    ConsultationWithResponses,
)


def select_keys_from_model(model, keys):
    model_attrs = model_to_dict(model)
    return {key: model_attrs[key] for key in keys}


def consultation_to_json(consultation):
    """
    Return the consultation in a format compliant with the public schema

    Raises:
        pydantic.ValidationError: if the generated JSON is not compliant
    """

    attrs = {}

    attrs["consultation"] = select_keys_from_model(consultation, ["name"])

    sections = []
    for section in consultation.section_set.all():
        questions = []
        for question in section.question_set.all():
            question_attrs = select_keys_from_model(question, ["text", "has_free_text", "multiple_choice_options"])
            question_attrs["multiple_choice"] = question_attrs.pop("multiple_choice_options")
            question_attrs["id"] = str(question.id)
            questions.append(question_attrs)

        section_attrs = select_keys_from_model(section, ["name"])
        section_attrs["questions"] = questions
        sections.append(section_attrs)

    attrs["consultation"]["sections"] = sections

    attrs["consultation_responses"] = []
    for response in consultation.consultationresponse_set.all():
        response_attrs = {"submitted_at": response.submitted_at.isoformat()}
        answers = []
        for answer in response.answer_set.all():
            answer_attrs = select_keys_from_model(answer, ["question", "multiple_choice", "free_text"])
            answer_attrs["question_id"] = str(answer_attrs.pop("question"))
            answers.append(answer_attrs)

        response_attrs["answers"] = answers
        attrs["consultation_responses"].append(response_attrs)

    # raise if we're invalid
    ConsultationWithResponses(**attrs)

    return json.dumps(attrs)
