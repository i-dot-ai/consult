"""
Tests for candidate themes ingestion workflow.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from themefinder.models import ThemeNode

from consultation_analyser.consultations.models import CandidateTheme, Consultation, Question
from consultation_analyser.ingest.ingestion.ingest_candidate_themes import (
    _ingest_candidate_themes_for_question,
    import_candidate_themes_from_s3,
    ingest_candidate_themes,
    load_candidate_themes_batch,
    load_candidate_themes_from_s3,
)
from consultation_analyser.ingest.ingestion.pydantic_models import CandidateThemeBatch


@pytest.fixture
def consultation(db):
    """Create a test consultation"""
    return Consultation.objects.create(code="TEST", title="Test Consultation")


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
def sample_themes_data():
    """Sample S3 theme data matching real format"""
    return {
        "theme_nodes": [
            {
                "topic_id": "1",
                "topic_label": "Healthcare Access",
                "topic_description": "Issues related to accessing healthcare services",
                "source_topic_count": 45,
                "parent_id": "0",
                "children": ["2", "3"],
            },
            {
                "topic_id": "2",
                "topic_label": "Rural Healthcare",
                "topic_description": "Healthcare access in rural areas",
                "source_topic_count": 20,
                "parent_id": "1",
                "children": [],
            },
            {
                "topic_id": "3",
                "topic_label": "Urban Healthcare",
                "topic_description": "Healthcare access in urban areas",
                "source_topic_count": 25,
                "parent_id": "1",
                "children": [],
            },
        ]
    }


@pytest.fixture
def mock_s3_client(sample_themes_data):
    """Mock S3 client that returns sample data"""
    client = MagicMock()
    client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=json.dumps(sample_themes_data).encode()))
    }
    return client


class TestLoadCandidateThemesFromS3:
    """Tests for load_candidate_themes_from_s3 function"""

    def test_load_themes_success(self, mock_s3_client):
        """Test successfully loading and validating themes from S3"""
        themes = load_candidate_themes_from_s3(
            consultation_code="TEST",
            question_number=1,
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=mock_s3_client,
        )

        # Verify correct S3 key was requested
        expected_key = "app_data/consultations/TEST/outputs/sign_off/2024-01-15/question_part_1/clustered_themes.json"
        mock_s3_client.get_object.assert_called_once_with(Bucket="test-bucket", Key=expected_key)

        # Verify themes loaded and validated
        assert len(themes) == 3
        assert all(isinstance(theme, ThemeNode) for theme in themes)

        # Verify first theme
        assert themes[0].topic_id == "1"
        assert themes[0].topic_label == "Healthcare Access"
        assert themes[0].topic_description == "Issues related to accessing healthcare services"
        assert themes[0].source_topic_count == 45
        assert themes[0].parent_id == "0"
        assert themes[0].children == ["2", "3"]

    def test_load_themes_file_not_found(self):
        """Test handling when S3 file doesn't exist"""
        client = MagicMock()
        client.get_object.side_effect = ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

        themes = load_candidate_themes_from_s3(
            consultation_code="TEST",
            question_number=1,
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Should return empty list when file not found
        assert themes == []

    def test_load_themes_invalid_data(self):
        """Test validation error when S3 data is malformed"""
        client = MagicMock()
        invalid_data = [{"topic_id": "1"}]  # Missing required fields
        client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=json.dumps(invalid_data).encode()))
        }

        with pytest.raises(Exception):  # Pydantic ValidationError
            load_candidate_themes_from_s3(
                consultation_code="TEST",
                question_number=1,
                timestamp="2024-01-15",
                bucket_name="test-bucket",
                s3_client=client,
            )


class TestLoadCandidateThemesBatch:
    """Tests for load_candidate_themes_batch function"""

    def test_load_batch_for_multiple_questions(
        self, db, consultation, question_1, question_2, mock_s3_client
    ):
        """Test loading themes for multiple questions"""
        batch = load_candidate_themes_batch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=mock_s3_client,
        )

        # Verify batch created
        assert isinstance(batch, CandidateThemeBatch)
        assert batch.consultation_code == "TEST"
        assert batch.timestamp == "2024-01-15"

        # Should have loaded themes for both questions
        assert 1 in batch.themes_by_question
        assert 2 in batch.themes_by_question
        assert len(batch.themes_by_question[1]) == 3
        assert len(batch.themes_by_question[2]) == 3

    def test_load_batch_specific_questions(
        self, db, consultation, question_1, question_2, mock_s3_client
    ):
        """Test loading themes for specific question numbers only"""
        batch = load_candidate_themes_batch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            question_numbers=[1],  # Only question 1
            bucket_name="test-bucket",
            s3_client=mock_s3_client,
        )

        # Should only have question 1
        assert 1 in batch.themes_by_question
        assert 2 not in batch.themes_by_question

    def test_load_batch_consultation_not_found(self, db):
        """Test error when consultation doesn't exist"""
        with pytest.raises(ValueError, match="Consultation with code 'MISSING' does not exist"):
            load_candidate_themes_batch(
                consultation_code="MISSING",
                timestamp="2024-01-15",
            )

    def test_load_batch_no_themes_for_question(self, db, consultation, question_1):
        """Test handling when no themes file exists for a question"""
        client = MagicMock()
        client.get_object.side_effect = ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

        batch = load_candidate_themes_batch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            bucket_name="test-bucket",
            s3_client=client,
        )

        # Batch should be created but with no themes
        assert batch.themes_by_question == {}


class TestIngestCandidateThemesForQuestion:
    """Tests for _ingest_candidate_themes_for_question function"""

    def test_ingest_themes_basic(self, db, question_1):
        """Test ingesting themes for a question"""
        themes = [
            ThemeNode(
                topic_id="1",
                topic_label="Healthcare Access",
                topic_description="Issues related to accessing healthcare services",
                source_topic_count=45,
                parent_id="0",
                children=[],
            ),
            ThemeNode(
                topic_id="2",
                topic_label="Rural Healthcare",
                topic_description="Healthcare access in rural areas",
                source_topic_count=20,
                parent_id="0",
                children=[],
            ),
        ]

        _ingest_candidate_themes_for_question(question_1, themes)

        # Verify themes created
        assert CandidateTheme.objects.filter(question=question_1).count() == 2

        theme1 = CandidateTheme.objects.get(question=question_1, name="Healthcare Access")
        assert theme1.description == "Issues related to accessing healthcare services"
        assert theme1.approximate_frequency == 45
        assert theme1.parent is None

        theme2 = CandidateTheme.objects.get(question=question_1, name="Rural Healthcare")
        assert theme2.approximate_frequency == 20
        assert theme2.parent is None

    def test_ingest_themes_with_parent_relationships(self, db, question_1):
        """Test ingesting themes with parent-child relationships"""
        themes = [
            ThemeNode(
                topic_id="1",
                topic_label="Healthcare Access",
                topic_description="Main theme",
                source_topic_count=45,
                parent_id="0",
                children=["1", "2"],
            ),
            ThemeNode(
                topic_id="2",
                topic_label="Rural Healthcare",
                topic_description="Sub theme",
                source_topic_count=20,
                parent_id="1",
                children=[],
            ),
        ]

        _ingest_candidate_themes_for_question(question_1, themes)

        # Verify parent relationship set
        parent_theme = CandidateTheme.objects.get(question=question_1, name="Healthcare Access")
        child_theme = CandidateTheme.objects.get(question=question_1, name="Rural Healthcare")

        assert child_theme.parent == parent_theme
        assert parent_theme.parent is None

    def test_ingest_themes_idempotent(self, db, question_1):
        """Test that re-running ingestion deletes old themes"""
        # First ingestion
        themes_v1 = [
            ThemeNode(
                topic_id="1",
                topic_label="Old Theme",
                topic_description="Old description",
                source_topic_count=10,
                parent_id="0",
                children=[],
            )
        ]
        _ingest_candidate_themes_for_question(question_1, themes_v1)
        assert CandidateTheme.objects.filter(question=question_1).count() == 1

        # Second ingestion with different themes
        themes_v2 = [
            ThemeNode(
                topic_id="2",
                topic_label="New Theme",
                topic_description="New description",
                source_topic_count=20,
                parent_id="0",
                children=[],
            ),
            ThemeNode(
                topic_id="3",
                topic_label="Another Theme",
                topic_description="Another description",
                source_topic_count=30,
                parent_id="0",
                children=[],
            ),
        ]
        _ingest_candidate_themes_for_question(question_1, themes_v2)

        # Should have new themes, not old ones
        assert CandidateTheme.objects.filter(question=question_1).count() == 2
        assert not CandidateTheme.objects.filter(question=question_1, name="Old Theme").exists()
        assert CandidateTheme.objects.filter(question=question_1, name="New Theme").exists()

    def test_ingest_themes_empty_list(self, db, question_1):
        """Test ingesting empty themes list"""
        _ingest_candidate_themes_for_question(question_1, [])

        # Should not create any themes
        assert CandidateTheme.objects.filter(question=question_1).count() == 0

    def test_ingest_themes_missing_parent_warning(self, db, question_1, caplog):
        """Test warning when parent_id references non-existent parent"""
        themes = [
            ThemeNode(
                topic_id="2",
                topic_label="Child Theme",
                topic_description="Child with missing parent",
                source_topic_count=10,
                parent_id="999",  # Parent doesn't exist
                children=[],
            )
        ]

        _ingest_candidate_themes_for_question(question_1, themes)

        # Theme should still be created but without parent
        theme = CandidateTheme.objects.get(question=question_1, name="Child Theme")
        assert theme.parent is None

        # Should log warning
        assert "Parent theme with topic_id '999' not found" in caplog.text


class TestIngestCandidateThemes:
    """Tests for ingest_candidate_themes function"""

    def test_ingest_batch_success(self, db, consultation, question_1, question_2):
        """Test ingesting a complete batch of themes"""
        batch = CandidateThemeBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            themes_by_question={
                1: [
                    ThemeNode(
                        topic_id="1",
                        topic_label="Theme Q1",
                        topic_description="Theme for question 1",
                        source_topic_count=10,
                        parent_id="0",
                    )
                ],
                2: [
                    ThemeNode(
                        topic_id="2",
                        topic_label="Theme Q2",
                        topic_description="Theme for question 2",
                        source_topic_count=20,
                        parent_id="0",
                    )
                ],
            },
        )

        ingest_candidate_themes(batch)

        # Verify themes created for both questions
        assert CandidateTheme.objects.filter(question=question_1).count() == 1
        assert CandidateTheme.objects.filter(question=question_2).count() == 1

        # Verify consultation timestamp updated
        consultation.refresh_from_db()
        assert consultation.timestamp == "2024-01-15"

    def test_ingest_batch_updates_timestamp(self, db, consultation, question_1):
        """Test that ingestion updates the consultation timestamp"""
        # Set initial timestamp
        consultation.timestamp = "2024-01-01"
        consultation.save()

        batch = CandidateThemeBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            themes_by_question={
                1: [
                    ThemeNode(
                        topic_id="1",
                        topic_label="Theme",
                        topic_description="Description",
                        source_topic_count=10,
                        parent_id="0",
                    )
                ]
            },
        )

        ingest_candidate_themes(batch)

        # Verify timestamp updated
        consultation.refresh_from_db()
        assert consultation.timestamp == "2024-01-15"

    def test_ingest_batch_consultation_not_found(self, db):
        """Test error when consultation doesn't exist"""
        batch = CandidateThemeBatch(
            consultation_code="MISSING",
            timestamp="2024-01-15",
            themes_by_question={},
        )

        with pytest.raises(ValueError, match="Consultation with code 'MISSING' does not exist"):
            ingest_candidate_themes(batch)

    def test_ingest_batch_question_not_found(self, db, consultation):
        """Test error when question doesn't exist"""
        batch = CandidateThemeBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            themes_by_question={
                999: [  # Question doesn't exist
                    ThemeNode(
                        topic_id="1",
                        topic_label="Theme",
                        topic_description="Description",
                        source_topic_count=10,
                        parent_id="0",
                    )
                ]
            },
        )

        with pytest.raises(ValueError, match="Question 999 does not exist"):
            ingest_candidate_themes(batch)


class TestImportCandidateThemesFromS3:
    """Tests for import_candidate_themes_from_s3 orchestration function"""

    def test_import_success(self, db, consultation, question_1, question_2, sample_themes_data):
        """Test complete import workflow from S3"""
        # Mock the batch loading to avoid S3 calls in orchestration
        mock_batch = CandidateThemeBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            themes_by_question={
                1: [ThemeNode(**theme) for theme in sample_themes_data["theme_nodes"]],
                2: [ThemeNode(**theme) for theme in sample_themes_data["theme_nodes"]],
            },
        )

        with patch(
            "consultation_analyser.ingest.ingestion.ingest_candidate_themes.load_candidate_themes_batch"
        ) as mock_load:
            mock_load.return_value = mock_batch

            import_candidate_themes_from_s3(
                consultation_code="TEST",
                timestamp="2024-01-15",
            )

        # Verify themes created
        assert CandidateTheme.objects.filter(question=question_1).count() == 3
        assert CandidateTheme.objects.filter(question=question_2).count() == 3

        # Verify consultation timestamp updated
        consultation.refresh_from_db()
        assert consultation.timestamp == "2024-01-15"

    def test_import_specific_questions(
        self, db, consultation, question_1, question_2, sample_themes_data
    ):
        """Test importing only specific questions"""
        # Mock the batch loading for only question 1
        mock_batch = CandidateThemeBatch(
            consultation_code="TEST",
            timestamp="2024-01-15",
            themes_by_question={
                1: [ThemeNode(**theme) for theme in sample_themes_data["theme_nodes"]],
            },
        )

        with patch(
            "consultation_analyser.ingest.ingestion.ingest_candidate_themes.load_candidate_themes_batch"
        ) as mock_load:
            mock_load.return_value = mock_batch

            import_candidate_themes_from_s3(
                consultation_code="TEST",
                timestamp="2024-01-15",
                question_numbers=[1],  # Only question 1
            )

        # Only question 1 should have themes
        assert CandidateTheme.objects.filter(question=question_1).count() == 3
        assert CandidateTheme.objects.filter(question=question_2).count() == 0
