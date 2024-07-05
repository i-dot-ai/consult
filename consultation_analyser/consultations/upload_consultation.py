import logging
import time

import ijson
import psutil
from django.utils.text import slugify


from .models import Answer, Consultation, ConsultationResponse, Question, Section

logger = logging.getLogger("upload")


class Timer:
    def __init__(self):
        self.last_time = time.time()

    def time(self, event):
        abs = time.time()
        delta = abs - self.last_time
        used_mb = psutil.Process().memory_info().rss / 1024**2

        self.last_time = abs
        self.last_delta = delta

        logline = (abs, delta, used_mb, event)
        logger.info(f"{logline}")


def upload_consultation(file, user):
    timer = Timer()
    timer.time("start")

    sections = []

    consultation_handle = ijson.items(file, "consultation")
    for consultation_attrs in consultation_handle:
        sections = consultation_attrs.pop("sections")
        consultation_attrs["slug"] = slugify(consultation_attrs["name"])
        consultation = Consultation(**consultation_attrs)
        consultation.save()
        consultation.users.set([user])

    del consultation_attrs
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

    del sections
    timer.time("created Sections")

    file.seek(0)
    responses_handle = ijson.items(file, "consultation_responses.item")
    responses_to_process = []

    for i, response in enumerate(responses_handle):
        responses_to_process.append(response)
        if i % 500 == 0:
            process_response_batch(responses_to_process, consultation.id, question_ids_map)
            responses_to_process = []

    timer.time("created Responses")

    return consultation


def process_response_batch(responses_to_process, consultation_id, question_ids_map):
    consultation_responses = []
    answers_attrs = []

    for response_attrs in responses_to_process:
        answers_attrs.append(response_attrs.pop("answers"))
        response_attrs["consultation_id"] = consultation_id
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
