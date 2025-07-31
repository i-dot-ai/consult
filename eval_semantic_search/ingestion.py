"""
Local file ingestion for consultation data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from django.contrib.postgres.search import SearchVector

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    Theme,
)

logger = logging.getLogger(__name__)


def import_consultation_data(consultation_code: str, embedding_generator, output_dir_timestamp: str, use_question_prefix: bool = False):
    """Import consultation data from local files"""
    # Always use eval_semantic_search/data as the base path
    from pathlib import Path
    eval_dir = Path(__file__).parent
    base_path = eval_dir / 'data' / consultation_code

    # Create or get consultation
    consultation, created = Consultation.objects.get_or_create(
        slug=consultation_code, defaults={"title": f"Evaluation: {consultation_code}"}
    )

    if not created:
        logger.info(f"Clearing existing data for {consultation_code}")
        _clear_consultation_data(consultation)

    # Import data
    _import_respondents(consultation, base_path / "inputs" / "respondents.jsonl")
    _import_questions_and_responses(consultation, base_path / "inputs", embedding_generator, output_dir_timestamp, use_question_prefix, base_path)

    return consultation


def _clear_consultation_data(consultation: Consultation):
    """Clear existing consultation data"""
    ResponseAnnotationTheme.objects.filter(
        response_annotation__response__question__consultation=consultation
    ).delete()
    ResponseAnnotation.objects.filter(response__question__consultation=consultation).delete()
    Response.objects.filter(question__consultation=consultation).delete()
    Theme.objects.filter(question__consultation=consultation).delete()
    Question.objects.filter(consultation=consultation).delete()
    Respondent.objects.filter(consultation=consultation).delete()


def _import_respondents(consultation: Consultation, file_path: Path):
    """Import respondents from JSONL file"""
    respondents = []

    with open(file_path, "r") as f:
        for line in f:
            data = json.loads(line)
            respondents.append(
                Respondent(
                    consultation=consultation,
                    themefinder_id=data["themefinder_id"],
                    demographics=data.get("demographics", {}),
                )
            )

    Respondent.objects.bulk_create(respondents)
    logger.info(f"Imported {len(respondents)} respondents")


def _import_questions_and_responses(
    consultation: Consultation, inputs_path: Path, embedding_generator, output_dir_timestamp: str, use_question_prefix: bool = False, base_path: Optional[Path] = None
):
    """Import questions and responses"""

    # Get question folders
    question_folders = sorted(
        [f for f in inputs_path.iterdir() if f.is_dir() and f.name.startswith("question_part_")]
    )

    for folder in question_folders:
        question_num = int(folder.name.replace("question_part_", ""))

        # Load question
        with open(folder / "question.json", "r") as f:
            question_data = json.load(f)

        question = Question.objects.create(
            consultation=consultation,
            number=question_num,
            text=question_data["question_text"],
            has_free_text=question_data.get("has_free_text", True),
            has_multiple_choice=question_data.get("has_multiple_choice", False),
            multiple_choice_options=question_data.get("multiple_choice_options", []),
        )

        if question.has_free_text:
            _import_responses(question, folder / "responses.jsonl", embedding_generator, use_question_prefix)

            # Import themes if available
            if base_path is not None:
                themes_path = (
                    base_path
                    / "outputs"
                    / "mapping"
                    / str(output_dir_timestamp)
                    / f"question_part_{question_num}"
                    / "themes.json"
                )
                if themes_path.exists():
                    _import_themes_and_annotations(question, themes_path.parent)


def _import_responses(question: Question, file_path: Path, embedding_generator, use_question_prefix: bool = False):
    """Import responses with embeddings"""

    respondent_dict = {
        r.themefinder_id: r for r in Respondent.objects.filter(consultation=question.consultation)
    }

    batch_texts = []
    batch_data = []

    with open(file_path, "r") as f:
        for line in f:
            data = json.loads(line)

            if data["themefinder_id"] not in respondent_dict:
                continue

            free_text = data.get("text", "")
            if not free_text:
                continue

            # Optionally prefix with question text
            if use_question_prefix:
                text_to_embed = f"Question: {question.text}\nAnswer: {free_text}"
            else:
                text_to_embed = free_text

            batch_texts.append(text_to_embed)
            batch_data.append(
                {
                    "respondent": respondent_dict[data["themefinder_id"]],
                    "question": question,
                    "free_text": free_text,
                    "chosen_options": data.get("chosen_options", []),
                }
            )

            # Process batch - reduced size to avoid rate limits
            if len(batch_texts) >= 20:
                _save_response_batch(batch_data, batch_texts, embedding_generator)
                batch_texts = []
                batch_data = []

    # Final batch
    if batch_texts:
        _save_response_batch(batch_data, batch_texts, embedding_generator)

    # Update search vectors
    for response in Response.objects.filter(question=question):
        response.search_vector = SearchVector("free_text")
        response.save(update_fields=["search_vector"])

    question.update_total_responses()


def _save_response_batch(batch_data: List[Dict], texts: List[str], embedding_generator):
    """Save batch of responses with embeddings"""
    embeddings = embedding_generator.embed_text(texts)

    responses = []
    for data, embedding in zip(batch_data, embeddings):
        responses.append(Response(**data, embedding=embedding))

    Response.objects.bulk_create(responses)


def _import_themes_and_annotations(question: Question, output_path: Path):
    """Import themes and annotations"""

    # Import themes
    with open(output_path / "themes.json", "r") as f:
        themes_data = json.load(f)

    themes = []
    for theme_data in themes_data:
        themes.append(
            Theme(
                question=question,
                name=theme_data["theme_name"],
                description=theme_data["theme_description"],
                key=theme_data.get("theme_key"),
            )
        )

    Theme.objects.bulk_create(themes)
    theme_map = {t.key: t.id for t in Theme.objects.filter(question=question)}

    # Import annotations
    responses = Response.objects.filter(question=question).values_list(
        "id", "respondent__themefinder_id"
    )

    # Create annotations
    annotations = []
    for response_id, _ in responses:
        annotations.append(
            ResponseAnnotation(
                response_id=response_id,
                sentiment=ResponseAnnotation.Sentiment.UNCLEAR,
                evidence_rich=ResponseAnnotation.EvidenceRich.NO,
                human_reviewed=False,
            )
        )

    ResponseAnnotation.objects.bulk_create(annotations)

    # Import theme mappings
    with open(output_path / "mapping.jsonl", "r") as f:
        mapping_data = {}
        for line in f:
            data = json.loads(line)
            mapping_data[data["themefinder_id"]] = data.get("theme_keys", [])

    # Create theme assignments
    annotation_map = {
        themefinder_id: annotation_id
        for annotation_id, themefinder_id in ResponseAnnotation.objects.filter(
            response__question=question
        ).values_list("id", "response__respondent__themefinder_id")
    }

    assignments = []
    for themefinder_id, theme_keys in mapping_data.items():
        if themefinder_id not in annotation_map:
            continue

        annotation_id = annotation_map[themefinder_id]
        for key in theme_keys:
            if key in theme_map:
                assignments.append(
                    ResponseAnnotationTheme(
                        response_annotation_id=annotation_id,
                        theme_id=theme_map[key],
                        is_original_ai_assignment=True,
                    )
                )

    ResponseAnnotationTheme.objects.bulk_create(assignments)
