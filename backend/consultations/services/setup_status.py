from django.utils import timezone

from consultations.models import Consultation


def update_survey_import_status_for_questions(consultation: Consultation) -> None:
    questions = consultation.question_set.all()
    survey_import_status = (
        Consultation.SurveyImportStatus.IMPORT_COMPLETE
        if questions.exists() and not questions.filter(type__isnull=True).exists()
        else Consultation.SurveyImportStatus.PENDING_QUESTIONS
    )
    Consultation.objects.filter(id=consultation.id).update(
        survey_import_status=survey_import_status, modified_at=timezone.now()
    )
