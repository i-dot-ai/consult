"""
Tests for response annotations ingestion workflow.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    SelectedTheme,
)
from consultation_analyser.support_console.ingestion.ingest_response_annotations import (
    _ingest_response_annotations,
    _ingest_selected_themes,
    import_response_annotations_from_s3,
    ingest_response_annotations,
    load_annotation_batch,
    load_detail_detections_from_s3,
    load_selected_themes_from_s3,
    load_sentiments_from_s3,
    load_theme_mappings_from_s3,
)
from consultation_analyser.support_console.ingestion.pydantic_models import (
    AnnotationBatch,
    DetailDetectionInput,
    SelectedThemeInput,
    SentimentInput,
    ThemeMappingInput,
)


@pytest.fixture
def consultation(db):
    """Create a test consultation"""
    return Consultation.objects.create(
        code="TEST", title="Test Consultation", timestamp="2024-01-01"
    )


@pytest.fixture
def question_1(db, consultation):
    """Create test question 1"""
    return Question.objects.create(
        consultation=consultation, text="What do you think?", number=1, has_free_text=True
    )


@pytest.fixture
def question_2(db, consultation):
    """Create test question 2"""
    return Question.objects.create(
        consultation=consultation, text="Any other comments?", number=2, has_free_text=True
    )


@pytest.fixture
def respondent_1(db, consultation):
    """Create test respondent 1"""
    return Respondent.objects.create(consultation=consultation, themefinder_id=1001)


@pytest.fixture
def respondent_2(db, consultation):
    """Create test respondent 2"""
    return Respondent.objects.create(consultation=consultation, themefinder_id=1002)


@pytest.fixture
def response_1(db, question_1, respondent_1):
    """Create test response 1 for question 1"""
    return Response.objects.create(
        question=question_1, respondent=respondent_1, free_text="I think healthcare is important"
    )


@pytest.fixture
def response_2(db, question_1, respondent_2):
    """Create test response 2 for question 1"""
    return Response.objects.create(
        question=question_1, respondent=respondent_2, free_text="Education needs more funding"
    )


@pytest.fixture
def sample_themes_data():
    """Sample S3 selected themes data"""
    return [
        {
            "theme_key": "healthcare",
            "theme_name": "Healthcare Access",
            "theme_description": "Issues related to accessing healthcare services",
        },
        {
            "theme_key": "education",
            "theme_name": "Education Funding",
            "theme_description": "Concerns about education funding levels",
        },
    ]


@pytest.fixture
def sample_sentiments_data():
    """Sample S3 sentiment data"""
    return [
        {"themefinder_id": 1001, "sentiment": "AGREEMENT"},
        {"themefinder_id": 1002, "sentiment": "DISAGREEMENT"},
    ]


@pytest.fixture
def sample_details_data():
    """Sample S3 detail detection data"""
    return [
        {"themefinder_id": 1001, "evidence_rich": "YES"},
        {"themefinder_id": 1002, "evidence_rich": "NO"},
    ]


@pytest.fixture
def sample_mappings_data():
    """Sample S3 theme mapping data"""
    return [
        {"themefinder_id": 1001, "theme_keys": ["healthcare"]},
        {"themefinder_id": 1002, "theme_keys": ["education", "healthcare"]},
    ]


@pytest.fixture
def mock_s3_client_themes(sample_themes_data):
    """Mock S3 client that returns sample themes"""
    client = MagicMock()
    client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=json.dumps(sample_themes_data).encode()))
    }
    return client


@pytest.fixture
def mock_s3_client_jsonl():
    """Mock S3 client that returns JSONL data"""

    def create_client(data):
        client = MagicMock()
        jsonl_content = "\n".join(json.dumps(item) for item in data)
        # Mock Body with iter_lines() method (read_jsonl_from_s3 uses iter_lines)
        mock_body = MagicMock()
        mock_body.iter_lines.return_value = jsonl_content.encode().splitlines()
        client.get_object.return_value = {"Body": mock_body}
        return client

    return create_client


class TestLoadSelectedThemesFromS3:
    """Tests for load_selected_themes_from_s3 function"""

    def test_load_themes_success(self, mock_s3_client_themes, sample_themes_data):
        """Test successfully loading and validating selected themes from S3"""
        themes = load_selected_themes_from_s3(
            consultation_code="TEST",
            question_number=1,
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=mock_s3_client_themes,
        )

        # Verify correct S3 key was requested
        expected_key = (
            "app_data/consultations/TEST/outputs/mapping/2024-01-15/question_part_1/themes.json"
        )
        mock_s3_client_themes.get_object.assert_called_once_with(
            Bucket="test-bucket", Key=expected_key
        )

        # Verify themes loaded and validated
        assert len(themes) == 2
        assert all(isinstance(theme, SelectedThemeInput) for theme in themes)

        # Verify first theme
        assert themes[0].theme_key == "healthcare"
        assert themes[0].theme_name == "Healthcare Access"
        assert themes[0].theme_description == "Issues related to accessing healthcare services"

    def test_load_themes_invalid_data(self):
        """Test validation error when S3 data is malformed"""
        client = MagicMock()
        invalid_data = [{"theme_key": "test"}]  # Missing required fields
        client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=json.dumps(invalid_data).encode()))
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            load_selected_themes_from_s3(
                consultation_code="TEST",
                question_number=1,
                timestamp="2024-01-15",
                bucket_name="test-bucket",
                s3_client=client,
            )


class TestLoadSentimentsFromS3:
    """Tests for load_sentiments_from_s3 function"""

    def test_load_sentiments_success(self, mock_s3_client_jsonl, sample_sentiments_data):
        """Test successfully loading sentiments from S3"""
        client = mock_s3_client_jsonl(sample_sentiments_data)

        sentiments = load_sentiments_from_s3(
            consultation_code="TEST",
            question_number=1,
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Verify sentiments loaded and validated
        assert len(sentiments) == 2
        assert all(isinstance(s, SentimentInput) for s in sentiments)

        assert sentiments[0].themefinder_id == 1001
        assert sentiments[0].sentiment == "AGREEMENT"
        assert sentiments[1].themefinder_id == 1002
        assert sentiments[1].sentiment == "DISAGREEMENT"

    def test_load_sentiments_file_not_found(self):
        """Test handling when sentiment file doesn't exist (optional file)"""
        client = MagicMock()
        client.get_object.side_effect = ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

        sentiments = load_sentiments_from_s3(
            consultation_code="TEST",
            question_number=1,
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Should return empty list when file not found (not an error)
        assert sentiments == []

    def test_load_sentiments_invalid_data(self):
        """Test validation error when sentiment data is malformed"""
        client = MagicMock()
        invalid_data = [{"themefinder_id": 1001}]  # Missing sentiment field
        jsonl_content = "\n".join(json.dumps(item) for item in invalid_data)
        # Mock Body with iter_lines() method
        mock_body = MagicMock()
        mock_body.iter_lines.return_value = jsonl_content.encode().splitlines()
        client.get_object.return_value = {"Body": mock_body}

        # Should not raise - has default value
        sentiments = load_sentiments_from_s3(
            consultation_code="TEST",
            question_number=1,
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Should use default value "UNCLEAR"
        assert sentiments[0].sentiment == "UNCLEAR"


class TestLoadDetailDetectionsFromS3:
    """Tests for load_detail_detections_from_s3 function"""

    def test_load_details_success(self, mock_s3_client_jsonl, sample_details_data):
        """Test successfully loading detail detections from S3"""
        client = mock_s3_client_jsonl(sample_details_data)

        details = load_detail_detections_from_s3(
            consultation_code="TEST",
            question_number=1,
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Verify details loaded and validated
        assert len(details) == 2
        assert all(isinstance(d, DetailDetectionInput) for d in details)

        assert details[0].themefinder_id == 1001
        assert details[0].evidence_rich == "YES"
        assert details[0].as_bool is True

        assert details[1].themefinder_id == 1002
        assert details[1].evidence_rich == "NO"
        assert details[1].as_bool is False


class TestLoadThemeMappingsFromS3:
    """Tests for load_theme_mappings_from_s3 function"""

    def test_load_mappings_success(self, mock_s3_client_jsonl, sample_mappings_data):
        """Test successfully loading theme mappings from S3"""
        client = mock_s3_client_jsonl(sample_mappings_data)

        mappings = load_theme_mappings_from_s3(
            consultation_code="TEST",
            question_number=1,
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Verify mappings loaded and validated
        assert len(mappings) == 2
        assert all(isinstance(m, ThemeMappingInput) for m in mappings)

        assert mappings[0].themefinder_id == 1001
        assert mappings[0].theme_keys == ["healthcare"]

        assert mappings[1].themefinder_id == 1002
        assert mappings[1].theme_keys == ["education", "healthcare"]


class TestLoadAnnotationBatch:
    """Tests for load_annotation_batch function"""

    def test_load_batch_for_multiple_questions(
        self,
        db,
        consultation,
        question_1,
        question_2,
        response_1,  # Need responses for questions to be included
        respondent_2,
        sample_themes_data,
        sample_sentiments_data,
        sample_details_data,
        sample_mappings_data,
    ):
        """Test loading annotations for multiple questions"""
        # Create a response for question_2 so it's included
        Response.objects.create(
            question=question_2, respondent=respondent_2, free_text="Response for Q2"
        )

        def mock_get_object(Bucket, Key):  # noqa: N803
            """Mock S3 get_object with different responses for different keys"""
            if "themes.json" in Key:
                return {
                    "Body": MagicMock(
                        read=MagicMock(return_value=json.dumps(sample_themes_data).encode())
                    )
                }
            elif "sentiment.jsonl" in Key:
                jsonl = "\n".join(json.dumps(item) for item in sample_sentiments_data)
                mock_body = MagicMock()
                mock_body.iter_lines.return_value = jsonl.encode().splitlines()
                return {"Body": mock_body}
            elif "detail_detection.jsonl" in Key:
                jsonl = "\n".join(json.dumps(item) for item in sample_details_data)
                mock_body = MagicMock()
                mock_body.iter_lines.return_value = jsonl.encode().splitlines()
                return {"Body": mock_body}
            elif "mapping.jsonl" in Key:
                jsonl = "\n".join(json.dumps(item) for item in sample_mappings_data)
                mock_body = MagicMock()
                mock_body.iter_lines.return_value = jsonl.encode().splitlines()
                return {"Body": mock_body}

        client = MagicMock()
        client.get_object = mock_get_object

        batch = load_annotation_batch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Verify batch created
        assert isinstance(batch, AnnotationBatch)
        assert batch.consultation_code == "TEST"
        assert batch.timestamp == "2024-01-15"

        # Should have loaded data for both questions
        assert 1 in batch.selected_themes_by_question
        assert 2 in batch.selected_themes_by_question
        assert len(batch.selected_themes_by_question[1]) == 2
        assert len(batch.selected_themes_by_question[2]) == 2

    def test_load_batch_specific_questions(
        self,
        db,
        consultation,
        question_1,
        question_2,
        sample_themes_data,
        sample_sentiments_data,
        sample_details_data,
        sample_mappings_data,
    ):
        """Test loading annotations for specific question numbers only"""

        def mock_get_object(Bucket, Key):  # noqa: N803
            if "themes.json" in Key:
                return {
                    "Body": MagicMock(
                        read=MagicMock(return_value=json.dumps(sample_themes_data).encode())
                    )
                }
            elif "sentiment.jsonl" in Key:
                jsonl = "\n".join(json.dumps(item) for item in sample_sentiments_data)
                mock_body = MagicMock()
                mock_body.iter_lines.return_value = jsonl.encode().splitlines()
                return {"Body": mock_body}
            elif "detail_detection.jsonl" in Key:
                jsonl = "\n".join(json.dumps(item) for item in sample_details_data)
                mock_body = MagicMock()
                mock_body.iter_lines.return_value = jsonl.encode().splitlines()
                return {"Body": mock_body}
            elif "mapping.jsonl" in Key:
                jsonl = "\n".join(json.dumps(item) for item in sample_mappings_data)
                mock_body = MagicMock()
                mock_body.iter_lines.return_value = jsonl.encode().splitlines()
                return {"Body": mock_body}

        client = MagicMock()
        client.get_object = mock_get_object

        batch = load_annotation_batch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            question_numbers=[1],  # Only question 1
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Should only have question 1
        assert 1 in batch.selected_themes_by_question
        assert 2 not in batch.selected_themes_by_question

    def test_load_batch_consultation_not_found(self, db):
        """Test error when consultation doesn't exist"""
        with pytest.raises(ValueError, match="Consultation with code 'MISSING' does not exist"):
            load_annotation_batch(
                consultation_code="MISSING",
                timestamp="2024-01-15",
            )

    def test_load_batch_without_sentiment_file(
        self,
        db,
        consultation,
        question_1,
        response_1,  # Need response for question to be included
        sample_themes_data,
        sample_details_data,
        sample_mappings_data,
    ):
        """Test loading batch when sentiment file is missing (optional)"""

        def mock_get_object(Bucket, Key):  # noqa: N803
            if "sentiment.jsonl" in Key:
                # Simulate file not found for sentiment
                raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
            elif "themes.json" in Key:
                return {
                    "Body": MagicMock(
                        read=MagicMock(return_value=json.dumps(sample_themes_data).encode())
                    )
                }
            elif "detail_detection.jsonl" in Key:
                jsonl = "\n".join(json.dumps(item) for item in sample_details_data)
                mock_body = MagicMock()
                mock_body.iter_lines.return_value = jsonl.encode().splitlines()
                return {"Body": mock_body}
            elif "mapping.jsonl" in Key:
                jsonl = "\n".join(json.dumps(item) for item in sample_mappings_data)
                mock_body = MagicMock()
                mock_body.iter_lines.return_value = jsonl.encode().splitlines()
                return {"Body": mock_body}

        client = MagicMock()
        client.get_object = mock_get_object

        batch = load_annotation_batch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Batch should be created but without sentiments for question 1
        assert 1 not in batch.sentiments_by_question or batch.sentiments_by_question[1] == []
        # Other data should still be present
        assert 1 in batch.selected_themes_by_question
        assert 1 in batch.details_by_question
        assert 1 in batch.mappings_by_question


class TestIngestSelectedThemes:
    """Tests for _ingest_selected_themes function"""

    def test_ingest_themes_basic(self, db, question_1):
        """Test ingesting selected themes for a question"""
        themes = [
            SelectedThemeInput(
                theme_key="healthcare",
                theme_name="Healthcare Access",
                theme_description="Issues related to accessing healthcare services",
            ),
            SelectedThemeInput(
                theme_key="education",
                theme_name="Education Funding",
                theme_description="Concerns about education funding levels",
            ),
        ]

        theme_lookup = _ingest_selected_themes(question_1, themes)

        # Verify themes created
        assert SelectedTheme.objects.filter(question=question_1).count() == 2

        # Verify theme lookup returned
        assert len(theme_lookup) == 2
        assert "healthcare" in theme_lookup
        assert "education" in theme_lookup

        # Verify theme details
        healthcare_theme = SelectedTheme.objects.get(question=question_1, key="healthcare")
        assert healthcare_theme.name == "Healthcare Access"
        assert healthcare_theme.description == "Issues related to accessing healthcare services"

    def test_ingest_themes_idempotent(self, db, question_1):
        """Test that re-running ingestion deletes old themes"""
        # First ingestion
        themes_v1 = [
            SelectedThemeInput(
                theme_key="old_theme",
                theme_name="Old Theme",
                theme_description="Old description",
            )
        ]
        _ingest_selected_themes(question_1, themes_v1)
        assert SelectedTheme.objects.filter(question=question_1).count() == 1

        # Second ingestion with different themes
        themes_v2 = [
            SelectedThemeInput(
                theme_key="new_theme",
                theme_name="New Theme",
                theme_description="New description",
            ),
            SelectedThemeInput(
                theme_key="another_theme",
                theme_name="Another Theme",
                theme_description="Another description",
            ),
        ]
        _ingest_selected_themes(question_1, themes_v2)

        # Should have new themes, not old ones
        assert SelectedTheme.objects.filter(question=question_1).count() == 2
        assert not SelectedTheme.objects.filter(question=question_1, key="old_theme").exists()
        assert SelectedTheme.objects.filter(question=question_1, key="new_theme").exists()

    def test_ingest_themes_empty_list(self, db, question_1):
        """Test ingesting empty themes list"""
        theme_lookup = _ingest_selected_themes(question_1, [])

        # Should not create any themes
        assert SelectedTheme.objects.filter(question=question_1).count() == 0
        assert theme_lookup == {}


class TestIngestResponseAnnotations:
    """Tests for _ingest_response_annotations function"""

    def test_ingest_annotations_basic(self, db, question_1, response_1, response_2):
        """Test ingesting response annotations"""
        # Create selected themes first
        themes = [
            SelectedThemeInput(
                theme_key="healthcare",
                theme_name="Healthcare Access",
                theme_description="Healthcare theme",
            )
        ]
        theme_lookup = _ingest_selected_themes(question_1, themes)

        # Create annotation data
        sentiments = [
            SentimentInput(themefinder_id=1001, sentiment="AGREEMENT"),
            SentimentInput(themefinder_id=1002, sentiment="DISAGREEMENT"),
        ]
        details = [
            DetailDetectionInput(themefinder_id=1001, evidence_rich="YES"),
            DetailDetectionInput(themefinder_id=1002, evidence_rich="NO"),
        ]
        mappings = [
            ThemeMappingInput(themefinder_id=1001, theme_keys=["healthcare"]),
            ThemeMappingInput(themefinder_id=1002, theme_keys=["healthcare"]),
        ]

        _ingest_response_annotations(question_1, sentiments, details, mappings, theme_lookup)

        # Verify annotations created
        assert ResponseAnnotation.objects.filter(response__question=question_1).count() == 2

        # Verify annotation for response 1
        ann1 = ResponseAnnotation.objects.get(response=response_1)
        assert ann1.sentiment == "AGREEMENT"
        assert ann1.evidence_rich is True
        assert ann1.human_reviewed is False
        assert ann1.themes.count() == 1
        assert ann1.themes.first().key == "healthcare"

        # Verify annotation for response 2
        ann2 = ResponseAnnotation.objects.get(response=response_2)
        assert ann2.sentiment == "DISAGREEMENT"
        assert ann2.evidence_rich is False
        assert ann2.themes.count() == 1

    def test_ingest_annotations_without_sentiment(self, db, question_1, response_1):
        """Test ingesting annotations when sentiment data is missing"""
        themes = [
            SelectedThemeInput(
                theme_key="healthcare", theme_name="Healthcare", theme_description="Healthcare"
            )
        ]
        theme_lookup = _ingest_selected_themes(question_1, themes)

        # No sentiments provided
        sentiments = []
        details = [DetailDetectionInput(themefinder_id=1001, evidence_rich="YES")]
        mappings = [ThemeMappingInput(themefinder_id=1001, theme_keys=["healthcare"])]

        _ingest_response_annotations(question_1, sentiments, details, mappings, theme_lookup)

        # Annotation should still be created with default sentiment
        ann = ResponseAnnotation.objects.get(response=response_1)
        assert ann.sentiment == "UNCLEAR"  # Default value
        assert ann.evidence_rich is True

    def test_ingest_annotations_multiple_themes(self, db, question_1, response_1):
        """Test linking annotation to multiple themes"""
        themes = [
            SelectedThemeInput(
                theme_key="healthcare", theme_name="Healthcare", theme_description="Healthcare"
            ),
            SelectedThemeInput(
                theme_key="education", theme_name="Education", theme_description="Education"
            ),
        ]
        theme_lookup = _ingest_selected_themes(question_1, themes)

        sentiments = []
        details = [DetailDetectionInput(themefinder_id=1001, evidence_rich="YES")]
        mappings = [ThemeMappingInput(themefinder_id=1001, theme_keys=["healthcare", "education"])]

        _ingest_response_annotations(question_1, sentiments, details, mappings, theme_lookup)

        # Verify annotation linked to both themes
        ann = ResponseAnnotation.objects.get(response=response_1)
        assert ann.themes.count() == 2
        theme_keys = [t.key for t in ann.themes.all()]
        assert "healthcare" in theme_keys
        assert "education" in theme_keys

    def test_ingest_annotations_idempotent(self, db, question_1, response_1):
        """Test that re-running ingestion deletes old annotations"""
        themes = [
            SelectedThemeInput(
                theme_key="healthcare", theme_name="Healthcare", theme_description="Healthcare"
            )
        ]
        theme_lookup = _ingest_selected_themes(question_1, themes)

        # First ingestion
        details_v1 = [DetailDetectionInput(themefinder_id=1001, evidence_rich="YES")]
        mappings_v1 = [ThemeMappingInput(themefinder_id=1001, theme_keys=["healthcare"])]
        _ingest_response_annotations(question_1, [], details_v1, mappings_v1, theme_lookup)

        ann_v1 = ResponseAnnotation.objects.get(response=response_1)
        assert ann_v1.evidence_rich is True

        # Second ingestion with different data
        details_v2 = [DetailDetectionInput(themefinder_id=1001, evidence_rich="NO")]
        mappings_v2 = [ThemeMappingInput(themefinder_id=1001, theme_keys=["healthcare"])]
        _ingest_response_annotations(question_1, [], details_v2, mappings_v2, theme_lookup)

        # Should only have one annotation with updated data
        assert ResponseAnnotation.objects.filter(response=response_1).count() == 1
        ann_v2 = ResponseAnnotation.objects.get(response=response_1)
        assert ann_v2.evidence_rich is False

    def test_ingest_annotations_missing_theme_key_warning(self, db, question_1, response_1, caplog):
        """Test warning when theme_key in mapping doesn't exist in selected themes"""
        themes = [
            SelectedThemeInput(
                theme_key="healthcare", theme_name="Healthcare", theme_description="Healthcare"
            )
        ]
        theme_lookup = _ingest_selected_themes(question_1, themes)

        details = [DetailDetectionInput(themefinder_id=1001, evidence_rich="YES")]
        mappings = [
            ThemeMappingInput(themefinder_id=1001, theme_keys=["healthcare", "nonexistent"])
        ]

        _ingest_response_annotations(question_1, [], details, mappings, theme_lookup)

        # Annotation should still be created with available theme
        ann = ResponseAnnotation.objects.get(response=response_1)
        assert ann.themes.count() == 1
        assert ann.themes.first().key == "healthcare"

        # Should log warning about missing theme
        assert "Theme key 'nonexistent' not found" in caplog.text


class TestIngestResponseAnnotationsBatch:
    """Tests for ingest_response_annotations function"""

    def test_ingest_batch_success(
        self, db, consultation, question_1, question_2, response_1, response_2
    ):
        """Test ingesting a complete batch of annotations"""
        batch = AnnotationBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            selected_themes_by_question={
                1: [
                    SelectedThemeInput(
                        theme_key="healthcare",
                        theme_name="Healthcare",
                        theme_description="Healthcare theme",
                    )
                ],
            },
            sentiments_by_question={
                1: [SentimentInput(themefinder_id=1001, sentiment="AGREEMENT")]
            },
            details_by_question={
                1: [DetailDetectionInput(themefinder_id=1001, evidence_rich="YES")]
            },
            mappings_by_question={
                1: [ThemeMappingInput(themefinder_id=1001, theme_keys=["healthcare"])]
            },
        )

        ingest_response_annotations(batch)

        # Verify themes and annotations created
        assert SelectedTheme.objects.filter(question=question_1).count() == 1
        assert ResponseAnnotation.objects.filter(response__question=question_1).count() == 2

        # Verify consultation timestamp updated
        consultation.refresh_from_db()
        assert consultation.timestamp == "2024-01-15"

    def test_ingest_batch_updates_timestamp(self, db, consultation, question_1, response_1):
        """Test that ingestion updates the consultation timestamp"""
        # Set initial timestamp
        consultation.timestamp = "2024-01-01"
        consultation.save()

        batch = AnnotationBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            selected_themes_by_question={
                1: [
                    SelectedThemeInput(
                        theme_key="theme1", theme_name="Theme 1", theme_description="Description"
                    )
                ]
            },
            details_by_question={
                1: [DetailDetectionInput(themefinder_id=1001, evidence_rich="YES")]
            },
            mappings_by_question={
                1: [ThemeMappingInput(themefinder_id=1001, theme_keys=["theme1"])]
            },
        )

        ingest_response_annotations(batch)

        # Verify timestamp updated
        consultation.refresh_from_db()
        assert consultation.timestamp == "2024-01-15"

    def test_ingest_batch_consultation_not_found(self, db):
        """Test error when consultation doesn't exist"""
        batch = AnnotationBatch(
            consultation_code="MISSING",
            timestamp="2024-01-15",
            selected_themes_by_question={},
        )

        with pytest.raises(ValueError, match="Consultation with code 'MISSING' does not exist"):
            ingest_response_annotations(batch)

    def test_ingest_batch_question_not_found(self, db, consultation):
        """Test error when question doesn't exist"""
        batch = AnnotationBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            selected_themes_by_question={
                999: [  # Question doesn't exist
                    SelectedThemeInput(
                        theme_key="theme1", theme_name="Theme 1", theme_description="Description"
                    )
                ]
            },
        )

        with pytest.raises(ValueError, match="Question 999 does not exist"):
            ingest_response_annotations(batch)


class TestImportResponseAnnotationsFromS3:
    """Tests for import_response_annotations_from_s3 orchestration function"""

    def test_import_success(
        self,
        db,
        consultation,
        question_1,
        question_2,
        response_1,
        response_2,
        sample_themes_data,
    ):
        """Test complete import workflow from S3"""
        # Mock the batch loading to avoid S3 calls in orchestration
        mock_batch = AnnotationBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            selected_themes_by_question={
                1: [SelectedThemeInput(**theme) for theme in sample_themes_data],
            },
            sentiments_by_question={
                1: [
                    SentimentInput(themefinder_id=1001, sentiment="AGREEMENT"),
                    SentimentInput(themefinder_id=1002, sentiment="DISAGREEMENT"),
                ]
            },
            details_by_question={
                1: [
                    DetailDetectionInput(themefinder_id=1001, evidence_rich="YES"),
                    DetailDetectionInput(themefinder_id=1002, evidence_rich="NO"),
                ]
            },
            mappings_by_question={
                1: [
                    ThemeMappingInput(themefinder_id=1001, theme_keys=["healthcare"]),
                    ThemeMappingInput(themefinder_id=1002, theme_keys=["education"]),
                ]
            },
        )

        with patch(
            "consultation_analyser.support_console.ingestion.ingest_response_annotations.load_annotation_batch"
        ) as mock_load:
            mock_load.return_value = mock_batch

            import_response_annotations_from_s3(
                consultation_code="TEST",
                timestamp="2024-01-15",
            )

        # Verify themes and annotations created
        assert SelectedTheme.objects.filter(question=question_1).count() == 2
        assert ResponseAnnotation.objects.filter(response__question=question_1).count() == 2

        # Verify consultation timestamp updated
        consultation.refresh_from_db()
        assert consultation.timestamp == "2024-01-15"

    def test_import_specific_questions(
        self, db, consultation, question_1, question_2, response_1, sample_themes_data
    ):
        """Test importing only specific questions"""
        # Mock the batch loading for only question 1
        mock_batch = AnnotationBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            selected_themes_by_question={
                1: [SelectedThemeInput(**theme) for theme in sample_themes_data],
            },
            details_by_question={
                1: [DetailDetectionInput(themefinder_id=1001, evidence_rich="YES")]
            },
            mappings_by_question={
                1: [ThemeMappingInput(themefinder_id=1001, theme_keys=["healthcare"])]
            },
        )

        with patch(
            "consultation_analyser.support_console.ingestion.ingest_response_annotations.load_annotation_batch"
        ) as mock_load:
            mock_load.return_value = mock_batch

            import_response_annotations_from_s3(
                consultation_code="TEST",
                timestamp="2024-01-15",
                question_numbers=[1],  # Only question 1
            )

        # Only question 1 should have themes
        assert SelectedTheme.objects.filter(question=question_1).count() == 2
        assert SelectedTheme.objects.filter(question=question_2).count() == 0
