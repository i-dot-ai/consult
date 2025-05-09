import time

import pytest
from django.db.models.query_utils import Q

from consultation_analyser.consultations.models import (
    Consultation,
    EvidenceRichMapping,
    SentimentMapping,
    ThemeMapping,
)
from consultation_analyser.factories import (
    ConsultationFactory,
    FreeTextAnswerFactory,
    FreeTextQuestionPartFactory,
    QuestionFactory,
    RespondentFactory,
    UserFactory,
)
from tests.helpers import sign_in


@pytest.mark.django_db
def test_managing_consultations_via_support(django_app):
    # given I am an admin user
    user = UserFactory(email="email@example.com", is_staff=True)
    sign_in(django_app, user.email)

    # when I generate a dummy consultation
    consultations_page = django_app.get("/support/consultations/")
    consultations_page = consultations_page.form.submit("generate_dummy_consultation")

    latest_consultation = Consultation.objects.all().order_by("created_at").last()
    consultation_page = consultations_page.click(latest_consultation.title)

    # and I should be able to delete the consultation
    confirmation_page = consultation_page.click("Delete this consultation")
    consultations_page = confirmation_page.form.submit("confirm_deletion").follow()

    assert "The consultation has been deleted" in consultations_page


@pytest.mark.django_db
def test_ingesting_themefinder_outputs(django_app, mock_consultation_input_objects):
    # given I am an admin user
    user = UserFactory(email="email@example.com", is_staff=True)
    sign_in(django_app, user.email)

    # and there is an existing consultation with imported responses
    consultation = ConsultationFactory()
    question_1 = QuestionFactory(consultation=consultation, number=1)
    question_2 = QuestionFactory(consultation=consultation, number=2)
    question_part_1 = FreeTextQuestionPartFactory(question=question_1)
    question_part_2 = FreeTextQuestionPartFactory(question=question_2)

    respondent_1 = RespondentFactory(themefinder_respondent_id=1, consultation=consultation)
    respondent_2 = RespondentFactory(themefinder_respondent_id=2, consultation=consultation)
    respondent_3 = RespondentFactory(themefinder_respondent_id=3, consultation=consultation)
    respondent_4 = RespondentFactory(themefinder_respondent_id=4, consultation=consultation)
    for respondent in [respondent_1, respondent_2, respondent_3, respondent_4]:
        for question_part in [question_part_1, question_part_2]:
            FreeTextAnswerFactory(question_part=question_part, respondent=respondent)

    # when I ingest all themefinder outputs from S3
    import_form = django_app.get("/support/consultations/import-themes/")
    import_form.form["consultation_slug"] = consultation.slug
    import_form.form["consultation_code"] = "con1"
    import_form.form["consultation_mapping_date"] = "2025-04-01/"
    import_form.form["question_choice"] = "all"
    import_form.form.submit()

    # TODO - improve this, but it works for now!
    time.sleep(5)

    # then all expected data is imported
    theme_mappings = ThemeMapping.objects.filter(
        Q(answer__question_part=question_part_1) | Q(answer__question_part=question_part_2)
    )
    assert theme_mappings.count() == 8

    sentiment_mappings = SentimentMapping.objects.filter(
        Q(answer__question_part=question_part_1) | Q(answer__question_part=question_part_2)
    )
    assert sentiment_mappings.count() == 6

    evidence_rich_mappings = EvidenceRichMapping.objects.filter(
        Q(answer__question_part=question_part_1) | Q(answer__question_part=question_part_2)
    )
    assert evidence_rich_mappings.count() == 6

    # and when I delete and reingest only one question data
    question_part_1.delete()
    question_part_2.delete()

    question_part_1 = FreeTextQuestionPartFactory(question=question_1)
    question_part_2 = FreeTextQuestionPartFactory(question=question_2)
    for respondent in [respondent_1, respondent_2, respondent_3, respondent_4]:
        for question_part in [question_part_1, question_part_2]:
            FreeTextAnswerFactory(question_part=question_part, respondent=respondent)

    import_form = django_app.get("/support/consultations/import-themes/")
    import_form.form["consultation_slug"] = consultation.slug
    import_form.form["consultation_code"] = "con1"
    import_form.form["consultation_mapping_date"] = "2025-04-01/"
    import_form.form["question_choice"] = "one"
    import_form.form["question_number"] = "1"
    import_form.form.submit()

    # TODO - improve this, but it works for now!
    time.sleep(5)

    # then only the new data should be added
    theme_mappings = ThemeMapping.objects.filter(
        Q(answer__question_part=question_part_1) | Q(answer__question_part=question_part_2)
    )
    assert theme_mappings.count() == 4

    sentiment_mappings = SentimentMapping.objects.filter(
        Q(answer__question_part=question_part_1) | Q(answer__question_part=question_part_2)
    )
    assert sentiment_mappings.count() == 3

    evidence_rich_mappings = EvidenceRichMapping.objects.filter(
        Q(answer__question_part=question_part_1) | Q(answer__question_part=question_part_2)
    )
    assert evidence_rich_mappings.count() == 3
