import pytest

from consultation_analyser.consultations import models
from consultation_analyser.factories import (
    AnswerFactory,
    ExecutionRunFactory,
    FrameworkFactory,
    QuestionPartFactory,
    ThemeFactory,
    ThemeMappingFactory,
)


@pytest.mark.django_db
def test_get_latest_theme_mappings_for_question_part_returns_latest_mappings():
    question_part = QuestionPartFactory()
    answer = AnswerFactory(question_part=question_part)

    # First theme mapping execution run
    first_framework = FrameworkFactory(question_part=question_part)
    theme1 = ThemeFactory(framework=first_framework)
    first_execution_run = ExecutionRunFactory(type=models.ExecutionRun.TaskType.THEME_MAPPING)
    ThemeMappingFactory(answer=answer, theme=theme1, execution_run=first_execution_run)
    # Second theme mapping execution run
    second_framework = FrameworkFactory(question_part=question_part)
    theme2 = ThemeFactory(framework=second_framework, name="theme 2")
    theme3 = ThemeFactory(framework=second_framework, name="theme 3")
    second_execution_run = ExecutionRunFactory(type=models.ExecutionRun.TaskType.THEME_MAPPING)
    ThemeMappingFactory(answer=answer, theme=theme2, execution_run=second_execution_run)
    ThemeMappingFactory(answer=answer, theme=theme3, execution_run=second_execution_run)

    # Get the latest theme mappings
    latest_mappings = models.ThemeMapping.get_latest_theme_mappings_for_question_part(question_part)
    assert latest_mappings.count() == 2
    assert "theme 2" in latest_mappings.values_list("theme__name", flat=True)
    assert all(mapping.execution_run == second_execution_run for mapping in latest_mappings)


@pytest.mark.django_db
def test_get_latest_theme_mappings_for_question_part_no_mappings():
    question_part = QuestionPartFactory()
    latest_mappings = models.ThemeMapping.get_latest_theme_mappings_for_question_part(question_part)
    assert latest_mappings.count() == 0
