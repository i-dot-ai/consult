"""
Utilities for formatting and handling validation errors in consultation data import.
"""


def _extract_file_path_from_error_message(error_message: str) -> str | None:
    """Extract file path from various error message formats."""
    if error_message.startswith("Missing required file:"):
        return error_message.replace("Missing required file: ", "")
    elif error_message.startswith("Missing output file:"):
        return error_message.replace("Missing output file: ", "")
    elif error_message.startswith("Missing "):
        return error_message.replace("Missing ", "")
    elif error_message.startswith("Invalid JSON in "):
        return error_message.split("Invalid JSON in ")[1]
    elif error_message.startswith("Invalid JSONL in "):
        return error_message.split("Invalid JSONL in ")[1]
    elif error_message.startswith("Empty file:"):
        return error_message.replace("Empty file: ", "")
    elif "Error checking " in error_message:
        parts = error_message.split("Error checking ")[1].split(":")
        return parts[0] if parts else None
    return None


def _extract_question_part_from_file_path(file_path: str) -> str | None:
    """Extract question part number from file path containing 'question_part_'."""
    if "question_part_" not in file_path:
        return None
    try:
        return file_path.split("question_part_")[1].split("/")[0]
    except IndexError:
        return None


def _create_validation_error_response(
    error_type: str, 
    user_message: str, 
    technical_message: str, 
    file_path: str | None = None
) -> dict[str, str]:
    """Create standardized error dictionary structure."""
    response = {
        "type": error_type,
        "message": user_message,
        "technical": technical_message
    }
    if file_path:
        response["file_path"] = file_path
    return response


def _format_missing_file_errors(error_message: str) -> dict[str, str] | None:
    """Handle missing file errors with consistent formatting."""
    prefixes = ["Missing required file:", "Missing output file:", "Missing "]
    
    for prefix in prefixes:
        if not error_message.startswith(prefix):
            continue
            
        file_path = error_message.replace(prefix, "").strip()
        file_name = file_path.split('/')[-1]
        question_part = _extract_question_part_from_file_path(file_path)
        
        if prefix == "Missing required file:":
            message = f"Required file is missing: {file_name}"
            error_type = "missing_file"
        elif prefix == "Missing output file:":
            message = f"Missing AI output file: {file_name}"
            error_type = "missing_output"
        else:  # "Missing "
            message = f"Missing {file_name}"
            error_type = "missing_file"
        
        if question_part:
            message += f" for question part {question_part}"
            
        return _create_validation_error_response(error_type, message, error_message, file_path)
    
    return None


def _format_file_format_errors(error_message: str) -> dict[str, str] | None:
    """Handle file format and validation errors."""
    format_patterns = [
        ("Invalid JSON", "invalid_format", "contains invalid JSON format"),
        ("Invalid JSONL", "invalid_format", "contains invalid JSONL format"),
        ("Empty file:", "empty_file", "is empty")
    ]
    
    for pattern, error_type, description in format_patterns:
        if error_message.startswith(pattern):
            file_path = _extract_file_path_from_error_message(error_message)
            if file_path:
                file_name = file_path.split('/')[-1]
                message = f"The file {file_name} {description}"
                return _create_validation_error_response(error_type, message, error_message, file_path)
    
    return None


def _format_access_errors(error_message: str) -> dict[str, str] | None:
    """Handle file access and permission errors."""
    if "An error occurred (404)" in error_message and "HeadObject operation: Not Found" in error_message:
        file_path = _extract_file_path_from_error_message(error_message)
        if file_path:
            file_name = file_path.split('/')[-1]
            message = f"Cannot find file: {file_name}"
            return _create_validation_error_response("file_not_found", message, error_message, file_path)
    
    elif error_message.startswith("Error checking "):
        parts = error_message.split(": ", 1)
        if len(parts) > 1:
            file_path = _extract_file_path_from_error_message(error_message)
            if file_path:
                file_name = file_path.split('/')[-1]
                error_detail = parts[1]
                message = f"Problem accessing {file_name}: {error_detail}"
                return _create_validation_error_response("file_error", message, error_message, file_path)
    
    return None


def format_validation_error(error_message: str) -> dict[str, str]:
    """
    Formats a validation error message into a more user-friendly format.
    
    Returns:
        dict: {"type": error_type, "message": user_friendly_message, "technical": original_message}
    """
    error_message = error_message.strip()
    
    # Try each error type handler in order
    for handler in [_format_missing_file_errors, _format_file_format_errors, _format_access_errors]:
        result = handler(error_message)
        if result:
            return result
    
    # Handle specific structural errors
    if "No question_part folders found" in error_message:
        return _create_validation_error_response(
            "no_questions",
            "No question folders found. Please ensure your consultation has at least one question_part folder.",
            error_message
        )
    
    # Handle system errors
    if error_message.startswith("Unexpected error during validation:"):
        return _create_validation_error_response(
            "system_error",
            "An unexpected error occurred during validation. Please check your S3 configuration and try again.",
            error_message
        )
    
    # Default fallback
    return _create_validation_error_response("unknown", error_message, error_message)