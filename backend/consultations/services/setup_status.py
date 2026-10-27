from django.utils import timezone

from consultations.models import Consultation


def update_upload_status_for_questions(consultation: Consultation) -> None:
    questions = consultation.question_set.all()
    upload_status = (
        Consultation.UploadStatus.READY
        if questions.exists() and not questions.filter(type__isnull=True).exists()
        else Consultation.UploadStatus.QUESTIONS_PENDING
    )
    Consultation.objects.filter(id=consultation.id).update(
        upload_status=upload_status, modified_at=timezone.now()
    )
