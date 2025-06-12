import pytest

from consultation_analyser.support_console.validation_utils import (
    format_validation_error,
    _extract_file_path_from_error_message,
    _extract_question_part_from_file_path,
    _create_validation_error_response,
    _format_missing_file_errors,
    _format_file_format_errors,
    _format_access_errors,
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


class TestHelperFunctions:
    """Test the helper functions used by format_validation_error."""
    
    def test_extract_file_path_from_error_message(self):
        # Test various error message formats
        test_cases = [
            ("Missing required file: path/to/file.json", "path/to/file.json"),
            ("Missing output file: path/to/output.json", "path/to/output.json"),
            ("Missing path/to/file.jsonl", "path/to/file.jsonl"),
            ("Invalid JSON in path/to/file.json", "path/to/file.json"),
            ("Invalid JSONL in path/to/file.jsonl", "path/to/file.jsonl"),
            ("Empty file: path/to/file.json", "path/to/file.json"),
            ("Error checking path/to/file.json: Some error", "path/to/file.json"),
            ("Unknown error format", None),
        ]
        
        for error_message, expected_path in test_cases:
            result = _extract_file_path_from_error_message(error_message)
            assert result == expected_path, f"Failed for: {error_message}"

    def test_extract_question_part_from_file_path(self):
        test_cases = [
            ("app_data/test/inputs/question_part_1/file.json", "1"),
            ("app_data/test/outputs/question_part_42/file.json", "42"),
            ("app_data/test/inputs/question_part_1/subfolder/file.json", "1"),
            ("app_data/test/inputs/no_question_part/file.json", None),
            ("question_part_5", "5"),
            ("", None),
        ]
        
        for file_path, expected_part in test_cases:
            result = _extract_question_part_from_file_path(file_path)
            assert result == expected_part, f"Failed for: {file_path}"

    def test_create_validation_error_response(self):
        # Test without file_path
        result = _create_validation_error_response(
            "test_type", "Test message", "Technical message"
        )
        expected = {
            "type": "test_type",
            "message": "Test message", 
            "technical": "Technical message"
        }
        assert result == expected
        
        # Test with file_path
        result = _create_validation_error_response(
            "test_type", "Test message", "Technical message", "path/to/file.json"
        )
        expected = {
            "type": "test_type",
            "message": "Test message",
            "technical": "Technical message",
            "file_path": "path/to/file.json"
        }
        assert result == expected

    def test_format_missing_file_errors(self):
        # Test cases that should be handled
        test_cases = [
            ("Missing required file: app_data/test/file.json", "missing_file"),
            ("Missing output file: app_data/test/output.json", "missing_output"),
            ("Missing app_data/test/file.jsonl", "missing_file"),
        ]
        
        for error_message, expected_type in test_cases:
            result = _format_missing_file_errors(error_message)
            assert result is not None, f"Should handle: {error_message}"
            assert result["type"] == expected_type
            
        # Test case that should not be handled
        result = _format_missing_file_errors("Invalid JSON in file.json")
        assert result is None

    def test_format_file_format_errors(self):
        # Test cases that should be handled
        test_cases = [
            ("Invalid JSON in app_data/test/file.json", "invalid_format"),
            ("Invalid JSONL in app_data/test/file.jsonl", "invalid_format"), 
            ("Empty file: app_data/test/file.json", "empty_file"),
        ]
        
        for error_message, expected_type in test_cases:
            result = _format_file_format_errors(error_message)
            assert result is not None, f"Should handle: {error_message}"
            assert result["type"] == expected_type
            
        # Test case that should not be handled
        result = _format_file_format_errors("Missing file.json")
        assert result is None

    def test_format_access_errors(self):
        # Test 404 error case
        error_404 = "Error checking app_data/test/file.json: An error occurred (404) when calling the HeadObject operation: Not Found"
        result = _format_access_errors(error_404)
        assert result is not None
        assert result["type"] == "file_not_found"
        assert "file.json" in result["message"]
        
        # Test generic error checking case
        error_generic = "Error checking app_data/test/file.json: Some other error"
        result = _format_access_errors(error_generic)
        assert result is not None
        assert result["type"] == "file_error"
        assert "file.json" in result["message"]
        assert "Some other error" in result["message"]
        
        # Test case that should not be handled
        result = _format_access_errors("Missing file.json")
        assert result is None