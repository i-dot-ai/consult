import json
import random
from typing import Optional

from django.conf import settings
from django_rq import job

from consultations.models import (
    CandidateTheme,
    CandidateThemeResponse,
    Consultation,
    MultiChoiceAnswer,
    Question,
    Response,
    ResponseAnnotation,
    SelectedTheme,
)
from factories import (
    CandidateThemeFactory,
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
    SelectedThemeFactory,
)
from hosting_environment import HostingEnvironment

logger = settings.LOGGER

DUMMY_CONSULTATIONS = [
    {
        "CONSULTATION_NAME": "Dummy Consultation - Data Setup",
        "CONSULTATION_CODE": "dummy-setup",
        "CONSULTATION_STAGE": Consultation.Stage.SETUP,
        "QUESTION_THEME_STATUS": Question.ThemeStatus.DRAFT,
    },
    {
        "CONSULTATION_NAME": "Dummy Consultation - Starting finalising themes",
        "CONSULTATION_CODE": "dummy-start-finalising-themes",
        "CONSULTATION_STAGE": Consultation.Stage.THEME_SIGN_OFF,
        "QUESTION_THEME_STATUS": Question.ThemeStatus.DRAFT,
    },
    {
        "CONSULTATION_NAME": "Dummy Consultation - Finished finalising themes",
        "CONSULTATION_CODE": "dummy-finished-finalising-themes",
        "CONSULTATION_STAGE": Consultation.Stage.THEME_SIGN_OFF,
        "QUESTION_THEME_STATUS": Question.ThemeStatus.CONFIRMED,
    },
    {
        "CONSULTATION_NAME": "Dummy Consultation - Analysis",
        "CONSULTATION_CODE": "dummy-analysis",
        "CONSULTATION_STAGE": Consultation.Stage.ANALYSIS,
        "QUESTION_THEME_STATUS": Question.ThemeStatus.CONFIRMED,
    },
]

NUMBER_RESPONDENTS = 100
REGIONS = ["North East", "North West", "South East", "South West", "Midlands", "London"]
AGE_GROUPS = ["Under 18", "18-35", "36-50", "51-65", "66+"]
RESPONDENT_TYPES = ["Individual", "Organisation"]
SAMPLE_QUESTIONS_PATH = "./tests/examples/sample_questions.json"


def create_consultation(config):
    """Create and return a Consultation from a config dict."""
    return ConsultationFactory(
        title=config["CONSULTATION_NAME"],
        code=config["CONSULTATION_CODE"],
        stage=config["CONSULTATION_STAGE"],
    )


def _demographics_for(themefinder_id):
    """Return deterministic demographics based on themefinder_id."""
    return {
        "region": REGIONS[themefinder_id % len(REGIONS)],
        "age_group": AGE_GROUPS[themefinder_id % len(AGE_GROUPS)],
        "respondent_type": RESPONDENT_TYPES[themefinder_id % len(RESPONDENT_TYPES)],
    }


def create_respondents(consultation, number_respondents):
    """Create and return a list of Respondents."""
    return [
        RespondentFactory(
            consultation=consultation,
            themefinder_id=i,
            demographics=_demographics_for(i),
        )
        for i in range(1, number_respondents + 1)
    ]


def create_question(consultation, question_data, theme_status):
    """Create and return a Question."""
    has_free_text = question_data["has_free_text"]
    has_multiple_choice = question_data["has_multiple_choice"]

    return QuestionFactory(
        text=question_data["question_text"],
        number=question_data["number"],
        consultation=consultation,
        has_free_text=has_free_text,
        has_multiple_choice=has_multiple_choice,
        theme_status=theme_status,
    )


def create_multi_choice_answers(question, choices):
    """Create MultiChoiceAnswers for a multiple choice question."""
    multi_choice_objects = [MultiChoiceAnswer(question=question, text=choice) for choice in choices]
    MultiChoiceAnswer.objects.bulk_create(multi_choice_objects)


def create_candidate_themes(question, candidate_themes_data):
    """Create CandidateThemes (and SelectedThemes if selected) from flat theme list."""
    key_to_candidate_theme = {}

    for theme_data in candidate_themes_data:
        candidate_theme = CandidateThemeFactory(
            question=question,
            name=theme_data["name"],
            description=theme_data.get("description", ""),
            parent=None,
            approximate_frequency=theme_data.get("approximate_frequency", 0),
        )
        key_to_candidate_theme[theme_data["key"]] = candidate_theme

        if question.theme_status == Question.ThemeStatus.CONFIRMED and theme_data.get("selected"):
            selected_theme = SelectedThemeFactory(
                question=question,
                name=theme_data["name"],
                description=theme_data.get("description", ""),
                key=theme_data["key"],
            )
            candidate_theme.selectedtheme = selected_theme
            candidate_theme.save()

    for theme_data in candidate_themes_data:
        parent_key = theme_data.get("parent_key")
        if parent_key and parent_key in key_to_candidate_theme:
            candidate_theme = key_to_candidate_theme[theme_data["key"]]
            candidate_theme.parent = key_to_candidate_theme[parent_key]
            candidate_theme.save()


def create_default_selected_themes(question):
    """Create the 'Other' and 'No Reason Given' themes added at start of assign-themes."""
    SelectedTheme.objects.get_or_create(
        question=question,
        name="Other",
        defaults={
            "description": "The response discusses an issue not covered by the listed themes"
        },
    )
    SelectedTheme.objects.get_or_create(
        question=question,
        name="No Reason Given",
        defaults={
            "description": "The response does not provide a substantive answer to the question"
        },
    )


def create_response(respondent, question, free_text_answers):
    """Create and return a Response."""
    free_text = random.choice(free_text_answers) if question.has_free_text else None
    return ResponseFactory(question=question, free_text=free_text, respondent=respondent)


def create_response_annotation(response, question):
    """Create a ResponseAnnotation and ResponseAnnotationThemes for a free text response."""
    selected_themes = list(question.selectedtheme_set.all())
    themes_for_response = random.sample(
        selected_themes,
        k=random.randint(1, len(selected_themes)),
    )
    random_sentiment = random.choice([s[0] for s in ResponseAnnotation.Sentiment.choices])
    random_evidence_rich = random.choice([True, False])
    response_annotation = ResponseAnnotationFactoryNoThemes(
        response=response,
        sentiment=random_sentiment,
        evidence_rich=random_evidence_rich,
    )
    response_annotation.add_original_ai_themes(themes_for_response)


def create_response_chosen_options(response, multiple_choice_options):
    """Add chosen options to a multiple choice response."""
    chosen_options = random.sample(
        multiple_choice_options,
        k=random.randint(1, len(multiple_choice_options)),
    )
    answers = MultiChoiceAnswer.objects.filter(question=response.question, text__in=chosen_options)
    response.chosen_options.add(*answers)


def candidate_theme_keys_for_respondent(themefinder_id, theme_keys):
    """Deterministically assign 1-2 theme keys to a respondent based on their ID."""
    idx = themefinder_id % len(theme_keys)
    if themefinder_id % 3 == 0 and len(theme_keys) > 1:
        idx2 = (themefinder_id + 1) % len(theme_keys)
        return [theme_keys[idx], theme_keys[idx2]]
    return [theme_keys[idx]]


def create_candidate_theme_responses(question):
    """Assign responses to candidate themes at all levels for a question deterministically."""
    all_themes = list(CandidateTheme.objects.filter(question=question))
    responses = list(
        Response.objects.filter(question=question, free_text__isnull=False)
        .exclude(free_text="")
        .select_related("respondent")
    )
    if not all_themes or not responses:
        return

    themes_by_parent = {}
    for theme in all_themes:
        themes_by_parent.setdefault(theme.parent_id, []).append(theme)

    records = []
    for sibling_themes in themes_by_parent.values():
        for response in responses:
            assigned = candidate_theme_keys_for_respondent(
                response.respondent.themefinder_id,
                sibling_themes,
            )
            for theme in assigned:
                records.append(CandidateThemeResponse(candidate_theme=theme, response=response))

    CandidateThemeResponse.objects.bulk_create(records, ignore_conflicts=True)


def create_dummy_consultation(
    file_path: str = SAMPLE_QUESTIONS_PATH,
    number_respondents: int = 10,
    consultation: Optional[Consultation] = None,
    config: Optional[dict] = None,
) -> Consultation:
    """
    Create consultation with questions, responses and themes from JSON file.
    Creates relevant objects depending on stage and theme status:
    - SETUP: Consultation, Questions, Respondents, Responses (ready for finding themes)
    - THEME_SIGN_OFF (DRAFT): + CandidateThemes + CandidateThemeResponses (finalising)
    - THEME_SIGN_OFF (CONFIRMED): + CandidateThemes + SelectedThemes (ready for assignment)
    - ANALYSIS: + SelectedThemes + ResponseAnnotations
    """
    if HostingEnvironment.is_production():
        raise RuntimeError("Dummy data generation should not be run in production")

    if config is None:
        config = DUMMY_CONSULTATIONS[-1]

    consultation_stage = config["CONSULTATION_STAGE"]
    theme_status = config["QUESTION_THEME_STATUS"]

    if consultation is None:
        logger.info("Creating consultation at stage: {stage}", stage=consultation_stage)
        consultation = create_consultation(config)

    logger.info("Creating {number_respondents} respondents", number_respondents=number_respondents)
    respondents = create_respondents(consultation, number_respondents)

    with open(file_path, "r") as file:
        questions_data = json.load(file)

    has_candidate_themes = consultation_stage in [
        Consultation.Stage.THEME_SIGN_OFF,
        Consultation.Stage.ANALYSIS,
    ]
    has_candidate_theme_responses = consultation_stage in [
        Consultation.Stage.THEME_SIGN_OFF,
        Consultation.Stage.ANALYSIS,
    ]
    has_default_selected_themes = consultation_stage == Consultation.Stage.ANALYSIS
    has_response_annotations = consultation_stage == Consultation.Stage.ANALYSIS

    for question_data in questions_data:
        logger.info("Creating a new question...")
        question = create_question(consultation, question_data, theme_status)
        multiple_choice_options = question_data.get("multiple_choice_options", [])
        free_text_answers = question_data.get("free_text_answers", [])

        if question.has_multiple_choice:
            create_multi_choice_answers(question, multiple_choice_options)

        if question.has_free_text and has_candidate_themes:
            create_candidate_themes(question, question_data["candidate_themes"])

        if question.has_free_text and has_default_selected_themes:
            create_default_selected_themes(question)

        for respondent in respondents:
            response = create_response(respondent, question, free_text_answers)

            if question.has_free_text and has_response_annotations:
                create_response_annotation(response, question)

            if question.has_multiple_choice:
                create_response_chosen_options(response, multiple_choice_options)

        if question.has_free_text and has_candidate_theme_responses:
            create_candidate_theme_responses(question)

        logger.info(
            "Finished adding question and responses for question {question_number}",
            question_number=question.number,
        )

    logger.info(
        "Finished adding dummy data for consultation {consultation_code}",
        consultation_code=consultation.code,
    )
    return consultation


# Will only be run occasionally to create dummy data - not in prod
@job("default", timeout=2400)
def create_dummy_consultation_job(
    file_path: str = SAMPLE_QUESTIONS_PATH,
    number_respondents: int = 10,
    consultation: Optional[Consultation] = None,
    config: Optional[dict] = None,
):
    create_dummy_consultation(
        file_path=file_path,
        number_respondents=number_respondents,
        consultation=consultation,
        config=config,
    )
