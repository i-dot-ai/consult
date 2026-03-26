#!/usr/bin/env python3
"""
Load testing script for the Consult application.

This script generates load tests by creating consultations with questions and responses
directly in the database using Django ORM.

Database Connection:
    The script uses Django's database configuration from settings/base.py, which reads
    the DATABASE_URL from environment variables or the .env file in the parent directory.

    Example DATABASE_URL format:
        DATABASE_URL=psql://username:password@host:port/database_name  # pragma: allowlist secret
        DATABASE_URL=psql://postgres:postgres@localhost:5432/consult_e2e_test  # pragma: allowlist secret

    The script will fail if the database is not accessible.
"""

import argparse
import os
import random
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# Setup Django environment
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.local")

import django

django.setup()

# Now we can import Django models
from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.auth.models import AbstractBaseUser  # noqa: E402

from consultations.models import (  # noqa: E402
    CandidateTheme,
    Consultation,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)

UserModel = get_user_model()
# Type alias for mypy
User = AbstractBaseUser


class Stage(str, Enum):
    """Stage options for consultation analysis."""

    NO_THEMES = "no themes"
    CANDIDATE_THEMES = "candidate themes"
    THEMES_APPROVED = "themes approved"
    ANALYSIS = "analysis"


# Sample data for generating test content
SAMPLE_QUESTIONS = [
    "What improvements would you suggest for public transportation in your area?",
    "How satisfied are you with the current state of local healthcare services?",
    "What measures should be taken to improve environmental sustainability in our community?",
    "Do you support the proposed changes to the local planning regulations?",
    "What additional facilities or services would benefit young people in the area?",
    "How effective do you think current road safety measures are?",
    "What are your views on the proposed development of green spaces?",
    "Should more funding be allocated to adult education programs?",
    "What improvements would you like to see in local sports and recreation facilities?",
    "How can we better support small businesses in the community?",
]

SAMPLE_RESPONSES = [
    "I believe this would greatly benefit our community and improve quality of life for residents.",
    "While I appreciate the intention, I have concerns about the implementation and long-term sustainability.",
    "This is an excellent initiative that addresses a real need in our area.",
    "I strongly support this proposal and think it should be prioritized.",
    "More consultation is needed before proceeding with these changes.",
    "The current approach is insufficient and needs significant improvement.",
    "I have mixed feelings about this - there are both advantages and drawbacks to consider.",
    "This would be a positive step forward but should be accompanied by additional measures.",
    "I oppose this proposal as it does not adequately address the underlying issues.",
    "This is a thoughtful approach that balances different community needs effectively.",
]

SAMPLE_MC_OPTIONS = [
    "Strongly Agree",
    "Agree",
    "Neutral",
    "Disagree",
    "Strongly Disagree",
    "Not Provided",
    "Unsure or no opinion",
]

SAMPLE_DEMOGRAPHICS = {
    "Individual or business": ["Individual", "Business", "Organisation", "Charity"],
    "Region": ["North", "South", "East", "West", "Central"],
    "Happy to be published": ["Yes, but without PII", "Yes, with full details", "No"],
}

# Performance optimization constants
RESPONDENT_BATCH_SIZE = 1000  # Batch size for bulk creating respondents
RESPONSE_BATCH_SIZE = 5000  # Batch size for bulk creating responses
M2M_BATCH_SIZE = 10000  # Batch size for bulk creating M2M relationships
RECONNECT_INTERVAL = 3600  # Reconnect to database every hour (seconds)


def load_sample_theme_data(yaml_path: Path) -> dict[str, Any]:
    """Load sample themes, sentiments, and annotation data from YAML file.

    Args:
        yaml_path: Path to the YAML file containing theme data

    Returns:
        Dictionary containing theme configuration
    """
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def periodic_reconnect() -> None:
    """Reconnect to database to avoid long-running connection timeouts."""
    from django.db import connection

    try:
        connection.close()
        connection.ensure_connection()
        print("  ♻️  Reconnected to database")
    except Exception as e:
        print(f"  ⚠️  Warning: Failed to reconnect to database: {e}")


def generate_theme_key(index: int) -> str:
    """Generate theme key: A, B, C, ..., Z, AA, AB, ...

    Args:
        index: Zero-based index

    Returns:
        Theme key string
    """
    result = ""
    index += 1  # Make it 1-based

    while index > 0:
        index -= 1
        result = chr(65 + (index % 26)) + result
        index //= 26

    return result


def create_candidate_themes_for_question(
    question: Question,
    theme_data: dict[str, Any],
) -> list[CandidateTheme]:
    """Create 3-7 candidate themes per question with free text.

    30% will have 1-2 child themes (hierarchical).

    Args:
        question: Question instance
        theme_data: Loaded theme data from YAML

    Returns:
        List of created CandidateTheme instances
    """
    if not question.has_free_text:
        return []

    config = theme_data["candidate_theme_counts"]
    num_themes = random.randint(config["min_per_question"], config["max_per_question"])

    available_themes = theme_data["candidate_themes"]
    selected_themes = random.sample(available_themes, min(num_themes, len(available_themes)))

    themes_to_create = []
    remaining_frequency = 100

    # Create parent themes
    for i, theme_config in enumerate(selected_themes):
        if i == len(selected_themes) - 1:
            frequency = remaining_frequency
        else:
            max_freq = min(40, remaining_frequency - (len(selected_themes) - i - 1) * 5)
            frequency = random.randint(5, max_freq)
            remaining_frequency -= frequency

        themes_to_create.append(
            {
                "question": question,
                "name": theme_config["name"],
                "description": theme_config["description"],
                "approximate_frequency": frequency,
                "parent": None,
                "parent_name": theme_config["name"],  # For child lookup
            }
        )

    # Bulk create parent themes
    parent_objects = [
        CandidateTheme(
            question=t["question"],
            name=t["name"],
            description=t["description"],
            approximate_frequency=t["approximate_frequency"],
            parent=None,
        )
        for t in themes_to_create
    ]
    parent_themes = CandidateTheme.objects.bulk_create(parent_objects)

    # Create child themes (30% chance)
    child_themes_to_create = []
    for parent_theme, theme_info in zip(parent_themes, themes_to_create):
        if random.random() < 0.3:  # 30% chance
            parent_name = theme_info["parent_name"]
            child_configs = theme_data.get("child_themes", {}).get(parent_name, [])

            if child_configs:
                num_children = random.randint(1, min(2, len(child_configs)))
                selected_children = random.sample(child_configs, num_children)

                for child_config in selected_children:
                    child_frequency = theme_info["approximate_frequency"] // len(selected_children)
                    child_themes_to_create.append(
                        CandidateTheme(
                            question=question,
                            name=child_config["name"],
                            description=child_config["description"],
                            approximate_frequency=child_frequency,
                            parent=parent_theme,
                        )
                    )

    # Bulk create child themes
    child_themes = []
    if child_themes_to_create:
        child_themes = CandidateTheme.objects.bulk_create(child_themes_to_create)

    return list(parent_themes) + child_themes


def create_selected_themes_for_question(
    question: Question,
    candidate_themes: list[CandidateTheme],
    user: AbstractBaseUser,
) -> list[SelectedTheme]:
    """Promote ~70% of candidate themes to selected themes.

    Assigns keys (A, B, C, ...).

    Args:
        question: Question instance
        candidate_themes: List of CandidateTheme instances
        user: User who is "selecting" the themes

    Returns:
        List of created SelectedTheme instances
    """
    if not candidate_themes:
        return []

    # Select ~70% to promote (prefer parents)
    num_to_select = max(1, int(len(candidate_themes) * 0.7))
    parent_themes = [t for t in candidate_themes if t.parent is None]
    child_themes = [t for t in candidate_themes if t.parent is not None]

    themes_to_promote = parent_themes[:num_to_select]
    if len(themes_to_promote) < num_to_select:
        remaining = num_to_select - len(themes_to_promote)
        themes_to_promote.extend(child_themes[:remaining])

    # Prepare selected themes for bulk creation
    selected_to_create = []
    for key_index, candidate in enumerate(themes_to_promote):
        key = generate_theme_key(key_index)

        selected_to_create.append(
            SelectedTheme(
                question=question,
                name=candidate.name,
                description=candidate.description,
                key=key,
                crosscuttingtheme=None,
                version=1,
                last_modified_by=user,
            )
        )

    # Bulk create
    selected_themes = SelectedTheme.objects.bulk_create(selected_to_create)

    # Link back to candidates (requires update, can't bulk_update the reverse relation efficiently)
    for candidate, selected in zip(themes_to_promote, selected_themes):
        candidate.selectedtheme = selected
        candidate.save(update_fields=["selectedtheme"])

    return selected_themes


def create_response_annotations(
    responses: list[Response],
    selected_themes: list[SelectedTheme],
    theme_data: dict[str, Any],
) -> tuple[int, int]:
    """Create annotations with themes, sentiment, evidence flags.

    Uses bulk_create for performance optimization.

    Args:
        responses: List of Response instances
        selected_themes: List of SelectedTheme instances for this question
        theme_data: Loaded theme data from YAML

    Returns:
        Tuple of (num_annotations, num_theme_assignments)
    """
    if not selected_themes:
        return (0, 0)

    sentiment_dist = theme_data["sentiment_distribution"]
    evidence_rich_pct = theme_data["evidence_rich_percentage"]
    theme_assign_config = theme_data["theme_assignment"]

    # Build weighted sentiment choices
    sentiment_choices = []
    for sentiment, weight in sentiment_dist.items():
        sentiment_choices.extend([sentiment] * weight)

    # Prepare annotations for bulk creation
    annotations_to_create = []
    for response in responses:
        if not response.free_text or response.free_text.strip() == "":
            continue

        annotations_to_create.append(
            ResponseAnnotation(
                response=response,
                sentiment=random.choice(sentiment_choices),
                evidence_rich=random.random() < (evidence_rich_pct / 100),
                human_reviewed=False,
            )
        )

    # Bulk create annotations
    annotations = ResponseAnnotation.objects.bulk_create(annotations_to_create)

    # Prepare theme assignments for bulk creation
    theme_assignments_to_create = []
    for annotation in annotations:
        num_themes = random.randint(
            theme_assign_config["min_themes_per_response"],
            min(theme_assign_config["max_themes_per_response"], len(selected_themes)),
        )

        assigned_themes = random.sample(selected_themes, num_themes)

        for theme in assigned_themes:
            theme_assignments_to_create.append(
                ResponseAnnotationTheme(
                    response_annotation=annotation,
                    theme=theme,
                    assigned_by=None,  # AI-assigned
                )
            )

    # Bulk create theme assignments
    theme_assignments = ResponseAnnotationTheme.objects.bulk_create(theme_assignments_to_create)

    return (len(annotations), len(theme_assignments))


def create_consultation(
    name: str,
    stage: Stage,
    user_email: str,
) -> Consultation:
    """
    Create a consultation in the database.

    Args:
        name: Name of the consultation
        stage: Stage of the consultation
        user_email: Email of the user creating the consultation

    Returns:
        Created Consultation instance

    Raises:
        SystemExit: If the user does not exist in the database
    """
    stage_mapping = {
        Stage.NO_THEMES: Consultation.Stage.THEME_SIGN_OFF,
        Stage.CANDIDATE_THEMES: Consultation.Stage.THEME_SIGN_OFF,
        Stage.THEMES_APPROVED: Consultation.Stage.THEME_MAPPING,  # After "Confirm and Proceed" clicked
        Stage.ANALYSIS: Consultation.Stage.ANALYSIS,  # After response annotations imported
    }

    # Get user - must already exist
    try:
        user = UserModel.objects.get(email=user_email)
        print(f"✓ Using existing user: {user_email}")
    except UserModel.DoesNotExist:
        print(f"✗ ERROR: User '{user_email}' does not exist in the database")
        print("\nPlease create the user first:")
        print("  1. Via Django admin: http://localhost:8000/admin/")
        print("  2. Via Django shell: python manage.py createsuperuser")
        print("  3. Or use an existing user email with --user-email")
        sys.exit(1)

    # Create consultation
    consultation = Consultation.objects.create(
        title=name,
        code=name.lower().replace(" ", "-"),
        stage=stage_mapping.get(stage, Consultation.Stage.THEME_SIGN_OFF),
        display_ai_selected_themes=True,
        model_name=Consultation.ModelName.GPT_41,
    )
    consultation.users.add(user)

    print(f"✓ Created consultation: {consultation.title}")
    print(f"  ID: {consultation.id}")
    print(f"  Code: {consultation.code}")
    print(f"  Stage: {consultation.stage}")

    return consultation


def create_demographics(consultation: Consultation) -> dict[str, list[DemographicOption]]:
    """
    Create demographic options for the consultation.

    Args:
        consultation: Consultation instance

    Returns:
        Dictionary mapping field names to lists of DemographicOption instances
    """
    demographics: dict[str, list[DemographicOption]] = {}

    for field_name, options in SAMPLE_DEMOGRAPHICS.items():
        demographics[field_name] = []
        for option_value in options:
            demo_option, created = DemographicOption.objects.get_or_create(
                consultation=consultation,
                field_name=field_name,
                field_value=option_value,
            )
            demographics[field_name].append(demo_option)

    print(f"✓ Created {len(demographics)} demographic categories")
    return demographics


def create_respondents(
    consultation: Consultation,
    num_respondents: int,
    demographics: dict[str, list[DemographicOption]],
) -> list[Respondent]:
    """
    Create respondents for the consultation using bulk operations.

    Args:
        consultation: Consultation instance
        num_respondents: Number of respondents to create
        demographics: Dictionary of demographic options

    Returns:
        List of created Respondent instances
    """
    print(f"Creating {num_respondents:,} respondents in batches of {RESPONDENT_BATCH_SIZE:,}...")

    all_respondents = []
    start_time = time.time()

    for batch_start in range(0, num_respondents, RESPONDENT_BATCH_SIZE):
        batch_end = min(batch_start + RESPONDENT_BATCH_SIZE, num_respondents)

        # Prepare respondents for bulk creation
        respondents_to_create = [
            Respondent(
                consultation=consultation,
                themefinder_id=i,
            )
            for i in range(batch_start + 1, batch_end + 1)
        ]

        # Bulk create respondents
        created_respondents = Respondent.objects.bulk_create(respondents_to_create)
        all_respondents.extend(created_respondents)

        # Prepare M2M relationships for demographics
        demographics_m2m = []
        for respondent in created_respondents:
            for field_name, options in demographics.items():
                if options:
                    demographics_m2m.append(
                        Respondent.demographics.through(
                            respondent_id=respondent.id,
                            demographicoption_id=random.choice(options).id,
                        )
                    )

        # Bulk create M2M relationships
        Respondent.demographics.through.objects.bulk_create(demographics_m2m)

        # Progress tracking
        elapsed = time.time() - start_time
        rate = batch_end / elapsed if elapsed > 0 else 0
        remaining = num_respondents - batch_end
        eta_seconds = remaining / rate if rate > 0 else 0

        print(
            f"  Created {batch_end:,}/{num_respondents:,} respondents "
            f"({batch_end / num_respondents * 100:.1f}%) "
            f"Rate: {rate:.0f}/sec ETA: {eta_seconds / 60:.1f} min"
        )

    total_time = time.time() - start_time
    print(f"✓ Created {len(all_respondents):,} respondents in {total_time:.1f} seconds")
    return all_respondents


def create_question(
    consultation: Consultation,
    question_number: int,
    question_type: str,
) -> Question:
    """
    Create a question for the consultation.

    Args:
        consultation: Consultation instance
        question_number: Question number
        question_type: 'open', 'hybrid', or 'multiple_choice'

    Returns:
        Created Question instance
    """
    question_text = random.choice(SAMPLE_QUESTIONS)

    has_free_text = question_type in ["open", "hybrid"]
    has_multiple_choice = question_type in ["hybrid", "multiple_choice"]

    question = Question.objects.create(
        consultation=consultation,
        text=question_text,
        number=question_number,
        has_free_text=has_free_text,
        has_multiple_choice=has_multiple_choice,
    )

    # Add multiple choice options if needed
    if has_multiple_choice:
        num_options = random.randint(3, 5)
        selected_options = random.sample(
            SAMPLE_MC_OPTIONS, min(num_options, len(SAMPLE_MC_OPTIONS))
        )

        for option_text in selected_options:
            MultiChoiceAnswer.objects.create(
                question=question,
                text=option_text,
            )

    return question


def create_responses_for_question(
    question: Question,
    respondents: list[Respondent],
    coverage_percent: float = 80.0,
) -> int:
    """
    Create responses for a question using bulk operations.

    Args:
        question: Question instance
        respondents: List of Respondent instances
        coverage_percent: Percentage of respondents who answer

    Returns:
        Number of responses created
    """
    # Determine how many respondents will answer
    num_responding = int(len(respondents) * coverage_percent / 100)
    responding = random.sample(respondents, num_responding)

    # Get MC options once if needed
    mc_options = []
    if question.has_multiple_choice:
        mc_options = list(MultiChoiceAnswer.objects.filter(question=question))

    # Prepare all responses and M2M relationships upfront
    responses_to_create = []
    m2m_data = []  # (response_index, option_ids)

    for idx, respondent in enumerate(responding):
        response = Response(
            respondent=respondent,
            question=question,
            free_text=random.choice(SAMPLE_RESPONSES) if question.has_free_text else None,
        )
        responses_to_create.append(response)

        # Prepare M2M data for this response
        if question.has_multiple_choice and mc_options:
            num_selections = random.randint(1, min(3, len(mc_options)))
            selected = random.sample(mc_options, num_selections)
            m2m_data.append((idx, [opt.id for opt in selected]))

    # Bulk create responses in batches
    all_created = []

    for i in range(0, len(responses_to_create), RESPONSE_BATCH_SIZE):
        batch = responses_to_create[i : i + RESPONSE_BATCH_SIZE]
        created_batch = Response.objects.bulk_create(batch)
        all_created.extend(created_batch)

    # Bulk create M2M relationships
    if m2m_data:
        m2m_to_create = []
        for idx, option_ids in m2m_data:
            response = all_created[idx]
            for option_id in option_ids:
                m2m_to_create.append(
                    Response.chosen_options.through(
                        response_id=response.id,
                        multichoiceanswer_id=option_id,
                    )
                )

        # Create M2M in batches
        for i in range(0, len(m2m_to_create), M2M_BATCH_SIZE):
            batch = m2m_to_create[i : i + M2M_BATCH_SIZE]
            Response.chosen_options.through.objects.bulk_create(batch)

    # Update question's total_responses count
    question.update_total_responses()

    return len(all_created)


def resume_load_test(
    consultation_code: str,
    num_of_questions: int,
    num_of_respondents: int,
    stage: Stage,
    user_email: str,
    question_type_distribution: dict[str, int] | None = None,
) -> None:
    """
    Resume an existing load test from where it failed.

    Args:
        consultation_code: Code of the existing consultation
        num_of_questions: Target number of questions
        num_of_respondents: Target number of respondents
        stage: Target stage of the consultation
        user_email: Email of user
        question_type_distribution: Distribution of question types
    """
    print("\n" + "=" * 80)
    print("RESUME EXISTING CONSULTATION")
    print("=" * 80)
    print(f"\nLooking up consultation: {consultation_code}")

    # Look up existing consultation
    try:
        consultation = Consultation.objects.get(code=consultation_code)
        print(f"✓ Found consultation: {consultation.title}")
        print(f"  ID: {consultation.id}")
        print(f"  Current Stage: {consultation.stage}")
    except Consultation.DoesNotExist:
        print(f"✗ ERROR: Consultation with code '{consultation_code}' not found")
        sys.exit(1)

    # Check existing data
    existing_respondents_count = Respondent.objects.filter(consultation=consultation).count()
    existing_questions_count = Question.objects.filter(consultation=consultation).count()
    existing_responses_count = Response.objects.filter(question__consultation=consultation).count()

    print("\nExisting data:")
    print(f"  Respondents: {existing_respondents_count:,}/{num_of_respondents:,}")
    print(f"  Questions: {existing_questions_count}/{num_of_questions}")
    print(f"  Responses: {existing_responses_count:,}")
    print()

    # Get demographics
    demographics = {}
    for field_name in SAMPLE_DEMOGRAPHICS.keys():
        options = list(
            DemographicOption.objects.filter(consultation=consultation, field_name=field_name)
        )
        demographics[field_name] = options

    # Resume respondent creation if needed
    if existing_respondents_count < num_of_respondents:
        print(f"\n⚠️  Resuming respondent creation from {existing_respondents_count:,}...")
        remaining = num_of_respondents - existing_respondents_count

        # Create remaining respondents
        print(f"Creating {remaining:,} additional respondents...")
        m2m_to_create = []

        for batch_start in range(
            existing_respondents_count, num_of_respondents, RESPONDENT_BATCH_SIZE
        ):
            batch_end = min(batch_start + RESPONDENT_BATCH_SIZE, num_of_respondents)

            batch_respondents = [
                Respondent(consultation=consultation, themefinder_id=i)
                for i in range(batch_start + 1, batch_end + 1)
            ]

            created = Respondent.objects.bulk_create(batch_respondents)

            # Add demographics
            for respondent in created:
                for field_name, options in demographics.items():
                    if options:
                        m2m_to_create.append(
                            Respondent.demographics.through(
                                respondent_id=respondent.id,
                                demographicoption_id=random.choice(options).id,
                            )
                        )

            Respondent.demographics.through.objects.bulk_create(m2m_to_create)
            m2m_to_create = []

            print(f"  Created {batch_end:,}/{num_of_respondents:,} respondents")

        print("✓ Completed respondent creation")

    # Get all respondents
    respondents = list(Respondent.objects.filter(consultation=consultation))
    print(f"\n✓ Total respondents available: {len(respondents):,}")

    # Resume question/response creation if needed
    if existing_questions_count < num_of_questions:
        print(f"\n⚠️  Resuming question creation from {existing_questions_count}...")

        # Calculate remaining question types
        if question_type_distribution is None:
            question_type_distribution = {"open": 40, "hybrid": 40, "multiple_choice": 20}

        open_count = int(num_of_questions * question_type_distribution["open"] / 100)
        hybrid_count = int(num_of_questions * question_type_distribution["hybrid"] / 100)
        mc_count = num_of_questions - open_count - hybrid_count

        question_types = (
            ["open"] * open_count + ["hybrid"] * hybrid_count + ["multiple_choice"] * mc_count
        )
        random.shuffle(question_types)

        # Create remaining questions
        last_reconnect = time.time()
        for i in range(existing_questions_count + 1, num_of_questions + 1):
            if time.time() - last_reconnect > RECONNECT_INTERVAL:
                periodic_reconnect()
                last_reconnect = time.time()

            question_type = question_types[i - 1]
            question = create_question(consultation, i, question_type)

            coverage = random.uniform(70, 90)
            num_responses = create_responses_for_question(question, respondents, coverage)

            print(
                f"  Question {i}/{num_of_questions}: {question_type} - {num_responses:,} responses"
            )

        print("✓ Completed question creation")
    else:
        print(f"\n✓ All {num_of_questions} questions already exist")

    # Now check if we need to create themes/annotations based on the target stage
    questions = list(Question.objects.filter(consultation=consultation))
    questions_with_themes = [q for q in questions if q.has_free_text]

    # Get user object for theme creation
    user = UserModel.objects.get(email=user_email)

    # Check if themes need to be created
    candidate_count = CandidateTheme.objects.filter(question__consultation=consultation).count()
    selected_count = SelectedTheme.objects.filter(question__consultation=consultation).count()
    annotation_count = ResponseAnnotation.objects.filter(
        response__question__consultation=consultation
    ).count()

    print("\n📊 Current theme/annotation status:")
    print(f"  Candidate themes: {candidate_count}")
    print(f"  Selected themes: {selected_count}")
    print(f"  Response annotations: {annotation_count:,}")

    # Load theme data if needed
    if stage in [Stage.CANDIDATE_THEMES, Stage.THEMES_APPROVED, Stage.ANALYSIS]:
        theme_data = load_sample_theme_data(Path(__file__).parent / "sample_themes.yaml")

        # Stage 2, 3, 4: Create candidate themes if missing
        if candidate_count == 0 and stage in [
            Stage.CANDIDATE_THEMES,
            Stage.THEMES_APPROVED,
            Stage.ANALYSIS,
        ]:
            print("\n⚠️  Creating candidate themes...")

            all_candidate_themes = {}
            for question in questions_with_themes:
                candidates = create_candidate_themes_for_question(question, theme_data)
                all_candidate_themes[question.id] = candidates

            total_candidates = CandidateTheme.objects.filter(
                question__consultation=consultation
            ).count()
            parent_count = CandidateTheme.objects.filter(
                question__consultation=consultation, parent=None
            ).count()
            child_count = total_candidates - parent_count
            print(
                f"✓ Created {total_candidates} candidate themes ({parent_count} parent, {child_count} child)"
            )
        else:
            # Load existing candidates
            all_candidate_themes = {}
            for question in questions_with_themes:
                candidates = list(CandidateTheme.objects.filter(question=question))
                all_candidate_themes[question.id] = candidates

        # Stage 3 & 4: Create selected themes if missing
        if selected_count == 0 and stage in [Stage.THEMES_APPROVED, Stage.ANALYSIS]:
            print("\n⚠️  Creating selected themes...")

            all_selected_themes = {}
            for question in questions_with_themes:
                candidates = all_candidate_themes.get(question.id, [])
                selected = create_selected_themes_for_question(question, candidates, user)
                all_selected_themes[question.id] = selected

            total_selected = SelectedTheme.objects.filter(
                question__consultation=consultation
            ).count()
            print(f"✓ Created {total_selected} selected themes")

            # Mark all themed questions as signed off
            print("\n⚠️  Marking themed questions as signed off...")
            updated_count = Question.objects.filter(
                id__in=[q.id for q in questions_with_themes]
            ).update(theme_status=Question.ThemeStatus.CONFIRMED)
            print(f"✓ Marked {updated_count} questions as signed off (theme_status=CONFIRMED)")

            # Update consultation stage if needed
            if consultation.stage != Consultation.Stage.THEME_MAPPING:
                consultation.stage = Consultation.Stage.THEME_MAPPING
                consultation.save(update_fields=["stage"])
                print("✓ Updated consultation stage to THEME_MAPPING")
        else:
            # Load existing selected themes
            all_selected_themes = {}
            for question in questions_with_themes:
                selected = list(SelectedTheme.objects.filter(question=question))
                all_selected_themes[question.id] = selected

        # Stage 4: Create response annotations if missing
        if annotation_count == 0 and stage == Stage.ANALYSIS:
            print("\n⚠️  Creating response annotations...")
            print("  (This may take several minutes for large datasets)")

            total_annotations = 0
            total_theme_assignments = 0

            for question in questions_with_themes:
                responses_list = list(Response.objects.filter(question=question))
                selected_themes = all_selected_themes.get(question.id, [])

                if responses_list and selected_themes:
                    num_annotations, num_assignments = create_response_annotations(
                        responses_list, selected_themes, theme_data
                    )
                    total_annotations += num_annotations
                    total_theme_assignments += num_assignments

            print(f"✓ Created {total_annotations:,} response annotations")
            print(f"✓ Created {total_theme_assignments:,} theme assignments")

            # Update consultation stage to ANALYSIS
            if consultation.stage != Consultation.Stage.ANALYSIS:
                consultation.stage = Consultation.Stage.ANALYSIS
                consultation.save(update_fields=["stage"])
                print("✓ Updated consultation stage to ANALYSIS")

    print("\n" + "=" * 80)
    print("RESUME COMPLETE - Consultation is now up to date")
    print("=" * 80)
    print(f"\nConsultation: {consultation.title}")
    print(f"Code: {consultation.code}")
    print(f"Stage: {consultation.stage}")
    print("\nFinal counts:")
    print(f"  Respondents: {Respondent.objects.filter(consultation=consultation).count():,}")
    print(f"  Questions: {Question.objects.filter(consultation=consultation).count()}")
    print(f"  Responses: {Response.objects.filter(question__consultation=consultation).count():,}")
    print(
        f"  Candidate themes: {CandidateTheme.objects.filter(question__consultation=consultation).count()}"
    )
    print(
        f"  Selected themes: {SelectedTheme.objects.filter(question__consultation=consultation).count()}"
    )
    print(
        f"  Response annotations: {ResponseAnnotation.objects.filter(response__question__consultation=consultation).count():,}"
    )
    print(
        f"  Questions signed off: {Question.objects.filter(consultation=consultation, theme_status='confirmed').count()}/{len(questions_with_themes)}"
    )


def run_load_test(
    name_of_consultation: str,
    num_of_questions: int,
    num_of_respondents: int,
    stage: Stage,
    user_email: str,
    question_type_distribution: dict[str, int] | None = None,
    resume_mode: bool = False,
    consultation_code: str | None = None,
) -> None:
    """
    Run the load test with the specified parameters.

    Args:
        name_of_consultation: Name of the consultation
        num_of_questions: Number of questions to generate
        num_of_respondents: Number of respondents to simulate
        stage: Stage of the consultation
        user_email: Email of user creating the consultation
        question_type_distribution: Distribution of question types (percentages)
        resume_mode: Whether to resume an existing consultation
        consultation_code: Code of consultation to resume (required if resume_mode=True)
    """
    # Handle resume mode
    if resume_mode and consultation_code:
        return resume_load_test(
            consultation_code,
            num_of_questions,
            num_of_respondents,
            stage,
            user_email,
            question_type_distribution,
        )

    if question_type_distribution is None:
        question_type_distribution = {
            "open": 40,
            "hybrid": 40,
            "multiple_choice": 20,
        }

    print("\n" + "=" * 80)
    print("CONSULT LOAD TEST")
    print("=" * 80)
    print("\nConfiguration:")
    print(f"  Consultation: {name_of_consultation}")
    print(f"  Questions: {num_of_questions}")
    print(f"  Respondents: {num_of_respondents}")
    print(f"  Stage: {stage.value}")
    print(f"  User: {user_email}")
    print(f"  Question Types: {question_type_distribution}")
    print("\n" + "=" * 80)

    # Step 1: Create consultation
    print("\nStep 1: Creating consultation...")
    consultation = create_consultation(name_of_consultation, stage, user_email)

    # Step 2: Create demographics
    print("\nStep 2: Creating demographic options...")
    demographics = create_demographics(consultation)

    # Step 3: Create respondents
    print("\nStep 3: Creating respondents...")
    respondents = create_respondents(consultation, num_of_respondents, demographics)

    # Step 4: Create questions and responses
    print(f"\nStep 4: Creating {num_of_questions} questions with responses...")
    print(f"  Estimated total responses: {int(num_of_questions * num_of_respondents * 0.8):,}")

    # Calculate question type distribution
    open_count = int(num_of_questions * question_type_distribution["open"] / 100)
    hybrid_count = int(num_of_questions * question_type_distribution["hybrid"] / 100)
    mc_count = num_of_questions - open_count - hybrid_count

    question_types = (
        ["open"] * open_count + ["hybrid"] * hybrid_count + ["multiple_choice"] * mc_count
    )
    random.shuffle(question_types)

    total_responses = 0
    last_reconnect = time.time()
    step4_start = time.time()

    for i, question_type in enumerate(question_types, start=1):
        # Periodic database reconnection to avoid timeouts
        if time.time() - last_reconnect > RECONNECT_INTERVAL:
            periodic_reconnect()
            last_reconnect = time.time()

        question = create_question(consultation, i, question_type)

        # Create responses for this question
        coverage = random.uniform(70, 90)
        num_responses = create_responses_for_question(question, respondents, coverage)
        total_responses += num_responses

        # Enhanced progress tracking
        elapsed = time.time() - step4_start
        rate = total_responses / elapsed if elapsed > 0 else 0
        estimated_total = int(num_of_questions * num_of_respondents * 0.8)
        remaining = estimated_total - total_responses
        eta_seconds = remaining / rate if rate > 0 else 0

        print(
            f"  Question {i}/{num_of_questions}: {question_type} - {num_responses:,} responses "
            f"(Total: {total_responses:,}, Rate: {rate:.0f}/sec, ETA: {eta_seconds / 60:.1f} min)"
        )

    step4_time = time.time() - step4_start
    print(
        f"✓ Created {num_of_questions} questions with {total_responses:,} total responses in {step4_time / 60:.1f} minutes"
    )

    # Get user object for theme creation
    user = UserModel.objects.get(email=user_email)

    # Load theme data for stages 2, 3, and 4
    if stage in [Stage.CANDIDATE_THEMES, Stage.THEMES_APPROVED, Stage.ANALYSIS]:
        theme_data = load_sample_theme_data(Path(__file__).parent / "sample_themes.yaml")
        print("\n✓ Loaded theme configuration from sample_themes.yaml")

    # Stage 2, 3, 4: Create candidate themes
    if stage in [Stage.CANDIDATE_THEMES, Stage.THEMES_APPROVED, Stage.ANALYSIS]:
        print("\nStep 5: Creating candidate themes...")

        all_candidate_themes = {}
        total_candidates = 0
        questions_with_themes = Question.objects.filter(
            consultation=consultation, has_free_text=True
        )

        for question in questions_with_themes:
            candidates = create_candidate_themes_for_question(question, theme_data)
            all_candidate_themes[question.id] = candidates
            total_candidates += len(candidates)

        parent_count = CandidateTheme.objects.filter(
            question__consultation=consultation, parent=None
        ).count()
        child_count = total_candidates - parent_count

        print(
            f"✓ Created {total_candidates} candidate themes ({parent_count} parent, {child_count} child)"
        )

    # Stage 3 & 4: Create selected themes (without or with annotations)
    if stage in [Stage.THEMES_APPROVED, Stage.ANALYSIS]:
        print("\nStep 6: Creating selected themes...")
        all_selected_themes = {}
        total_selected = 0

        for question in questions_with_themes:
            candidates = all_candidate_themes.get(question.id, [])
            selected = create_selected_themes_for_question(question, candidates, user)
            all_selected_themes[question.id] = selected
            total_selected += len(selected)

        print(f"✓ Created {total_selected} selected themes")

        # Mark all themed questions as signed off (theme_status = CONFIRMED)
        print("\nStep 6.5: Marking themed questions as signed off...")

        updated_count = Question.objects.filter(
            id__in=[q.id for q in questions_with_themes]
        ).update(theme_status=Question.ThemeStatus.CONFIRMED)

        print(f"✓ Marked {updated_count} questions as signed off (theme_status=CONFIRMED)")

    # Stage 4 only: Create response annotations (apply themes to responses)
    if stage == Stage.ANALYSIS:
        print("\nStep 7: Creating response annotations...")
        print("  (This may take several minutes for large datasets)")

        total_annotations = 0
        total_theme_assignments = 0

        for question in questions_with_themes:
            responses_list = list(Response.objects.filter(question=question))
            selected_themes = all_selected_themes.get(question.id, [])

            num_annotations, num_assignments = create_response_annotations(
                responses_list, selected_themes, theme_data
            )

            total_annotations += num_annotations
            total_theme_assignments += num_assignments

        print(f"✓ Created {total_annotations} response annotations")
        print(f"✓ Created {total_theme_assignments} theme assignments")

    # Summary
    print("\n" + "=" * 80)
    print("LOAD TEST COMPLETE")
    print("=" * 80)

    # Basic counts
    print("\n📊 CONSULTATION DATA:")
    print(f"  Name: {consultation.title}")
    print(f"  Code: {consultation.code}")
    print(f"  ID: {consultation.id}")
    print(f"  Stage: {consultation.stage}")

    print("\n📝 QUESTIONS & RESPONSES:")
    print(f"  Questions: {num_of_questions} total")
    print(f"    - Open (free text): {open_count}")
    print(f"    - Hybrid (free text + MC): {hybrid_count}")
    print(f"    - Multiple choice: {mc_count}")

    # Show sign-off status for Stage 3 & 4
    if stage in [Stage.THEMES_APPROVED, Stage.ANALYSIS]:
        questions_with_free_text = open_count + hybrid_count
        signed_off_count = Question.objects.filter(
            consultation=consultation,
            has_free_text=True,
            theme_status=Question.ThemeStatus.CONFIRMED,
        ).count()
        print(
            f"    - Signed off: {signed_off_count}/{questions_with_free_text} questions with free text"
        )

    print(f"  Respondents: {num_of_respondents}")
    print(f"  Responses: {total_responses}")

    # Stage 2, 3, 4: Candidate themes additions
    if stage in [Stage.CANDIDATE_THEMES, Stage.THEMES_APPROVED, Stage.ANALYSIS]:
        parent_count = CandidateTheme.objects.filter(
            question__consultation=consultation, parent=None
        ).count()
        child_count = (
            CandidateTheme.objects.filter(question__consultation=consultation)
            .exclude(parent=None)
            .count()
        )
        total_candidates = parent_count + child_count

        print("\n🎯 CANDIDATE THEMES:")
        print(f"  Total: {total_candidates}")
        print(f"    - Parent themes: {parent_count}")
        print(f"    - Child themes: {child_count}")

    # Stage 3 & 4: Selected themes additions
    if stage in [Stage.THEMES_APPROVED, Stage.ANALYSIS]:
        selected_count = SelectedTheme.objects.filter(question__consultation=consultation).count()

        print("\n✅ SELECTED THEMES:")
        print(f"  Total: {selected_count}")

    # Stage 4 only: Response annotations
    if stage == Stage.ANALYSIS:
        annotations_count = ResponseAnnotation.objects.filter(
            response__question__consultation=consultation
        ).count()

        theme_links_count = ResponseAnnotationTheme.objects.filter(
            response_annotation__response__question__consultation=consultation
        ).count()

        print("\n📊 RESPONSE ANALYSIS:")
        print(f"  Annotations: {annotations_count}")
        print(f"  Theme assignments: {theme_links_count}")
        if annotations_count > 0:
            print(f"  Avg themes per response: {theme_links_count / annotations_count:.1f}")

        # Sentiment breakdown
        agreement = ResponseAnnotation.objects.filter(
            response__question__consultation=consultation, sentiment="AGREEMENT"
        ).count()
        disagreement = ResponseAnnotation.objects.filter(
            response__question__consultation=consultation, sentiment="DISAGREEMENT"
        ).count()
        unclear = ResponseAnnotation.objects.filter(
            response__question__consultation=consultation, sentiment="UNCLEAR"
        ).count()

        print("\n💭 SENTIMENT DISTRIBUTION:")
        if annotations_count > 0:
            print(f"  Agreement: {agreement} ({agreement / annotations_count * 100:.0f}%)")
            print(f"  Disagreement: {disagreement} ({disagreement / annotations_count * 100:.0f}%)")
            print(f"  Unclear: {unclear} ({unclear / annotations_count * 100:.0f}%)")

        evidence_rich = ResponseAnnotation.objects.filter(
            response__question__consultation=consultation, evidence_rich=True
        ).count()

        if annotations_count > 0:
            print(
                f"  Evidence-rich: {evidence_rich} ({evidence_rich / annotations_count * 100:.0f}%)"
            )

    print("\n🔗 ACCESS:")
    print(f"  URL: /consultations/{consultation.id}/")
    print("\n" + "=" * 80 + "\n")


def test_database_connection() -> None:
    """
    Test database connection and provide helpful error messages if it fails.

    Raises:
        SystemExit: If database connection fails
    """
    from django.db import connection
    from django.db.utils import OperationalError

    try:
        # Attempt to connect to the database
        connection.ensure_connection()
        print("✓ Database connection successful\n")
    except OperationalError as e:
        print("✗ ERROR: Could not connect to the database\n")
        print(f"Error details: {str(e)}\n")
        print("Troubleshooting steps:")
        print("  1. Check if PostgreSQL is running:")
        print("     - Docker: docker-compose up -d postgres")
        print("     - Native: pg_ctl status")
        print("  2. Verify DATABASE_URL in ../.env file:")
        print(
            "     DATABASE_URL=psql://username:password@host:port/database_name"  # pragma: allowlist secret
        )
        print("  3. Test connection manually:")
        print("     psql -h localhost -U postgres -d consult_e2e_test")
        print("  4. Check if the database exists:")
        print("     createdb consult_e2e_test")
        sys.exit(1)


def main() -> None:
    """Parse arguments and run the load test."""
    parser = argparse.ArgumentParser(
        prog="load_test",
        description="Load testing script for the Consult application - creates data directly in database",
    )

    parser.add_argument(
        "--name-of-consultation",
        type=str,
        required=False,
        help="Name of the consultation (required for new consultations, not needed for --resume)",
    )

    parser.add_argument(
        "--num-of-questions",
        type=int,
        default=20,
        help="Number of questions to generate (default: 20)",
    )

    parser.add_argument(
        "--num-of-respondents",
        type=int,
        default=100,
        help="Number of respondents to simulate (default: 100)",
    )

    parser.add_argument(
        "--stage",
        type=Stage,
        choices=list(Stage),
        required=True,
        help="Stage of the consultation (required)",
    )

    parser.add_argument(
        "--user-email",
        type=str,
        default="load.test@example.com",
        help="Email of user creating the consultation (default: load.test@example.com)",
    )

    parser.add_argument(
        "--question-types",
        type=str,
        default="40,40,20",
        help="Question type distribution as percentages: open,hybrid,multiple_choice (default: 40,40,20)",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume an existing consultation (requires --consultation-code)",
    )

    parser.add_argument(
        "--consultation-code",
        type=str,
        help="Code of existing consultation to resume (use with --resume)",
    )

    args = parser.parse_args()

    # Validate resume arguments
    if args.resume and not args.consultation_code:
        print("Error: --consultation-code is required when using --resume")
        sys.exit(1)

    if not args.resume and args.consultation_code:
        print(
            "Warning: --consultation-code specified but --resume not set. Ignoring consultation code."
        )

    # Validate name is provided when not resuming
    if not args.resume and not args.name_of_consultation:
        print("Error: --name-of-consultation is required when creating a new consultation")
        sys.exit(1)

    # Test database connection first
    print("Checking database connection...")
    test_database_connection()

    # Parse question type distribution
    try:
        open_pct, hybrid_pct, mc_pct = map(int, args.question_types.split(","))
        if open_pct + hybrid_pct + mc_pct != 100:
            print("Error: Question type percentages must sum to 100")
            sys.exit(1)

        question_type_distribution = {
            "open": open_pct,
            "hybrid": hybrid_pct,
            "multiple_choice": mc_pct,
        }
    except ValueError:
        print(
            "Error: Invalid question type distribution format. Use: open,hybrid,multiple_choice (e.g., 40,40,20)"
        )
        sys.exit(1)

    run_load_test(
        name_of_consultation=args.name_of_consultation or "",  # Empty string when resuming
        num_of_questions=args.num_of_questions,
        num_of_respondents=args.num_of_respondents,
        stage=args.stage,
        user_email=args.user_email,
        question_type_distribution=question_type_distribution,
        resume_mode=args.resume,
        consultation_code=args.consultation_code,
    )


if __name__ == "__main__":
    main()
