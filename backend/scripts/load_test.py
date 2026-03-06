#!/usr/bin/env python3
"""
Load testing script for the Consult application.

This script generates load tests by simulating multiple respondents
answering consultation questions.
"""

import argparse
import random
from enum import Enum
from pathlib import Path
from typing import Any

import requests
import yaml


class Environment(str, Enum):
    """Environment options for load testing."""

    DEV = "dev"
    PREPROD = "preprod"
    PROD = "prod"


class Stage(str, Enum):
    """Stage options for consultation analysis."""

    NO_THEMES = "no themes"
    FINALISING_THEMES = "finalising themes"
    WITH_CANDIDATE_THEMES = "with candidate themes"
    ANALYSIS = "analysis"


def get_random_question(data: dict[str, Any]) -> str:
    """Get a random question from the YAML data.

    Args:
        data: Dictionary containing questions and responses from YAML

    Returns:
        A random question string
    """
    questions = data.get("questions", [])
    if not questions:
        raise ValueError("No questions found in YAML data")
    return random.choice(questions)


def get_random_response(data: dict[str, Any]) -> str:
    """Get a random response from the YAML data.

    Args:
        data: Dictionary containing questions and responses from YAML

    Returns:
        A random response string
    """
    responses = data.get("responses", [])
    if not responses:
        raise ValueError("No responses found in YAML data")
    return random.choice(responses)


def load_sample_data(yaml_path: Path) -> dict[str, Any]:
    """Load sample questions and responses from YAML file.

    Args:
        yaml_path: Path to the YAML file

    Returns:
        Dictionary containing questions and responses
    """
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def run_load_test(
    environment: Environment,
    jwt: str,
    waf_token: str,
    name_of_consultation: str,
    num_of_questions: int,
    num_of_respondents: int,
    stage: Stage,
    include_s3_generation: bool,
) -> None:
    """Run the load test with the specified parameters.

    Args:
        environment: Environment to run the test against
        jwt: JWT token for authentication
        waf_token: WAF token for authentication
        name_of_consultation: Name of the consultation
        num_of_questions: Number of questions to generate
        num_of_respondents: Number of respondents to simulate
        stage: Stage of the consultation
        include_s3_generation: Whether to include S3 generation
    """
    # Load sample data
    yaml_path = Path(__file__).parent / "sample_data.yaml"
    data = load_sample_data(yaml_path)

    # Main processing loop - placeholder for now
    print("Running load test with the following parameters:")
    print(f"  Environment: {environment.value}")
    print(f"  Consultation: {name_of_consultation}")
    print(f"  Number of questions: {num_of_questions}")
    print(f"  Number of respondents: {num_of_respondents}")
    print(f"  Stage: {stage}")
    print(f"  Include S3 generation: {include_s3_generation}")
    print(f"\nSample question: {get_random_question(data)}")
    print(f"Sample response: {get_random_response(data)}")

    endpoint = (
        f"https://consult-backend-external-{environment.value.lower()}.ai.cabinetoffice.gov.uk"
        if environment.value.lower() in ["dev", "preprod"]
        else "https://consult-backend-external.ai.cabinetoffice.gov.uk"
    )

    print(f"\nStep 1: Validating OIDC token and obtaining Django JWT...")

    client = requests.Session()
    validate_response = client.post(
        f"{endpoint}/api/validate-token/",
        json={"internal_access_token": jwt},
        headers={
            "Content-Type": "application/json",
            "x-external-access-token": waf_token
        }
    )

    if validate_response.status_code != 200:
        print(f"Token validation failed!")
        print(f"Status: {validate_response.status_code}")
        print(f"Response: {validate_response.text}")
        validate_response.raise_for_status()

    token_data = validate_response.json()
    django_jwt = token_data["access"]
    session_id = token_data.get("sessionId")

    print(f"✓ Token validated successfully")
    print(f"  Django JWT: {django_jwt[:50]}...")
    print(f"  Session ID: {session_id}")

    # Step 2: Update client headers with Django JWT for subsequent requests
    client.headers.update({
        "Authorization": f"Bearer {django_jwt}",
        "x-external-access-token": waf_token,
        "Content-Type": "application/json"
    })

    stage_mapping = {
        Stage.NO_THEMES: "theme_sign_off",
        Stage.FINALISING_THEMES: "theme_sign_off",
        Stage.WITH_CANDIDATE_THEMES: "theme_mapping",
        Stage.ANALYSIS: "analysis",
    }

    create_consultation_data = {
        "title": name_of_consultation,
        "code": name_of_consultation.lower().replace(" ", "-"),
        "stage": stage_mapping.get(stage, "theme_sign_off"),
        "display_ai_selected_themes": True,
        "model_name": "gpt-4.1",
    }

    print(f"\nStep 2: Creating consultation with authenticated session...")
    print(f"Sending POST request to: {endpoint}/api/consultations/")
    print(f"Headers: Authorization=Bearer {django_jwt[:30]}..., x-external-access-token={waf_token}")
    print(f"Payload: {create_consultation_data}\n")

    response = client.post(f"{endpoint}/api/consultations/", json=create_consultation_data)

    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    if response.status_code != 201:
        print(f"Response Body: {response.text[:1000]}")

    response.raise_for_status()
    consultation = response.json()
    consultation_id = consultation.get('id')
    print(f"\n✓ Successfully created consultation!")
    print(f"  Consultation ID: {consultation_id}")
    print(f"  Consultation Code: {consultation['code']}")
    
    # Step 3: Create questions and responses using Django ORM
    # Note: The API does not support POST for questions/responses directly
    # They are typically imported via /api/consultations/setup/ from S3
    # For load testing, we'll need to use Django ORM or database access
    
    print(f"\nStep 3: Creating {num_of_questions} questions with {num_of_respondents} responses each...")
    print(f"Note: Questions and Responses cannot be created via REST API")
    print(f"      They must be created using Django ORM or imported from S3")
    print(f"\nTo populate this consultation with test data:")
    print(f"  1. Use Django shell: python manage.py shell")
    print(f"  2. Create questions using: Question.objects.create(consultation_id='{consultation_id}', ...)")
    print(f"  3. Create respondents using: Respondent.objects.create(consultation_id='{consultation_id}', ...)")
    print(f"  4. Create responses using: Response.objects.create(question=question, respondent=respondent, ...)")
    print(f"\nAlternatively, prepare S3 data and use: POST /api/consultations/setup/")
    
    # TODO: If include_s3_generation is True, generate S3 files and trigger import
    if include_s3_generation:
        print(f"\n⚠ S3 generation not yet implemented")
        print(f"  This would generate CSV/JSON files in S3 with:")
        print(f"    - {num_of_questions} questions")
        print(f"    - {num_of_respondents} respondents")
        print(f"    - {num_of_respondents * num_of_questions} responses")
        print(f"  Then trigger: POST {endpoint}/api/consultations/setup/")



def main() -> None:
    """Parse arguments and run the load test."""
    parser = argparse.ArgumentParser(
        prog="load_test",
        description="Load testing script for the Consult application",
        usage="For load testing the consultation app. Please provide the JWT found from the ECS logs of your chosen"
        "environments backend service. If you've chosen to add S3 files, then your CLI session that runs this"
        "script needs to be AWS-vault exec'd.",
    )

    parser.add_argument(
        "--environment",
        type=Environment,
        choices=list(Environment),
        default=Environment.DEV,
        help="Environment to run the test against (default: dev)",
    )

    parser.add_argument(
        "--jwt",
        type=str,
        required=True,
        help="JWT token for authentication (required, secret)",
    )

    parser.add_argument(
        "--waf-token",
        type=str,
        required=True,
        help="WAF token for authentication (required, secret)",
    )

    parser.add_argument(
        "--name-of-consultation",
        type=str,
        required=True,
        help="Name of the consultation (required)",
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
        default=10000,
        help="Number of respondents to simulate (default: 10,000)",
    )

    parser.add_argument(
        "--stage",
        type=Stage,
        choices=list(Stage),
        required=True,
        help="Stage of the consultation (required)",
    )

    parser.add_argument(
        "--include-s3-generation",
        action="store_true",
        default=False,
        help="Include S3 generation (default: false)",
    )

    args = parser.parse_args()

    run_load_test(
        environment=args.environment,
        jwt=args.jwt,
        waf_token=args.waf_token,
        name_of_consultation=args.name_of_consultation,
        num_of_questions=args.num_of_questions,
        num_of_respondents=args.num_of_respondents,
        stage=args.stage,
        include_s3_generation=args.include_s3_generation,
    )


if __name__ == "__main__":
    main()
