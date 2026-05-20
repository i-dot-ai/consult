import json
from datetime import date

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand

from consultations.dummy_data import (
    AGE_GROUPS,
    NUMBER_RESPONDENTS,
    REGIONS,
    RESPONDENT_TYPES,
    SAMPLE_QUESTIONS_PATH,
    candidate_theme_keys_for_respondent,
)
from hosting_environment import HostingEnvironment

TIMESTAMP = date.today().isoformat()


def _to_jsonl(records):
    return "\n".join(json.dumps(r) for r in records)


def _load_questions():
    with open(SAMPLE_QUESTIONS_PATH, "r") as f:
        return json.load(f)


def _build_respondents():
    return [
        {
            "themefinder_id": i,
            "demographic_data": {
                "region": [REGIONS[i % len(REGIONS)]],
                "age_group": [AGE_GROUPS[i % len(AGE_GROUPS)]],
                "respondent_type": [RESPONDENT_TYPES[i % len(RESPONDENT_TYPES)]],
            },
        }
        for i in range(1, NUMBER_RESPONDENTS + 1)
    ]


def _build_responses(question_data):
    free_text_answers = question_data.get("free_text_answers", [])
    if not free_text_answers:
        return []
    non_empty = [a for a in free_text_answers if a]
    return [
        {"themefinder_id": i, "text": non_empty[i % len(non_empty)]}
        for i in range(1, NUMBER_RESPONDENTS + 1)
    ]


def _build_multi_choice(question_data):
    options = question_data.get("multiple_choice_options", [])
    if not options:
        return []
    return [
        {"themefinder_id": i, "options": [options[i % len(options)]]}
        for i in range(1, NUMBER_RESPONDENTS + 1)
    ]


def _build_question_json(question_data):
    return {
        "question_text": question_data["question_text"],
        "question_number": question_data["number"],
        "has_free_text": question_data["has_free_text"],
        "multi_choice_options": question_data.get("multiple_choice_options", []),
    }


def _build_clustered_themes(question_data):
    """Build clustered_themes.json from the flat candidate_themes list."""
    candidate_themes = question_data.get("candidate_themes", [])
    key_to_topic_id = {}
    theme_nodes = []

    for i, theme in enumerate(candidate_themes, start=1):
        topic_id = str(i)
        key_to_topic_id[theme["key"]] = topic_id
        parent_key = theme.get("parent_key")
        parent_id = key_to_topic_id.get(parent_key, "0") if parent_key else "0"
        theme_nodes.append(
            {
                "topic_id": topic_id,
                "parent_id": parent_id,
                "topic_label": theme["name"],
                "topic_description": theme.get("description", ""),
                "source_topic_count": max(1, theme.get("approximate_frequency", 10)),
            }
        )

    return {"theme_nodes": theme_nodes}


def _themes_grouped_by_parent(candidate_themes):
    """Group flat themes by parent_key (None for top-level)."""
    groups = {}
    for theme in candidate_themes:
        groups.setdefault(theme.get("parent_key"), []).append(theme)
    return groups


def _build_candidate_themes_json(question_data):
    """Build themes.json from all candidate_themes (for THEME_SIGN_OFF mapping)."""
    candidate_themes = question_data.get("candidate_themes", [])
    return [
        {
            "theme_key": theme["key"],
            "theme_name": theme["name"],
            "theme_description": theme.get("description", ""),
        }
        for theme in candidate_themes
    ]


DEFAULT_THEMES = [
    {
        "theme_key": "OTHER",
        "theme_name": "Other",
        "theme_description": "The response discusses an issue not covered by the listed themes",
    },
    {
        "theme_key": "NO_REASON",
        "theme_name": "No Reason Given",
        "theme_description": "The response does not provide a substantive answer to the question",
    },
]


def _build_themes_json(question_data):
    """Build themes.json (selected themes) from candidate_themes marked as selected, plus defaults."""
    candidate_themes = question_data.get("candidate_themes", [])
    themes = [
        {
            "theme_key": theme["key"],
            "theme_name": theme["name"],
            "theme_description": theme.get("description", ""),
        }
        for theme in candidate_themes
        if theme.get("selected")
    ]
    themes.extend(DEFAULT_THEMES)
    return themes




def _build_candidate_theme_mappings(question_data):
    """Build mapping.jsonl for candidate themes using deterministic assignment per sibling group."""
    candidate_themes = question_data.get("candidate_themes", [])
    if not candidate_themes:
        return []

    groups = _themes_grouped_by_parent(candidate_themes)
    respondent_keys = {i: [] for i in range(1, NUMBER_RESPONDENTS + 1)}
    for sibling_themes in groups.values():
        group_keys = [t["key"] for t in sibling_themes]
        for i in range(1, NUMBER_RESPONDENTS + 1):
            respondent_keys[i].extend(candidate_theme_keys_for_respondent(i, group_keys))

    return [
        {"themefinder_id": i, "theme_keys": respondent_keys[i]}
        for i in range(1, NUMBER_RESPONDENTS + 1)
    ]


def _build_theme_mappings(question_data):
    """Build mapping.jsonl for selected themes (analysis stage) using deterministic assignment."""
    themes = _build_themes_json(question_data)
    if not themes:
        return []
    theme_keys = [t["theme_key"] for t in themes]
    return [
        {"themefinder_id": i, "theme_keys": candidate_theme_keys_for_respondent(i, theme_keys)}
        for i in range(1, NUMBER_RESPONDENTS + 1)
    ]


def _build_sentiments():
    choices = ["AGREEMENT", "DISAGREEMENT", "UNCLEAR"]
    return [
        {"themefinder_id": i, "sentiment": choices[i % len(choices)]}
        for i in range(1, NUMBER_RESPONDENTS + 1)
    ]


def _build_evidence_rich():
    choices = ["YES", "NO"]
    return [
        {"themefinder_id": i, "evidence_rich": choices[i % len(choices)]}
        for i in range(1, NUMBER_RESPONDENTS + 1)
    ]


def _build_themes_csv(question_data):
    """Build themes.csv content (selected themes) for the assign-themes batch job."""
    themes = _build_themes_json(question_data)
    lines = ["Theme Name,Theme Description"]
    for theme in themes:
        name = theme["theme_name"]
        description = theme["theme_description"]
        lines.append(f"{name},{description}")
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Reset and seed S3 with dummy consultation data matching the DB. Only runs on deployed non-prod environments."

    def handle(self, *args, **options):
        if HostingEnvironment.is_production():
            self.stdout.write("Skipping S3 seed on production.")
            return

        if not HostingEnvironment.is_deployed():
            self.stdout.write("Skipping S3 seed on local environment (no real S3 bucket).")
            return

        s3_client = boto3.client("s3")
        bucket = settings.AWS_BUCKET_NAME

        self._delete_existing_data(s3_client, bucket)
        questions_data = _load_questions()

        # S3-only consultation (no DB record)
        self._seed_consultation(s3_client, bucket, "dummy-s3-only", questions_data)

        # SETUP — inputs only
        self._seed_consultation(s3_client, bucket, "dummy-setup", questions_data)

        # Starting finalising themes — has clustered themes + candidate theme mappings
        self._seed_consultation(
            s3_client,
            bucket,
            "dummy-start-finalising-themes",
            questions_data,
            include_clustered_themes=True,
            include_candidate_theme_mappings=True,
        )

        # Finished finalising themes — has clustered themes + themes.csv (ready for assignment)
        self._seed_consultation(
            s3_client,
            bucket,
            "dummy-finished-finalising-themes",
            questions_data,
            include_clustered_themes=True,
            include_candidate_theme_mappings=True,
            include_themes_csv=True,
        )

        # ANALYSIS — has everything from earlier stages + mapping outputs
        self._seed_consultation(
            s3_client,
            bucket,
            "dummy-analysis",
            questions_data,
            include_clustered_themes=True,
            include_candidate_theme_mappings=True,
            include_mapping_outputs=True,
            include_themes_csv=True,
        )

        self.stdout.write("S3 seed complete.")

    def _delete_existing_data(self, s3_client, bucket):
        prefix = "app_data/consultations/"
        paginator = s3_client.get_paginator("list_objects_v2")
        objects_to_delete = []

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                objects_to_delete.append({"Key": obj["Key"]})

        if objects_to_delete:
            # delete_objects supports max 1000 keys per call
            for i in range(0, len(objects_to_delete), 1000):
                s3_client.delete_objects(
                    Bucket=bucket, Delete={"Objects": objects_to_delete[i : i + 1000]}
                )
            self.stdout.write(f"  Deleted {len(objects_to_delete)} existing objects.")

    def _seed_consultation(
        self,
        s3_client,
        bucket,
        code,
        questions_data,
        include_clustered_themes=False,
        include_candidate_theme_mappings=False,
        include_mapping_outputs=False,
        include_themes_csv=False,
    ):
        self.stdout.write(f"  Seeding S3 data for: {code}")
        prefix = f"app_data/consultations/{code}"

        # Respondents
        s3_client.put_object(
            Bucket=bucket,
            Key=f"{prefix}/inputs/respondents.jsonl",
            Body=_to_jsonl(_build_respondents()),
        )

        for question_data in questions_data:
            q_num = question_data["number"]
            q_prefix = f"{prefix}/inputs/question_part_{q_num}"

            # Question definition
            s3_client.put_object(
                Bucket=bucket,
                Key=f"{q_prefix}/question.json",
                Body=json.dumps(_build_question_json(question_data)),
            )

            # Free text responses
            if question_data["has_free_text"]:
                responses = _build_responses(question_data)
                if responses:
                    s3_client.put_object(
                        Bucket=bucket,
                        Key=f"{q_prefix}/responses.jsonl",
                        Body=_to_jsonl(responses),
                    )

            # Multi choice
            if question_data.get("multiple_choice_options"):
                multi_choice = _build_multi_choice(question_data)
                if multi_choice:
                    s3_client.put_object(
                        Bucket=bucket,
                        Key=f"{q_prefix}/multi_choice.jsonl",
                        Body=_to_jsonl(multi_choice),
                    )

            # Stage-specific outputs (only for free text questions)
            if not question_data["has_free_text"]:
                continue

            if include_clustered_themes:
                key = f"{prefix}/outputs/sign_off/{TIMESTAMP}/question_part_{q_num}/clustered_themes.json"
                s3_client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=json.dumps(_build_clustered_themes(question_data)),
                )

            if include_candidate_theme_mappings:
                out_prefix = f"{prefix}/outputs/mapping/{TIMESTAMP}/question_part_{q_num}"
                themes = _build_candidate_themes_json(question_data)
                s3_client.put_object(
                    Bucket=bucket,
                    Key=f"{out_prefix}/themes.json",
                    Body=json.dumps(themes),
                )
                s3_client.put_object(
                    Bucket=bucket,
                    Key=f"{out_prefix}/mapping.jsonl",
                    Body=_to_jsonl(_build_candidate_theme_mappings(question_data)),
                )

            if include_themes_csv:
                s3_client.put_object(
                    Bucket=bucket,
                    Key=f"{q_prefix}/themes.csv",
                    Body=_build_themes_csv(question_data),
                )

            if include_mapping_outputs:
                out_prefix = f"{prefix}/outputs/mapping/{TIMESTAMP}/question_part_{q_num}"
                themes = _build_themes_json(question_data)
                s3_client.put_object(
                    Bucket=bucket,
                    Key=f"{out_prefix}/themes.json",
                    Body=json.dumps(themes),
                )
                s3_client.put_object(
                    Bucket=bucket,
                    Key=f"{out_prefix}/mapping.jsonl",
                    Body=_to_jsonl(_build_theme_mappings(question_data)),
                )
                s3_client.put_object(
                    Bucket=bucket,
                    Key=f"{out_prefix}/sentiment.jsonl",
                    Body=_to_jsonl(_build_sentiments()),
                )
                s3_client.put_object(
                    Bucket=bucket,
                    Key=f"{out_prefix}/detail_detection.jsonl",
                    Body=_to_jsonl(_build_evidence_rich()),
                )
