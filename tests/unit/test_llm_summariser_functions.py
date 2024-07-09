import string

import pytest
import tiktoken

from consultation_analyser.factories import (
    ConsultationBuilder,
)
from consultation_analyser.pipeline.backends.langchain_llm_backend import (
    get_random_sample_of_responses_for_theme,
)


@pytest.mark.django_db
def test_get_random_sample_of_responses_for_theme():
    encoding = tiktoken.get_encoding("cl100k_base")  # Use arbitrary encoding model
    consultation_builder = ConsultationBuilder()
    question = consultation_builder.add_question()

    answer_text = "Here are my strong opinions on chocolate. I love KitKats."  # 14 tokens

    answer = consultation_builder.add_answer(question, free_text=answer_text)
    theme = consultation_builder.add_theme()

    answer.themes.add(theme)

    combined_responses = get_random_sample_of_responses_for_theme(
        theme, encoding=encoding, max_tokens=40
    )
    assert combined_responses.strip() == answer_text

    for i in range(3):
        answer = consultation_builder.add_answer(question, free_text=answer_text)
        answer.themes.add(theme)

    combined_responses = get_random_sample_of_responses_for_theme(
        theme, encoding=encoding, max_tokens=40
    )

    assert len(encoding.encode(combined_responses)) < 30, combined_responses
    assert combined_responses.count(answer_text) > 1, combined_responses


@pytest.mark.django_db
def test_get_random_sample_of_responses_for_theme_does_not_repeat():
    encoding = tiktoken.get_encoding("cl100k_base")  # Use arbitrary encoding model
    consultation_builder = ConsultationBuilder()
    question = consultation_builder.add_question()
    theme = consultation_builder.add_theme()

    answers = list(string.ascii_lowercase)  # get 27 distinct answers
    for a in answers:
        answer = consultation_builder.add_answer(question, free_text=a)
        answer.themes.add(theme)

    combined_responses = get_random_sample_of_responses_for_theme(
        theme, encoding=encoding, max_tokens=100
    )

    selected_answers = "".join(combined_responses.splitlines())
    assert len(selected_answers) == len(set(selected_answers))
