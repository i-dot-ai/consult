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
        f"https://consult-{environment.value.lower()}.ai.cabinetoffice.gov.uk"
        if environment.value.lower() in ["dev", "preprod"]
        else "https://consult.ai.cabinetoffice.gov.uk"
    )

    # Create HTTP client with authentication header
    client = requests.Session()
    client.headers.update({"x-amzn-oidc-data": jwt, "Content-Type": "application/json"})
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

    print("Sending to", endpoint)

    response = client.post(f"{endpoint}/api/consultations/", json=create_consultation_data)
    response.raise_for_status()
    consultation = response.status_code
    print(f"\nCreated consultation: {consultation}")


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
        name_of_consultation=args.name_of_consultation,
        num_of_questions=args.num_of_questions,
        num_of_respondents=args.num_of_respondents,
        stage=args.stage,
        include_s3_generation=args.include_s3_generation,
    )


if __name__ == "__main__":
    main()
