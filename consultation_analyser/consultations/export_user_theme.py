import csv
from io import StringIO

import boto3
from django.conf import settings

from consultation_analyser.consultations.models import (
    Answer,
    Consultation,
    Question,
    QuestionPart,
    ThemeMapping,
)


def export_user_theme(consultation_slug: str, s3_key: str) -> None:
    consultation = Consultation.objects.get(slug=consultation_slug)
    output = []

    for question in Question.objects.filter(consultation=consultation):
        for question_part in QuestionPart.objects.filter(question=question):
            for response in Answer.objects.filter(question_part=question_part):
                original_themes = (
                    ThemeMapping.history.filter(answer=response)
                    .filter(stance__in=[ThemeMapping.Stance.POSITIVE, ThemeMapping.Stance.NEGATIVE])
                    .filter(history_type="+")
                )
                current_themes = ThemeMapping.objects.filter(answer=response).filter(
                    stance=ThemeMapping.Stance.HUMAN
                )
                auditors = set(
                    [
                        theme_mapping.history_user.email
                        for theme_mapping in ThemeMapping.history.filter(answer=response).filter(
                            stance=ThemeMapping.Stance.HUMAN
                        )
                    ]
                )
                output.append(
                    {
                        "Consultation": consultation.title,
                        "Question number": question.number,
                        "Question text": question.text,
                        "Question part text": question_part.text,
                        "Response text": response.text,
                        "Response has been audited": response.is_theme_mapping_audited,
                        # TODO: replace theme name with keys when they are available
                        "Original themes": ", ".join(
                            [theme_mapping.theme.name for theme_mapping in original_themes]
                        ),
                        "Current themes": ", ".join(
                            [theme_mapping.theme.name for theme_mapping in current_themes]
                        ),
                        "Auditors": ", ".join(list(auditors)),
                    }
                )

    if settings.ENVIRONMENT == "local":
        with open("downloads/example_consultation_theme_changes.csv", mode="w") as file:
            writer = csv.DictWriter(file, fieldnames=output[0].keys())
            writer.writeheader()
            for row in output:
                writer.writerow(row)
    else:
        if len(s3_key) == 0:
            raise ValueError("s3_key cannot be empty")

        s3_client = boto3.client("s3")

        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=output[0].keys())
        writer.writeheader()
        for row in output:
            writer.writerow(row)

        s3_client.put_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=f"{s3_key}/consultation_theme_changes.csv",
            Body=csv_buffer.getvalue(),
        )
        csv_buffer.close()
