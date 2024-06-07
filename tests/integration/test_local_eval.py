import json
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command

from consultation_analyser.consultations.public_schema import ConsultationWithResponsesAndThemes
from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
def test_local_eval():
    UserFactory(email="email@example.com")

    file_path = settings.BASE_DIR / "tests" / "examples" / "chocolate.json"

    call_command("evaluate", input=file_path, embedding_model="fake")

    output_folder = Path("tmp/eval/dummy-chocolate-consultation")
    json_with_themes_path = output_folder / "consultation_with_themes.json"
    # timings = output_folder / "timings.json"

    with_themes = json.loads(open(json_with_themes_path).read())

    # Bail if it's invalid
    ConsultationWithResponsesAndThemes(**with_themes)