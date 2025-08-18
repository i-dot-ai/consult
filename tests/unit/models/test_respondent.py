import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.django_db
class TestRespondent:
    def test_respondent_creation(self):
        """Test basic respondent creation"""
        respondent = factories.RespondentFactory()
        assert isinstance(respondent, models.Respondent)
        assert respondent.consultation
        assert respondent.themefinder_id

    def test_respondent_identifier_property(self):
        """Test the identifier property"""
        # With themefinder_id
        respondent = factories.RespondentFactory(themefinder_id=12345)
        assert respondent.identifier == 12345

        # Without themefinder_id
        respondent_no_tf = factories.RespondentFactory(themefinder_id=None)
        assert respondent_no_tf.identifier == respondent_no_tf.id

    def test_respondent_demographics(self):
        """Test demographics field"""
        demographics = {"age": "35", "gender": "female", "location": "London"}
        respondent = factories.RespondentFactory(demographics=demographics)
        assert {x.field_name: x.field_value for x in respondent.demographics.all()} == demographics

    def test_respondent_consultation_relationship(self):
        """Test foreign key relationship with Consultation"""
        consultation = factories.ConsultationFactory()
        respondent1 = factories.RespondentFactory(consultation=consultation)
        respondent2 = factories.RespondentFactory(consultation=consultation)

        # Check reverse relationship
        consultation_respondents = consultation.respondent_set.all()
        assert respondent1 in consultation_respondents
        assert respondent2 in consultation_respondents
        assert consultation_respondents.count() == 2
