import json

from django.conf import settings

from authentication.models import User
from consultations.models import (
    CandidateTheme,
    CandidateThemeResponse,
    Consultation,
    Question,
    Response,
    ResponseAnnotation,
    SelectedTheme,
)
from factories import (
    CandidateThemeFactory,
    ClosedQuestionFactory,
    ConsultationFactory,
    DemographicQuestionFactory,
    OpenQuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
    SelectedThemeFactory,
)
from hosting_environment import HostingEnvironment
from rq_context import job

logger = settings.LOGGER

DUMMY_CONSULTATIONS = [
    {
        "CONSULTATION_NAME": "Dummy Consultation - Data Setup",
        "CONSULTATION_CODE": "dummy-setup",
        "CONSULTATION_STAGE": Consultation.Stage.SETUP,
        "QUESTION_STATUS": Question.ThemeStatus.DRAFT,
        "QUESTION_THEME_STATUS": Question.ThemeStatus.DRAFT,
    },
    {
        "CONSULTATION_NAME": "Dummy Consultation - Starting finalising themes",
        "CONSULTATION_CODE": "dummy-start-finalising-themes",
        "CONSULTATION_STAGE": Consultation.Stage.FINALISING_THEMES,
        "QUESTION_STATUS": Question.ThemeStatus.FINALISING_THEMES,
        "QUESTION_THEME_STATUS": Question.ThemeStatus.DRAFT,
    },
    {
        "CONSULTATION_NAME": "Dummy Consultation - Finished finalising themes",
        "CONSULTATION_CODE": "dummy-finished-finalising-themes",
        "CONSULTATION_STAGE": Consultation.Stage.ASSIGNING_THEMES,
        "QUESTION_STATUS": Question.ThemeStatus.CONFIRMED,
        "QUESTION_THEME_STATUS": Question.ThemeStatus.CONFIRMED,
    },
    {
        "CONSULTATION_NAME": "Dummy Consultation - Analysis",
        "CONSULTATION_CODE": "dummy-analysis",
        "CONSULTATION_STAGE": Consultation.Stage.ANALYSIS,
        "QUESTION_STATUS": Question.ThemeStatus.CONFIRMED,
        "QUESTION_THEME_STATUS": Question.ThemeStatus.CONFIRMED,
    },
]

NUMBER_RESPONDENTS = 100
SAMPLE_QUESTIONS_PATH = "./tests/examples/sample_questions.json"


def create_consultation(config):
    """Create and return a Consultation from a config dict."""
    return ConsultationFactory(
        title=config["CONSULTATION_NAME"],
        code=config["CONSULTATION_CODE"],
        stage=config["CONSULTATION_STAGE"],
        data_source=Consultation.DataSource.CITIZEN_SPACE,
    )


def create_respondents(consultation, number_respondents):
    """Create and return a list of Respondents."""
    return [
        RespondentFactory(
            consultation=consultation,
            themefinder_id=i,
        )
        for i in range(1, number_respondents + 1)
    ]


def create_question(consultation, question_data, status, theme_status, questions_by_key):
    """Create and return a Question."""
    question_type = question_data["type"]
    factory = {
        Question.QuestionType.OPEN: OpenQuestionFactory,
        Question.QuestionType.CLOSED: ClosedQuestionFactory,
        Question.QuestionType.DEMOGRAPHIC: DemographicQuestionFactory,
    }[question_type]
    closed_question_key = question_data.get("closed_question")

    return factory(
        text=question_data["question_text"],
        short_name=question_data["short_name"],
        number=question_data["number"],
        consultation=consultation,
        closed_question=questions_by_key.get(closed_question_key),
        status=status,
        theme_status=theme_status,
    )


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


def create_responses(respondent, question, question_data):
    """Create V2 responses, including one row per selected closed-question option."""
    answers = question_data["answers"]
    answer_count = 1 + (respondent.themefinder_id % 2) if question_data.get("multi_select") else 1
    values = [
        answers[(respondent.themefinder_id + offset) % len(answers)]
        for offset in range(answer_count)
    ]
    return [
        ResponseFactory(
            question=question,
            respondent=respondent,
            text=value,
            free_text=value if question.type == Question.QuestionType.OPEN else None,
        )
        for value in values
    ]


def create_response_annotation(response, question):
    """Create a ResponseAnnotation and ResponseAnnotationThemes for a free text response."""
    selected_themes = list(question.selectedtheme_set.all())
    tf_id = response.respondent.themefinder_id

    # Assign 1 or 2 themes deterministically based on themefinder_id
    num_themes = 1 + (tf_id % 2)
    themes_for_response = [selected_themes[tf_id % len(selected_themes)]]
    if num_themes > 1 and len(selected_themes) > 1:
        themes_for_response.append(selected_themes[(tf_id + 1) % len(selected_themes)])

    sentiment_choices = [s[0] for s in ResponseAnnotation.Sentiment.choices]
    sentiment = sentiment_choices[tf_id % len(sentiment_choices)]
    evidence_rich = tf_id % 3 == 0

    response_annotation = ResponseAnnotationFactoryNoThemes(
        response=response,
        sentiment=sentiment,
        evidence_rich=evidence_rich,
    )
    response_annotation.add_original_ai_themes(themes_for_response)


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
    consultation: Consultation | None = None,
    config: dict | None = None,
) -> Consultation:
    """
    Create consultation with questions, responses and themes from JSON file.
    Creates relevant objects depending on stage and theme status:
    - SETUP: Consultation only (start of the import flow)
    - FINALISING_THEMES (DRAFT): + CandidateThemes + CandidateThemeResponses (finalising)
    - ASSIGNING_THEMES (CONFIRMED): + CandidateThemes + SelectedThemes (ready for assignment)
    - ANALYSIS: + CandidateThemes + SelectedThemes + ResponseAnnotations
    """
    if HostingEnvironment.is_production() or HostingEnvironment.is_preprod_environment():
        raise RuntimeError("Dummy data generation should not be run in production")

    if config is None:
        config = DUMMY_CONSULTATIONS[-1]

    consultation_stage = config["CONSULTATION_STAGE"]
    question_status = config["QUESTION_STATUS"]
    theme_status = config["QUESTION_THEME_STATUS"]

    if consultation is None:
        logger.info("Creating consultation at stage: {stage}", stage=consultation_stage)
        consultation = create_consultation(config)
        consultation.users.set(User.objects.filter(is_staff=True))

    if consultation_stage == Consultation.Stage.SETUP:
        return consultation

    logger.info("Creating {number_respondents} respondents", number_respondents=number_respondents)
    respondents = create_respondents(consultation, number_respondents)

    with open(file_path, "r") as file:
        questions_data = json.load(file)

    has_candidate_themes = consultation_stage in [
        Consultation.Stage.FINALISING_THEMES,
        Consultation.Stage.ASSIGNING_THEMES,
        Consultation.Stage.ANALYSIS,
    ]
    has_candidate_theme_responses = consultation_stage in [
        Consultation.Stage.FINALISING_THEMES,
        Consultation.Stage.ASSIGNING_THEMES,
        Consultation.Stage.ANALYSIS,
    ]
    has_default_selected_themes = consultation_stage == Consultation.Stage.ANALYSIS
    has_response_annotations = consultation_stage == Consultation.Stage.ANALYSIS

    questions_by_key: dict[str, Question] = {}
    for question_data in questions_data:
        logger.info("Creating a new question...")
        question = create_question(
            consultation, question_data, question_status, theme_status, questions_by_key
        )
        questions_by_key[question_data["fixture_key"]] = question

        if question.type == Question.QuestionType.OPEN and has_candidate_themes:
            create_candidate_themes(question, question_data["candidate_themes"])

        if question.type == Question.QuestionType.OPEN and has_default_selected_themes:
            create_default_selected_themes(question)

        for respondent in respondents:
            responses = create_responses(respondent, question, question_data)

            if question.type == Question.QuestionType.OPEN and has_response_annotations:
                create_response_annotation(responses[0], question)

        if question.type == Question.QuestionType.OPEN and has_candidate_theme_responses:
            create_candidate_theme_responses(question)

        logger.info(
            "Finished adding question and responses for question {question_number}",
            question_number=question.number,
        )

    consultation.survey_import_status = Consultation.SurveyImportStatus.IMPORT_COMPLETE
    consultation.save(update_fields=["survey_import_status"])

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
    consultation: Consultation | None = None,
    config: dict | None = None,
):
    create_dummy_consultation(
        file_path=file_path,
        number_respondents=number_respondents,
        consultation=consultation,
        config=config,
    )
