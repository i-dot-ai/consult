import json
import logging
import time
from itertools import batched

from django.utils.text import slugify

from consultation_analyser.consultations.public_schema import ConsultationWithResponses

from .models import Answer, Consultation, ConsultationResponse, Question, Section

logger = logging.getLogger("upload")


class Timer:
    def __init__(self):
        self.timings = []
        self.last_time = time.time()

    def time(self, event):
        abs = time.time()
        delta = abs - self.last_time

        logline = (abs, delta, event)
        logger.info(f"{logline}")

        self.timings.append(logline)
        self.last_time = abs
        self.last_delta = delta


def upload_consultation(file, user):
    timer = Timer()
    timer.time("start")

    uploaded_json = file.read()
    timer.time("file read")

    attrs = json.loads(uploaded_json)
    timer.time("file parse")

    consultation_with_responses = ConsultationWithResponses(**attrs)
    timer.time("roundtrip to ConsultationWithResponses")
    del consultation_with_responses
    del uploaded_json

    responses = attrs["consultation_responses"]
    consultation_attrs = attrs["consultation"]
    sections = consultation_attrs.pop("sections")
    timer.time("separated parts")

    consultation_attrs["slug"] = slugify(consultation_attrs["name"])
    consultation = Consultation(**consultation_attrs)
    consultation.save()
    consultation.users.set([user])
    timer.time("created Consultation")

    question_ids_map = {}

    for section_attrs in sections:
        section_attrs["consultation_id"] = consultation.id
        questions = section_attrs.pop("questions")
        section_attrs["slug"] = slugify(section_attrs["name"])
        section = Section(**section_attrs)
        section.save()
        for question_attrs in questions:
            supplied_id = question_attrs.pop("id")
            question_attrs["slug"] = slugify(question_attrs["text"])
            if "multiple_choice" in question_attrs:
                question_attrs["multiple_choice_options"] = question_attrs.pop("multiple_choice")
            question_attrs["section_id"] = section.id
            question = Question(**question_attrs)
            question.save()
            question_ids_map[supplied_id] = question.id
    timer.time("created Sections")

    for responses_batch in batched(responses, 500):
        consultation_responses = []
        answers_attrs = []

        for response_attrs in responses_batch:
            answers_attrs.append(response_attrs.pop("answers"))
            response_attrs["consultation_id"] = consultation.id
            consultation_responses.append(ConsultationResponse(**response_attrs))

        created_responses = ConsultationResponse.objects.bulk_create(consultation_responses)

        offset_to_response_id_map = {
            offset: created.id for offset, created in enumerate(created_responses)
        }

        answers = []

        for offset, answer_list in enumerate(answers_attrs):
            for answer in answer_list:
                if "theme_id" in answer:
                    answer.pop("theme_id")
                answer["consultation_response_id"] = offset_to_response_id_map[offset]
                question_id = answer.pop("question_id")
                answer["question_id"] = question_ids_map[question_id]
                answers.append(Answer(**answer))

        Answer.objects.bulk_create(answers)

    response_count = len(responses)
    timer.time(f"created {response_count} Responses")
    logger.info(f"Time per response: {timer.last_delta / response_count}")

    return consultation
