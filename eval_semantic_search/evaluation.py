"""
Semantic search precision evaluation.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from pgvector.django import CosineDistance

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Response,
    Theme,
)

logger = logging.getLogger(__name__)


@dataclass
class ThemeResult:
    theme_name: str
    theme_description: str
    total_responses_with_theme: int
    true_positives: int
    precision: float


def evaluate_consultation(consultation_code: str, embedding_generator, k: int = 20) -> Dict[str, Any]:
    """Evaluate semantic search for a consultation"""
    
    consultation = Consultation.objects.get(slug=consultation_code)
    questions = Question.objects.filter(consultation=consultation, has_free_text=True).order_by('number')
    
    all_results = []
    all_precisions = []
    
    for question in questions:
        logger.info(f"Evaluating question {question.number}")
        question_results = evaluate_question(question, embedding_generator, k)
        
        all_results.append({
            'question_number': question.number,
            'question_text': question.text,
            'themes': [
                {
                    'theme_name': r.theme_name,
                    'total_responses_with_theme': r.total_responses_with_theme,
                    'true_positives': r.true_positives,
                    'precision': r.precision
                }
                for r in question_results
            ],
            'average_precision': sum(r.precision for r in question_results) / len(question_results) if question_results else 0
        })
        
        all_precisions.extend([r.precision for r in question_results])
    
    return {
        'consultation': consultation.title,
        'total_questions': len(questions),
        'total_themes': len(all_precisions),
        'overall_precision': sum(all_precisions) / len(all_precisions) if all_precisions else 0,
        'questions': all_results
    }


def evaluate_question(question: Question, embedding_generator, k: int) -> List[ThemeResult]:
    """Evaluate all themes for a question"""
    
    # Exclude generic themes that shouldn't be evaluated
    excluded_themes = ["None of the Above", "No Reason Given", "Other"]
    themes = Theme.objects.filter(question=question).exclude(name__in=excluded_themes)
    results = []
    
    for theme in themes:
        # Create search query
        query = f"{theme.name}: {theme.description}"
        query_embedding = embedding_generator.embed_text(query)
        
        # Get top k responses
        top_responses = Response.objects.filter(
            question=question,
            free_text__isnull=False
        ).exclude(
            free_text=''
        ).annotate(
            distance=CosineDistance('embedding', query_embedding)
        ).order_by('distance')[:k]
        
        # Get ground truth
        responses_with_theme = Response.objects.filter(
            question=question,
            annotation__responseannotationtheme__theme=theme,
            annotation__responseannotationtheme__is_original_ai_assignment=True
        ).values_list('id', flat=True)
        
        # Calculate precision
        top_ids = {r.id for r in top_responses}
        true_positives = len(top_ids.intersection(set(responses_with_theme)))
        
        # Use min(k, total_responses_with_theme) for fair precision calculation
        # If there are only 5 responses with the theme, we should calculate precision out of 5, not 20
        denominator = min(k, len(responses_with_theme))
        precision = true_positives / denominator if denominator > 0 else 0
        
        results.append(ThemeResult(
            theme_name=theme.name,
            theme_description=theme.description,
            total_responses_with_theme=len(responses_with_theme),
            true_positives=true_positives,
            precision=precision
        ))
    
    return results