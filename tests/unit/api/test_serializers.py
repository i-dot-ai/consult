from uuid import uuid4

from consultation_analyser.consultations.api.serializers import (
    DemographicAggregationsSerializer,
    QuestionSerializer,
    ThemeAggregationsSerializer,
    ThemeInformationSerializer,
    ThemeSerializer,
)


class TestDemographicAggregationsSerializer:
    def test_valid_data(self):
        """Test serializer with valid demographic aggregations data"""
        data = {
            "demographic_aggregations": {
                "gender": {"male": 10, "female": 15},
                "age_group": {"18-25": 12, "26-35": 13},
            }
        }
        serializer = DemographicAggregationsSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_empty_data(self):
        """Test serializer with empty aggregations"""
        data = {"demographic_aggregations": {}}
        serializer = DemographicAggregationsSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_invalid_counts(self):
        """Test serializer with invalid count values"""
        data = {"demographic_aggregations": {"gender": {"male": "invalid", "female": 15}}}
        serializer = DemographicAggregationsSerializer(data=data)
        assert not serializer.is_valid()


class TestThemeSerializer:
    def test_valid_data(self):
        """Test theme serializer with valid data"""
        data = {"id": uuid4(), "name": "Test Theme", "description": "A test theme description"}
        serializer = ThemeSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_missing_required_fields(self):
        """Test theme serializer with missing required fields"""
        data = {"key": 1}
        serializer = ThemeSerializer(data=data)
        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_invalid_id_type(self):
        """Test theme serializer with invalid ID type"""
        data = {"id": "invalid", "name": "Test Theme", "description": "A test theme description"}
        serializer = ThemeSerializer(data=data)
        assert not serializer.is_valid()
        assert "id" in serializer.errors


class TestThemeInformationSerializer:
    def test_valid_data(self):
        """Test theme information serializer with valid data"""
        data = {
            "themes": [
                {"id": uuid4(), "name": "Theme A", "description": "Description A"},
                {"id": uuid4(), "name": "Theme B", "description": "Description B"},
            ]
        }
        serializer = ThemeInformationSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_empty_themes(self):
        """Test theme information serializer with empty themes list"""
        data = {"themes": []}
        serializer = ThemeInformationSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_invalid_theme_data(self):
        """Test theme information serializer with invalid theme data"""
        data = {
            "themes": [
                {"id": 1, "name": "Theme A"},  # Missing description
                {"id": "invalid", "name": "Theme B", "description": "Description B"},  # Invalid ID
            ]
        }
        serializer = ThemeInformationSerializer(data=data)
        assert not serializer.is_valid()


class TestThemeAggregationsSerializer:
    def test_valid_data(self):
        """Test theme aggregations serializer with valid data"""
        data = {"theme_aggregations": {"1": 10, "2": 5, "3": 20}}
        serializer = ThemeAggregationsSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_empty_aggregations(self):
        """Test theme aggregations serializer with empty data"""
        data = {"theme_aggregations": {}}
        serializer = ThemeAggregationsSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_invalid_count_values(self):
        """Test theme aggregations serializer with invalid count values"""
        data = {"theme_aggregations": {"1": "invalid", "2": 5}}
        serializer = ThemeAggregationsSerializer(data=data)
        assert not serializer.is_valid()


class TestQuestionSerializer:
    def test_valid_data(self):
        """Test question information serializer with valid data"""
        data = {
            "question_text": "What do you think about this topic?",
            "total_responses": 150,
            "number": 1,
        }
        serializer = QuestionSerializer(data=data)
        assert serializer.is_valid()
        expected = {
            "text": "What do you think about this topic?",
            "number": 1,
        }

        assert serializer.validated_data == expected

    def test_missing_fields(self):
        """Test question information serializer with missing fields"""
        data = {
            "question_text": "What do you think about this topic?",
            "total_responses": 150,
        }
        serializer = QuestionSerializer(data=data)
        assert not serializer.is_valid()
        assert "number" in serializer.errors

    def test_invalid_response_count(self):
        """Test question information serializer with invalid response count"""
        data = {
            "question_text": "What do you think about this topic?",
            "total_responses": "invalid",
        }
        serializer = QuestionSerializer(data=data)
        assert not serializer.is_valid()
        assert "number" in serializer.errors
