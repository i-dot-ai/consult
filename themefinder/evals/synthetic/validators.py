"""Dataset validation utilities for synthetic data generation."""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of dataset validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_dataset(
    dataset_path: Path,
    *,
    expected_responses_per_question: int | None = None,
) -> ValidationResult:
    """Validate a generated dataset's completeness and referential integrity.

    Args:
        dataset_path: Root directory of the generated dataset.
        expected_responses_per_question: Expected response count for every question,
            when known by the generator.
    """
    errors: list[str] = []
    warnings: list[str] = []
    inputs_dir = dataset_path / "inputs"
    if not inputs_dir.exists():
        return ValidationResult(is_valid=False, errors=["Missing inputs/ directory"])

    question_parts = sorted(
        d
        for d in inputs_dir.iterdir()
        if d.is_dir() and d.name.startswith("question_part")
    )
    if not question_parts:
        return ValidationResult(
            is_valid=False, errors=["No question_part directories found"]
        )

    response_ids_by_question: dict[str, set[int]] = {}
    all_response_ids: set[int] = set()
    for question_part in question_parts:
        response_ids = _validate_question_part(
            question_part,
            expected_responses_per_question,
            errors,
        )
        response_ids_by_question[question_part.name] = response_ids
        all_response_ids.update(response_ids)

    _validate_respondents(inputs_dir / "respondents.jsonl", all_response_ids, errors)

    outputs_dir = dataset_path / "outputs" / "mapping"
    if not outputs_dir.exists():
        errors.append("Missing outputs/mapping/ directory")
    else:
        date_dirs = sorted(d for d in outputs_dir.iterdir() if d.is_dir())
        if not date_dirs:
            errors.append("No output date directories found")
        else:
            _validate_outputs(
                date_dirs[-1], response_ids_by_question, dataset_path, errors
            )

    return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)


def _load_jsonl(path: Path, errors: list[str], description: str) -> list[dict]:
    """Load a JSONL file, returning only valid object records."""
    records: list[dict] = []
    try:
        with open(path) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(
                        f"Invalid JSON at line {line_num} in {description}: {exc}"
                    )
                    continue
                if not isinstance(record, dict):
                    errors.append(f"Invalid record at line {line_num} in {description}")
                    continue
                records.append(record)
    except OSError as exc:
        errors.append(f"Could not read {description}: {exc}")
    return records


def _validate_question_part(
    question_part: Path,
    expected_responses: int | None,
    errors: list[str],
) -> set[int]:
    """Validate input files for one question part and return response IDs."""
    question_name = question_part.name
    question_file = question_part / "question.json"
    if not question_file.exists():
        errors.append(f"Missing question.json in {question_name}")
    else:
        try:
            with open(question_file) as f:
                question = json.load(f)
            if not question.get("question_text"):
                errors.append(f"Missing question_text in {question_name}/question.json")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Invalid question.json in {question_name}: {exc}")

    responses_file = question_part / "responses.jsonl"
    if not responses_file.exists():
        errors.append(f"Missing responses.jsonl in {question_name}")
        return set()

    response_ids: set[int] = set()
    for line_num, response in enumerate(
        _load_jsonl(responses_file, errors, f"{question_name}/responses.jsonl"), 1
    ):
        response_id = response.get("response_id")
        if not isinstance(response_id, int):
            errors.append(
                f"Missing or invalid response_id at record {line_num} in {question_name}/responses.jsonl"
            )
            continue
        if response_id in response_ids:
            errors.append(
                f"Duplicate response_id {response_id} in {question_name}/responses.jsonl"
            )
            continue
        if (
            not isinstance(response.get("response"), str)
            or not response["response"].strip()
        ):
            errors.append(
                f"Missing or invalid response text for response {response_id} in {question_name}"
            )
            continue
        response_ids.add(response_id)

    if expected_responses is not None and len(response_ids) != expected_responses:
        errors.append(
            f"Expected {expected_responses} responses in {question_name}, found {len(response_ids)}"
        )
    return response_ids


def _validate_respondents(
    respondents_file: Path,
    expected_response_ids: set[int],
    errors: list[str],
) -> None:
    """Validate respondent records cover every response ID."""
    if not respondents_file.exists():
        errors.append("Missing respondents.jsonl")
        return

    respondent_ids = {
        record.get("response_id")
        for record in _load_jsonl(respondents_file, errors, "respondents.jsonl")
        if isinstance(record.get("response_id"), int)
    }
    missing = expected_response_ids - respondent_ids
    if missing:
        errors.append(
            f"Missing respondent entries for response_ids: {sorted(missing)[:5]}..."
        )


def _validate_outputs(
    date_dir: Path,
    response_ids_by_question: dict[str, set[int]],
    dataset_path: Path,
    errors: list[str],
) -> None:
    """Validate all generated ground-truth files for every question part."""
    for question_name, expected_response_ids in response_ids_by_question.items():
        output_dir = date_dir / question_name
        if not output_dir.exists():
            errors.append(f"Missing output directory for {question_name}")
            continue

        theme_ids = _validate_themes(output_dir / "themes.json", dataset_path, errors)
        _validate_mapping(
            output_dir / "mapping.jsonl",
            question_name,
            expected_response_ids,
            theme_ids,
            errors,
        )
        _validate_record_ids(
            output_dir / "sentiment.jsonl",
            question_name,
            expected_response_ids,
            "sentiment",
            {"AGREE", "DISAGREE", "UNCLEAR"},
            "position",
            errors,
        )
        _validate_record_ids(
            output_dir / "detail_detection.jsonl",
            question_name,
            expected_response_ids,
            "detail_detection",
            {"YES", "NO"},
            "evidence_rich",
            errors,
        )


def _validate_themes(
    themes_file: Path, dataset_path: Path, errors: list[str]
) -> set[str]:
    """Validate themes and return their IDs."""
    if not themes_file.exists():
        errors.append(f"Missing themes.json in {themes_file.parent.name}")
        return set()
    try:
        with open(themes_file) as f:
            themes = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid themes.json in {themes_file.parent.name}: {exc}")
        return set()

    if not isinstance(themes, list):
        errors.append(
            f"Invalid themes.json in {themes_file.parent.name}: expected an array"
        )
        return set()

    theme_ids = {
        theme.get("topic_id")
        for theme in themes
        if isinstance(theme, dict) and isinstance(theme.get("topic_id"), str)
    }
    if len(theme_ids) != len(themes):
        errors.append(
            f"Missing or duplicate topic_id in {themes_file.relative_to(dataset_path)}"
        )
    for special_theme in ("XX", "XY"):
        if special_theme not in theme_ids:
            errors.append(
                f"Missing special theme {special_theme} in {themes_file.relative_to(dataset_path)}"
            )
    return theme_ids


def _validate_mapping(
    mapping_file: Path,
    question_name: str,
    expected_response_ids: set[int],
    theme_ids: set[str],
    errors: list[str],
) -> None:
    """Validate mapping records and their theme references."""
    if not mapping_file.exists():
        errors.append(f"Missing mapping.jsonl in {question_name}")
        return

    records = _load_jsonl(mapping_file, errors, f"{question_name}/mapping.jsonl")
    seen_ids: set[int] = set()
    for record in records:
        response_id = record.get("response_id")
        if not isinstance(response_id, int):
            errors.append(
                f"Missing or invalid response_id in {question_name}/mapping.jsonl"
            )
            continue
        if response_id in seen_ids:
            errors.append(
                f"Duplicate mapping for response_id {response_id} in {question_name}"
            )
        seen_ids.add(response_id)

        labels = record.get("labels")
        stances = record.get("stances")
        if not isinstance(labels, list) or not labels:
            errors.append(
                f"Missing labels for response {response_id} in {question_name}"
            )
            continue
        if not isinstance(stances, list) or len(labels) != len(stances):
            errors.append(
                f"Labels/stances length mismatch for response {response_id} in {question_name}"
            )
        for label in labels:
            if label not in theme_ids:
                errors.append(
                    f"Invalid theme reference '{label}' for response {response_id} in {question_name}"
                )
        if any(stance not in {"POSITIVE", "NEGATIVE", "NEUTRAL"} for stance in stances):
            errors.append(
                f"Invalid stance for response {response_id} in {question_name}"
            )

    _validate_exact_ids(
        seen_ids, expected_response_ids, "mapping", question_name, errors
    )


def _validate_record_ids(
    path: Path,
    question_name: str,
    expected_response_ids: set[int],
    record_type: str,
    allowed_values: set[str],
    value_key: str,
    errors: list[str],
) -> None:
    """Validate one record per response with an allowed categorical value."""
    if not path.exists():
        errors.append(f"Missing {path.name} in {question_name}")
        return

    records = _load_jsonl(path, errors, f"{question_name}/{path.name}")
    seen_ids: set[int] = set()
    for record in records:
        response_id = record.get("response_id")
        if not isinstance(response_id, int):
            errors.append(
                f"Missing or invalid response_id in {question_name}/{path.name}"
            )
            continue
        if response_id in seen_ids:
            errors.append(
                f"Duplicate {record_type} record for response_id {response_id} in {question_name}"
            )
        seen_ids.add(response_id)
        if record.get(value_key) not in allowed_values:
            errors.append(
                f"Invalid {value_key} for response {response_id} in {question_name}/{path.name}"
            )

    _validate_exact_ids(
        seen_ids, expected_response_ids, record_type, question_name, errors
    )


def _validate_exact_ids(
    actual_ids: set[int],
    expected_ids: set[int],
    record_type: str,
    question_name: str,
    errors: list[str],
) -> None:
    """Ensure a ground-truth file has exactly one record for every response."""
    missing_ids = expected_ids - actual_ids
    extra_ids = actual_ids - expected_ids
    if missing_ids:
        errors.append(
            f"Missing {record_type} records for response_ids {sorted(missing_ids)[:5]} in {question_name}"
        )
    if extra_ids:
        errors.append(
            f"Unexpected {record_type} records for response_ids {sorted(extra_ids)[:5]} in {question_name}"
        )
