import pytest

from consultation_analyser.consultations.models import (
    CandidateTheme,
    CrossCuttingTheme,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)
from consultations.services import clone_consultation
from consultation_analyser.factories import (
    CandidateThemeFactory,
    ConsultationFactory,
    MultiChoiceAnswerFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
    SelectedThemeFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestCloneConsultation:
    def test_consultation(self):
        user1 = UserFactory()
        user2 = UserFactory()
        original = ConsultationFactory(title="Original Consultation", code="original_consultation")
        original.users.add(user1, user2)

        cloned = clone_consultation(original)

        assert cloned.title == "Original Consultation (Clone)"
        assert cloned.code == ""
        assert cloned.stage == original.stage
        assert set(cloned.users.all()) == {user1, user2}

    def test_respondents_and_demographics(self):
        original = ConsultationFactory()
        demo1 = DemographicOption.objects.create(
            consultation=original, field_name="region", field_value="north"
        )
        demo2 = DemographicOption.objects.create(
            consultation=original, field_name="age", field_value="25-34"
        )
        respondent = RespondentFactory(consultation=original, themefinder_id=123, name="Test User")
        respondent.demographics.add(demo1, demo2)

        cloned = clone_consultation(original)

        cloned_respondent = Respondent.objects.get(consultation=cloned)
        cloned_demograhics = cloned_respondent.demographics.all()
        assert cloned_respondent.themefinder_id == 123
        assert cloned_respondent.name == "Test User"
        assert cloned_respondent.demographics.count() == 2
        # Verify they are new objects
        assert demo1.id not in [d.id for d in cloned_demograhics]
        assert demo2.id not in [d.id for d in cloned_demograhics]

    def test_questions_and_multi_choice_answers(self):
        original = ConsultationFactory()
        question = QuestionFactory(consultation=original, has_multiple_choice=True)
        answer1 = MultiChoiceAnswerFactory(question=question, text="Option A")
        answer2 = MultiChoiceAnswerFactory(question=question, text="Option B")

        cloned = clone_consultation(original)

        cloned_question = Question.objects.get(consultation=cloned)
        cloned_answers = MultiChoiceAnswer.objects.filter(question=cloned_question)
        assert cloned_answers.count() == 2
        assert cloned_answers.filter(text="Option A").exists()
        assert cloned_answers.filter(text="Option B").exists()
        # Verify they are new objects
        assert answer1.id not in [a.id for a in cloned_answers]
        assert answer2.id not in [a.id for a in cloned_answers]

    def test_themes(self):
        original = ConsultationFactory()
        question = QuestionFactory(consultation=original)
        cross_cutting_theme = CrossCuttingTheme.objects.create(
            consultation=original, name="Cross Cutting Theme", description="Description"
        )
        user = UserFactory()
        selected_theme = SelectedThemeFactory(
            question=question,
            name="Theme 1",
            crosscuttingtheme=cross_cutting_theme,
            last_modified_by=user,
        )
        candidate_theme = CandidateThemeFactory(
            question=question, name="Parent Theme", parent=None, selectedtheme=selected_theme
        )
        CandidateThemeFactory(question=question, name="Child Theme", parent=candidate_theme)

        cloned = clone_consultation(original)

        cloned_question = Question.objects.get(consultation=cloned)
        cloned_selected_theme = SelectedTheme.objects.get(question=cloned_question)
        cloned_cct = CrossCuttingTheme.objects.get(consultation=cloned)

        assert cloned_selected_theme.name == "Theme 1"
        assert cloned_selected_theme.last_modified_by == user
        assert cloned_selected_theme.crosscuttingtheme == cloned_cct

        cloned_candidate_themes = CandidateTheme.objects.filter(question=cloned_question)
        cloned_parent = cloned_candidate_themes.get(name="Parent Theme")
        cloned_child = cloned_candidate_themes.get(name="Child Theme")

        assert cloned_parent.selectedtheme == cloned_selected_theme
        assert cloned_parent.parent is None
        assert cloned_child.parent == cloned_parent

    def test_responses_and_chosen_options(self):
        original = ConsultationFactory()
        question = QuestionFactory(
            consultation=original, has_free_text=True, has_multiple_choice=True
        )
        answer = MultiChoiceAnswerFactory(question=question, text="Option A")
        respondent = RespondentFactory(consultation=original)
        response = ResponseFactory(
            question=question,
            respondent=respondent,
            free_text="Test response",
        )
        response.chosen_options.add(answer)

        cloned = clone_consultation(original)

        cloned_question = Question.objects.get(consultation=cloned)
        cloned_response = Response.objects.get(question=cloned_question)
        cloned_answer = cloned_response.chosen_options.first()

        assert cloned_response.free_text == "Test response"
        assert cloned_response.chosen_options.count() == 1

        assert cloned_answer.text == "Option A"
        assert cloned_answer.id != answer.id

    def test_response_annotations_and_themes(self):
        original = ConsultationFactory()
        question = QuestionFactory(consultation=original)
        respondent = RespondentFactory(consultation=original)
        user = UserFactory()
        theme = SelectedTheme.objects.create(
            question=question, name="Theme 1", description="Description"
        )
        response = ResponseFactory(question=question, respondent=respondent)
        annotation = ResponseAnnotation.objects.create(response=response)
        rat = ResponseAnnotationTheme.objects.create(
            response_annotation=annotation, theme=theme, assigned_by=user
        )

        cloned = clone_consultation(original)

        cloned_question = Question.objects.get(consultation=cloned)
        cloned_theme = SelectedTheme.objects.get(question=cloned_question)
        cloned_response = Response.objects.get(question=cloned_question)
        cloned_annotation = ResponseAnnotation.objects.get(response=cloned_response)
        cloned_rat = ResponseAnnotationTheme.objects.get(response_annotation=cloned_annotation)

        assert cloned_rat.theme == cloned_theme
        assert cloned_rat.assigned_by == user
        assert cloned_rat.id != rat.id

    def test_response_read_by_is_not_cloned(self):
        original = ConsultationFactory()
        question = QuestionFactory(consultation=original)
        respondent = RespondentFactory(consultation=original)
        user = UserFactory()
        response = ResponseFactory(question=question, respondent=respondent)
        response.read_by.add(user)

        cloned = clone_consultation(original)

        cloned_question = Question.objects.get(consultation=cloned)
        cloned_response = Response.objects.get(question=cloned_question)

        assert cloned_response.read_by.count() == 0

    def test_response_flagged_by_is_not_cloned(self):
        original = ConsultationFactory()
        question = QuestionFactory(consultation=original)
        respondent = RespondentFactory(consultation=original)
        user = UserFactory()
        response = ResponseFactory(question=question, respondent=respondent)
        annotation = ResponseAnnotation.objects.create(response=response)
        annotation.flagged_by.add(user)

        cloned = clone_consultation(original)

        cloned_question = Question.objects.get(consultation=cloned)
        cloned_response = Response.objects.get(question=cloned_question)
        cloned_annotation = ResponseAnnotation.objects.get(response=cloned_response)

        assert cloned_annotation.flagged_by.count() == 0
