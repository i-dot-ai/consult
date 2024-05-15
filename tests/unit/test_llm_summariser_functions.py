import pytest
import tiktoken

from consultation_analyser.factories import AnswerFactory, QuestionFactory, ThemeFactory
from consultation_analyser.pipeline.llm_summariser import get_random_sample_of_responses_for_theme


@pytest.mark.django_db
def test_get_random_sample_of_responses_for_theme():
    encoding = tiktoken.get_encoding("cl100k_base")  # Use arbitrary encoding model
    question = QuestionFactory(has_free_text=True)
    theme = ThemeFactory(question=question)
    text = "Here are my strong opinions on chocolate. I love KitKats."  # 14 tokens
    AnswerFactory(question=question, theme=theme, free_text=text)
    combined_responses = get_random_sample_of_responses_for_theme(theme, encoding=encoding, max_tokens=40)
    assert combined_responses.strip() == text

    # Now test that we combine multiple responses but don't exceed limit.
    for i in range(3):
        AnswerFactory(question=question, theme=theme, free_text=text)
    combined_responses = get_random_sample_of_responses_for_theme(theme, encoding=encoding, max_tokens=40)
    assert len(encoding.encode(combined_responses)) < 30, combined_responses
    assert combined_responses.count(text) > 1, combined_responses
