import uuid
from uuid import uuid4

from consultation_analyser.consultations.api.serializers import (
    ConsultationExportSerializer,
    ConsultationFolderSerializer,
    ConsultationImportSerializer,
    DemographicAggregationsSerializer,
    QuestionSerializer,
    RespondentSerializer,
    ResponseThemeInformationSerializer,
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


class TestConsultationImportSerializer:
    def test_valid_data(self):
        """Test import consultation information serializer with valid data"""
        data = {
            "consultation_name": "test",
            "timestamp": "08-09-2025",
            "action": "sign_off",
            "consultation_code": "demo_consultation",
        }
        serializer = ConsultationImportSerializer(data=data)
        assert serializer.is_valid()
        expected = {
            "consultation_name": "test",
            "timestamp": "08-09-2025",
            "action": "sign_off",
            "consultation_code": "demo_consultation",
        }

        assert serializer.validated_data == expected
        assert serializer.get_sign_off()

        data = {
            "consultation_name": "test",
            "timestamp": "08-09-2025",
            "action": "dashboard",
            "consultation_code": "demo_consultation",
        }
        serializer = ConsultationImportSerializer(data=data)
        assert serializer.is_valid()
        expected = {
            "consultation_name": "test",
            "timestamp": "08-09-2025",
            "action": "dashboard",
            "consultation_code": "demo_consultation",
        }
        assert serializer.validated_data == expected
        assert not serializer.get_sign_off()

    def test_missing_fields(self):
        """Test consultation import information serializer with missing fields"""
        data = {
            "consultation_name": "test",
            "action": "dashboard",
            "consultation_code": "demo_consultation",
        }
        serializer = ConsultationImportSerializer(data=data)
        assert not serializer.is_valid()
        assert "timestamp" in serializer.errors

    def test_invalid_fields(self):
        """Test consultation import information serializer with invalid code"""
        data = {
            "consultation_name": "test",
            "timestamp": "08-09-2025",
            "action": "sign_off",
            "consultation_code": False,
        }
        serializer = ConsultationImportSerializer(data=data)
        assert not serializer.is_valid()
        assert "consultation_code" in serializer.errors


class TestConsultationFoldersSerializer:
    def test_valid_data(self):
        """Test consultation folders information serializer with valid data"""
        data = [
            {"value": "test consultation 2", "text": "test consultation 2"},
            {"value": "test consultation 3", "text": "test consultation 3"},
            {"value": "test consultation", "text": "test consultation"},
        ]
        serializer = ConsultationFolderSerializer(data=data, many=True)
        assert serializer.is_valid()
        expected = [
            {"value": "test consultation 2", "text": "test consultation 2"},
            {"value": "test consultation 3", "text": "test consultation 3"},
            {"value": "test consultation", "text": "test consultation"},
        ]

        assert serializer.validated_data == expected

    def test_missing_fields(self):
        """Test consultation folders information serializer with missing fields"""
        data = [
            {
                "value": "test consultation 2",
            },
            {"value": "test consultation 3", "text": "test consultation 3"},
            {"value": "test consultation", "text": "test consultation"},
        ]
        serializer = ConsultationFolderSerializer(data=data, many=True)
        assert not serializer.is_valid()
        assert any("text" in error_dict for error_dict in serializer.errors)

    def test_invalid_fields(self):
        """Test consultation folder information serializer with invalid value"""
        data = [
            {"value": False, "text": "test consultation 2"},
            {"value": "test consultation 3", "text": "test consultation 3"},
            {"value": "test consultation", "text": "test consultation"},
        ]
        serializer = ConsultationFolderSerializer(data=data, many=True)
        assert not serializer.is_valid()
        assert any("value" in error_dict for error_dict in serializer.errors)


class TestConsultationExportSerializer:
    def test_valid_data(self):
        """Test export consultation information serializer with valid data"""
        question_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        data = {
            "s3_key": "test",
            "question_ids": question_ids,
        }
        serializer = ConsultationExportSerializer(data=data)
        assert serializer.is_valid()
        expected = {
            "s3_key": "test",
            "question_ids": question_ids,
        }

        assert serializer.validated_data == expected

        data = {
            "s3_key": None,
            "question_ids": question_ids,
        }
        serializer = ConsultationExportSerializer(data=data)
        assert serializer.is_valid()
        expected = {
            "s3_key": None,
            "question_ids": question_ids,
        }
        assert serializer.validated_data == expected

    def test_missing_fields(self):
        """Test consultation export information serializer with missing fields"""
        data = {
            "s3_key": None,
        }
        serializer = ConsultationExportSerializer(data=data)
        assert not serializer.is_valid()
        assert "question_ids" in serializer.errors

    def test_invalid_fields(self):
        """Test consultation export information serializer with invalid code"""
        data = {
            "s3_key": None,
            "question_ids": "test bad field",
        }
        serializer = ConsultationExportSerializer(data=data)
        assert not serializer.is_valid()
        assert "question_ids" in serializer.errors


class TestRespondentSerializer:
    def test_valid_data_with_name(self):
        """Test respondent serializer with valid data including name"""
        data = {
            "name": "John Doe",
        }
        serializer = RespondentSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_valid_data_minimal(self):
        """Test respondent serializer with minimal valid data"""
        data = {}
        serializer = RespondentSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_valid_data_with_null_name(self):
        """Test respondent serializer with null name"""
        data = {"name": None}
        serializer = RespondentSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_read_only_fields_ignored(self):
        """Test that read-only fields are ignored in validation"""
        data = {
            "id": uuid4(),  # read-only, should be ignored
            "themefinder_id": 12345,  # read-only, should be ignored
            "name": "John Doe",
            "demographics": [  # read-only, should be ignored
                {"id": "age_group", "field_name": "age_group", "field_value": "25-34"},
            ],
        }
        serializer = RespondentSerializer(data=data)
        assert serializer.is_valid()
        # Only writable fields should be in validated_data
        assert serializer.validated_data == {"name": "John Doe"}


class TestResponseThemeInformationSerializer:
    def test_valid_data(self):
        """Test response theme information serializer with valid data"""
        data = {
            "selected_themes": [
                {"id": uuid4(), "name": "Theme A", "description": "Description A", "key": "theme_a"}
            ],
            "all_themes": [
                {
                    "id": uuid4(),
                    "name": "Theme A",
                    "description": "Description A",
                    "key": "theme_a",
                },
                {
                    "id": uuid4(),
                    "name": "Theme B",
                    "description": "Description B",
                    "key": "theme_b",
                },
            ],
        }
        serializer = ResponseThemeInformationSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_empty_themes(self):
        """Test response theme information serializer with empty themes"""
        data = {"selected_themes": [], "all_themes": []}
        serializer = ResponseThemeInformationSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_no_selected_themes(self):
        """Test response theme information serializer with no selected themes"""
        data = {
            "selected_themes": [],
            "all_themes": [
                {
                    "id": uuid4(),
                    "name": "Theme A",
                    "description": "Description A",
                    "key": "theme_a",
                },
                {
                    "id": uuid4(),
                    "name": "Theme B",
                    "description": "Description B",
                    "key": "theme_b",
                },
            ],
        }
        serializer = ResponseThemeInformationSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_invalid_theme_structure(self):
        """Test response theme information serializer with invalid theme structure"""
        data = {
            "selected_themes": [
                {"id": "invalid-uuid", "name": "Theme A"}  # Missing description and invalid ID
            ],
            "all_themes": [
                {"name": "Theme B"}  # Missing ID and description
            ],
        }
        serializer = ResponseThemeInformationSerializer(data=data)
        assert not serializer.is_valid()

    def test_missing_required_fields(self):
        """Test response theme information serializer with missing required fields"""
        data = {
            "selected_themes": []
            # Missing all_themes
        }
        serializer = ResponseThemeInformationSerializer(data=data)
        assert not serializer.is_valid()
        assert "all_themes" in serializer.errors

    def test_invalid_field_types(self):
        """Test response theme information serializer with invalid field types"""
        data = {
            "selected_themes": "not a list",
            "all_themes": [{"id": uuid4(), "name": "Theme A", "description": "Description A"}],
        }
        serializer = ResponseThemeInformationSerializer(data=data)
        assert not serializer.is_valid()
        assert "selected_themes" in serializer.errors
