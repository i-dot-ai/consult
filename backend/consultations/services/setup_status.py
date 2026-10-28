from django.utils import timezone

from consultations.models import Consultation


def update_servey_import_status_for_questions(consultation: Consultation) -> None:
    questions = consultation.question_set.all()
    servey_import_status = (
        Consultation.ServeyImportStatus.IMPORT_COMPLETE
        if questions.exists() and not questions.filter(type__isnull=True).exists()
        else Consultation.ServeyImportStatus.PENDING_QUESTIONS
    )
    Consultation.objects.filter(id=consultation.id).update(
        servey_import_status=servey_import_status, modified_at=timezone.now()
    )
