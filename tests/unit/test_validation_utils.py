
from consultation_analyser.support_console.validation_utils import (
    format_validation_error,
)


class TestFormatValidationError:
    def test_missing_required_file(self):
        error = "Missing required file: app_data/test/inputs/respondents.jsonl"
        result = format_validation_error(error)
        assert result["type"] == "missing_file"
        assert "respondents.jsonl" in result["message"]
        assert result["file_path"] == "app_data/test/inputs/respondents.jsonl"

    def test_missing_file_with_question_part(self):
        error = "Missing app_data/test/inputs/question_part_1/question.json"
        result = format_validation_error(error)
        assert result["type"] == "missing_file"
        assert "question.json" in result["message"]
        assert "question part 1" in result["message"]

    def test_missing_output_file(self):
        error = "Missing output file: app_data/test/outputs/mapping/2024-01-01/question_part_1/themes.json"
        result = format_validation_error(error)
        assert result["type"] == "missing_output"
        assert "themes.json" in result["message"]
        assert "question part 1" in result["message"]

    def test_no_questions_found(self):
        error = "No question_part folders found in app_data/test/inputs/"
        result = format_validation_error(error)
        assert result["type"] == "no_questions"
        assert "No question folders found" in result["message"]

    def test_invalid_json(self):
        error = "Invalid JSON in app_data/test/inputs/question_part_1/question.json"
        result = format_validation_error(error)
        assert result["type"] == "invalid_format"
        assert "question.json" in result["message"]
        assert "invalid JSON format" in result["message"]

    def test_invalid_jsonl(self):
        error = "Invalid JSONL in app_data/test/inputs/question_part_1/responses.jsonl"
        result = format_validation_error(error)
        assert result["type"] == "invalid_format"
        assert "responses.jsonl" in result["message"]
        assert "invalid JSONL format" in result["message"]

    def test_empty_file(self):
        error = "Empty file: app_data/test/inputs/question_part_1/responses.jsonl"
        result = format_validation_error(error)
        assert result["type"] == "empty_file"
        assert "responses.jsonl" in result["message"]
        assert "empty" in result["message"]

    def test_file_not_found(self):
        error = "Error checking app_data/test/file.json: An error occurred (404) when calling the HeadObject operation: Not Found"
        result = format_validation_error(error)
        assert result["type"] == "file_not_found"
        assert "file.json" in result["message"]
        assert "Cannot find file" in result["message"]

    def test_unexpected_error(self):
        error = "Unexpected error during validation: Something went wrong"
        result = format_validation_error(error)
        assert result["type"] == "system_error"
        assert "unexpected error" in result["message"]

    def test_unknown_error(self):
        error = "Some random error message"
        result = format_validation_error(error)
        assert result["type"] == "unknown"
        assert result["message"] == "Some random error message"


