from uuid import uuid4

from consultation_analyser.consultations.api.serializers import (
    DemographicAggregationsSerializer,
    DemographicOptionsSerializer,
    FilterSerializer,
    QuestionSerializer,
    ThemeAggregationsSerializer,
    ThemeInformationSerializer,
    ThemeSerializer,
)


class TestDemographicOptionsSerializer:
    def test_valid_data(self):
        """Test serializer with valid demographic options data"""
        data = {
            "demographic_options": {
                "gender": ["male", "female"],
                "age_group": ["18-25", "26-35"],
                "region": ["north", "south"],
            }
        }
        serializer = DemographicOptionsSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_empty_data(self):
        """Test serializer with empty demographic options"""
        data = {"demographic_options": {}}
        serializer = DemographicOptionsSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def test_invalid_structure(self):
        """Test serializer with invalid data structure"""
        data = {"demographic_options": "invalid"}
        serializer = DemographicOptionsSerializer(data=data)
        assert not serializer.is_valid()


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
        assert serializer.validated_data == {
            "description": "A test theme description",
            "name": "Test Theme",
        }

    def test_missing_required_fields(self):
        """Test theme serializer with missing required fields"""
        data = {"id": 1}
        serializer = ThemeSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors
        assert "description" in serializer.errors

    def test_invalid_id_type(self):
        """Test theme serializer with invalid ID type"""
        data = {"id": "invalid", "key": "Test Theme", "description": "A test theme description"}
        serializer = ThemeSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors


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
        expected = {
            "themes": [
                {"name": "Theme A", "description": "Description A"},
                {"name": "Theme B", "description": "Description B"},
            ]
        }
        assert serializer.validated_data == expected

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
            "slug": "topic",
        }
        serializer = QuestionSerializer(data=data)
        assert serializer.is_valid()
        expected = {
            "text": "What do you think about this topic?",
            "number": 1,
            "slug": "topic",
        }

        assert serializer.validated_data == expected

    def test_missing_fields(self):
        """Test question information serializer with missing fields"""
        data = {
            "question_text": "What do you think about this topic?",
            "total_responses": 150,
            "slug": "topic",
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


class TestFilterSerializer:
    def test_empty_filters(self):
        """Test filter serializer with no filters"""
        data = {}
        serializer = FilterSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {"page": 1, "page_size": 50}  # defaults

    def test_all_valid_filters(self):
        """Test filter serializer with all valid filter types"""
        data = {
            "sentimentFilters": "AGREEMENT,DISAGREEMENT",
            "themeFilters": "1,2,3",
            "themesSortDirection": "ascending",
            "themesSortType": "frequency",
            "evidenceRich": True,
            "searchValue": "test search",
            "searchMode": "semantic",
            "demoFilters": ["individual:true", "region:north"],
            "page": 2,
            "page_size": 25,
        }
        serializer = FilterSerializer(data=data)
        assert serializer.is_valid()

        validated = serializer.validated_data
        assert validated["sentimentFilters"] == "AGREEMENT,DISAGREEMENT"
        assert validated["themeFilters"] == "1,2,3"
        assert validated["evidenceRich"] is True
        assert validated["searchValue"] == "test search"
        assert validated["searchMode"] == "semantic"
        assert validated["demoFilters"] == ["individual:true", "region:north"]
        assert validated["page"] == 2
        assert validated["page_size"] == 25

    def test_invalid_search_mode(self):
        """Test filter serializer with invalid search mode"""
        data = {"searchMode": "invalid"}
        serializer = FilterSerializer(data=data)
        assert not serializer.is_valid()
        assert "searchMode" in serializer.errors

    def test_invalid_pagination_parameters(self):
        """Test filter serializer with invalid pagination parameters"""
        # Test page too small
        data = {"page": 0}
        serializer = FilterSerializer(data=data)
        assert not serializer.is_valid()
        assert "page" in serializer.errors

        # Test page_size too small
        data = {"page_size": 0}
        serializer = FilterSerializer(data=data)
        assert not serializer.is_valid()
        assert "page_size" in serializer.errors

        # Test page_size too large
        data = {"page_size": 200}
        serializer = FilterSerializer(data=data)
        assert not serializer.is_valid()
        assert "page_size" in serializer.errors

    def test_boolean_evidence_rich_conversion(self):
        """Test that evidenceRich is properly converted to boolean"""
        # Test string 'true'
        data = {"evidenceRich": "true"}
        serializer = FilterSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["evidenceRich"] is True

        # Test string 'false'
        data = {"evidenceRich": "false"}
        serializer = FilterSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["evidenceRich"] is False

        # Test boolean True
        data = {"evidenceRich": True}
        serializer = FilterSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["evidenceRich"] is True

    def test_demo_filters_list_validation(self):
        """Test that demoFilters accepts list of strings"""
        data = {"demoFilters": ["key1:value1", "key2:value2", "key3:value3"]}
        serializer = FilterSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["demoFilters"] == [
            "key1:value1",
            "key2:value2",
            "key3:value3",
        ]

        # Test invalid - not a list
        data = {"demoFilters": "key1:value1"}
        serializer = FilterSerializer(data=data)
        assert not serializer.is_valid()
        assert "demoFilters" in serializer.errors

    def test_optional_fields_not_required(self):
        """Test that all filter fields are optional"""
        data = {"page": 1}  # Only provide one optional field
        serializer = FilterSerializer(data=data)
        assert serializer.is_valid()

    def test_blank_string_handling(self):
        """Test that blank strings are allowed for string fields that allow them"""
        data = {"sentimentFilters": "", "themeFilters": ""}
        serializer = FilterSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["sentimentFilters"] == ""
        assert serializer.validated_data["themeFilters"] == ""
