#!/usr/bin/env python3
"""
Generate consultation data files for load testing.

This script generates respondents, questions, and responses in the format
expected by the consultation import process.
"""

import argparse
import json
import os
import random
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import yaml


def load_config(config_path: Path) -> dict[str, Any]:
    """Load load_test_config.yaml"""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_sample_data(sample_data_path: Path) -> dict[str, Any]:
    """Load sample_data.yaml with questions, responses, demographics, mc_options"""
    with open(sample_data_path, "r") as f:
        return yaml.safe_load(f)


def get_s3_bucket_name(environment: Optional[str] = None) -> str:
    """
    Get S3 bucket name based on environment.
    
    Args:
        environment: Environment name (dev, preprod, prod). If None, reads from ENVIRONMENT env var.
    
    Returns:
        S3 bucket name
    """
    if environment is None:
        environment = os.environ.get('ENVIRONMENT', 'dev')
    
    environment = environment.lower()
    
    if environment in ['dev', 'preprod']:
        return f"i-dot-ai-{environment}-consult-data"
    else:
        return "i-dot-ai-prod-consult-data"


def validate_s3_connection(bucket_name: str) -> bool:
    """
    Validate S3 connection by attempting to list bucket.
    
    Args:
        bucket_name: Name of S3 bucket to test
    
    Returns:
        True if connection is valid, False otherwise
    """
    try:
        s3_client = boto3.client('s3')
        # Try to list the bucket (head_bucket would be faster but ls is more user-friendly)
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✓ S3 connection validated: {bucket_name}")
        return True
    except NoCredentialsError:
        print("✗ ERROR: No AWS credentials found!")
        print("  Please run this script inside an aws-vault exec session:")
        print(f"    aws-vault exec <profile> -- uv run scripts/generate_consultation_data.py ...")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '403':
            print(f"✗ ERROR: Access denied to bucket: {bucket_name}")
            print("  Check your AWS permissions")
        elif error_code == '404':
            print(f"✗ ERROR: Bucket not found: {bucket_name}")
            print("  Check the bucket name and environment")
        else:
            print(f"✗ ERROR: S3 connection failed: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: Unexpected S3 error: {e}")
        return False


def upload_to_s3(
    local_path: Path,
    bucket_name: str,
    s3_prefix: str,
    dry_run: bool = False
) -> bool:
    """
    Upload directory to S3 using sync-like behavior.
    
    Args:
        local_path: Local directory path to upload
        bucket_name: S3 bucket name
        s3_prefix: S3 key prefix (e.g., 'app_data/consultations/my-consultation/inputs')
        dry_run: If True, only show what would be uploaded
    
    Returns:
        True if upload succeeded, False otherwise
    """
    if dry_run:
        print(f"  [DRY RUN] Would upload: {local_path} -> s3://{bucket_name}/{s3_prefix}/")
        return True
    
    try:
        s3_client = boto3.client('s3')
        uploaded_files = 0
        
        # Walk through local directory and upload all files
        for root, dirs, files in os.walk(local_path):
            for file in files:
                local_file = Path(root) / file
                # Calculate relative path from local_path
                relative_path = local_file.relative_to(local_path)
                # Construct S3 key
                s3_key = f"{s3_prefix}/{relative_path}".replace('\\', '/')
                
                # Upload file
                print(f"    Uploading: {relative_path} -> s3://{bucket_name}/{s3_key}")
                s3_client.upload_file(
                    str(local_file),
                    bucket_name,
                    s3_key
                )
                uploaded_files += 1
        
        print(f"  ✓ Uploaded {uploaded_files} files to s3://{bucket_name}/{s3_prefix}/")
        return True
        
    except Exception as e:
        print(f"  ✗ Upload failed: {e}")
        return False


def upload_consultations_to_s3(
    consultation_codes: list[str],
    temp_data_dir: Path,
    bucket_name: str,
    dry_run: bool = False
) -> dict[str, bool]:
    """
    Upload multiple consultations to S3.
    
    Args:
        consultation_codes: List of consultation codes to upload
        temp_data_dir: Base directory containing consultation folders
        bucket_name: S3 bucket name
        dry_run: If True, only show what would be uploaded
    
    Returns:
        Dictionary mapping consultation_code to success status
    """
    results = {}
    
    print(f"\nUploading {len(consultation_codes)} consultation(s) to S3...")
    print(f"Bucket: {bucket_name}")
    print("=" * 80)
    
    for code in consultation_codes:
        print(f"\nUploading: {code}")
        local_path = temp_data_dir / code
        
        if not local_path.exists():
            print(f"  ✗ Local directory not found: {local_path}")
            results[code] = False
            continue
        
        # S3 path: app_data/consultations/{code}/inputs/
        s3_prefix = f"app_data/consultations/{code}/inputs"
        
        success = upload_to_s3(local_path, bucket_name, s3_prefix, dry_run)
        results[code] = success
    
    return results


def generate_respondents(
    num_respondents: int, demographics: dict[str, list[str]]
) -> list[dict[str, Any]]:
    """
    Generate respondents.jsonl data.
    
    Args:
        num_respondents: Number of respondents to generate
        demographics: Dictionary of demographic categories and their possible values
    
    Returns:
        List of respondent dictionaries
    """
    respondents = []
    
    for i in range(1, num_respondents + 1):
        # For each demographic category, select exactly 1 random value
        demographic_data = {}
        for category, options in demographics.items():
            demographic_data[category] = [random.choice(options)]
        
        respondent = {
            "themefinder_id": i,
            "demographic_data": demographic_data
        }
        respondents.append(respondent)
    
    return respondents


def determine_question_type(
    question_num: int, total_questions: int, distribution: dict[str, int]
) -> str:
    """
    Determine if question is 'open', 'hybrid', or 'multiple_choice'
    based on percentage distribution from config.
    
    Args:
        question_num: Current question number (1-indexed)
        total_questions: Total number of questions
        distribution: Dictionary with 'open', 'hybrid', 'multiple_choice' percentages
    
    Returns:
        'open' | 'hybrid' | 'multiple_choice'
    """
    # Calculate cutoff points based on percentages
    open_count = int(total_questions * distribution['open'] / 100)
    hybrid_count = int(total_questions * distribution['hybrid'] / 100)
    # Remaining are multiple_choice
    
    if question_num <= open_count:
        return 'open'
    elif question_num <= open_count + hybrid_count:
        return 'hybrid'
    else:
        return 'multiple_choice'


def generate_question(
    question_num: int,
    question_type: str,
    question_texts: list[str],
    mc_options: list[str]
) -> dict[str, Any]:
    """
    Generate question.json data.
    
    Args:
        question_num: Question number (1-indexed)
        question_type: 'open', 'hybrid', or 'multiple_choice'
        question_texts: List of available question texts
        mc_options: List of available multiple choice options
    
    Returns:
        Question dictionary
    """
    question_text = random.choice(question_texts)
    
    question_data = {
        "question_number": question_num,
        "question_text": question_text,
        "has_free_text": question_type in ['open', 'hybrid']
    }
    
    # Add multiple choice options for hybrid and multiple_choice questions
    if question_type in ['hybrid', 'multiple_choice']:
        # Select 3-5 random options
        num_options = random.randint(3, 5)
        selected_options = random.sample(mc_options, min(num_options, len(mc_options)))
        question_data["multi_choice_options"] = selected_options
    
    return question_data


def generate_responses(
    respondent_ids: list[int],
    response_texts: list[str],
    coverage_percent: float = 80.0
) -> list[dict[str, Any]]:
    """
    Generate responses.jsonl data (for open/hybrid questions with free text).
    
    Args:
        respondent_ids: List of all respondent IDs
        response_texts: List of available response texts
        coverage_percent: Percentage of respondents who answer (default: 80%)
    
    Returns:
        List of response dictionaries
    """
    # Randomly select subset of respondents to answer
    num_respondents_answering = int(len(respondent_ids) * coverage_percent / 100)
    respondents_answering = random.sample(respondent_ids, num_respondents_answering)
    
    responses = []
    for respondent_id in respondents_answering:
        response = {
            "themefinder_id": respondent_id,
            "text": random.choice(response_texts)
        }
        responses.append(response)
    
    return responses


def generate_multi_choice_responses(
    respondent_ids: list[int],
    mc_options: list[str],
    coverage_percent: float = 85.0
) -> list[dict[str, Any]]:
    """
    Generate multi_choice.jsonl data (for hybrid/multiple_choice questions).
    
    Args:
        respondent_ids: List of all respondent IDs
        mc_options: List of multiple choice options for this question
        coverage_percent: Percentage of respondents who answer (default: 85%)
    
    Returns:
        List of multi_choice dictionaries
    """
    # Randomly select subset of respondents to answer
    num_respondents_answering = int(len(respondent_ids) * coverage_percent / 100)
    respondents_answering = random.sample(respondent_ids, num_respondents_answering)
    
    multi_choice_responses = []
    for respondent_id in respondents_answering:
        # Each respondent can select 1-3 options
        num_selections = random.randint(1, min(3, len(mc_options)))
        selected_options = random.sample(mc_options, num_selections)
        
        response = {
            "themefinder_id": respondent_id,
            "options": selected_options
        }
        multi_choice_responses.append(response)
    
    return multi_choice_responses


def write_jsonl(filepath: Path, data: list[dict[str, Any]]) -> None:
    """Write list of dicts to JSONL file (one JSON object per line)"""
    with open(filepath, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")


def write_json(filepath: Path, data: dict[str, Any]) -> None:
    """Write dict to JSON file (pretty formatted)"""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def generate_consultation_data(
    consultation: dict[str, Any],
    sample_data: dict[str, Any],
    output_base_dir: Path
) -> dict[str, Any]:
    """
    Generate all files for one consultation.
    
    Args:
        consultation: Consultation configuration from load_test_config.yaml
        sample_data: Sample data from sample_data.yaml
        output_base_dir: Base directory for output (e.g., scripts/temp_data)
    
    Returns:
        Statistics dictionary with counts of generated data
    """
    consultation_code = consultation['code']
    num_questions = consultation['num_questions']
    num_respondents = consultation['num_respondents']
    question_types_dist = consultation['question_types']
    
    print(f"\nGenerating data for: {consultation['name']}")
    print(f"  Code: {consultation_code}")
    print(f"  Questions: {num_questions}")
    print(f"  Respondents: {num_respondents}")
    
    # Create consultation directory
    consultation_dir = output_base_dir / consultation_code
    consultation_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate respondents
    print(f"  Generating respondents...")
    respondents = generate_respondents(num_respondents, sample_data['demographics'])
    respondents_file = consultation_dir / "respondents.jsonl"
    write_jsonl(respondents_file, respondents)
    
    # Get all respondent IDs
    respondent_ids = [r['themefinder_id'] for r in respondents]
    
    # Statistics
    stats = {
        'consultation_code': consultation_code,
        'consultation_name': consultation['name'],
        'num_respondents': num_respondents,
        'num_questions': num_questions,
        'questions_by_type': {'open': 0, 'hybrid': 0, 'multiple_choice': 0},
        'total_free_text_responses': 0,
        'total_multi_choice_responses': 0,
        'total_files': 1  # respondents.jsonl
    }
    
    # Generate questions
    print(f"  Generating {num_questions} questions...")
    for q_num in range(1, num_questions + 1):
        question_type = determine_question_type(q_num, num_questions, question_types_dist)
        stats['questions_by_type'][question_type] += 1
        
        # Create question directory
        question_dir = consultation_dir / f"question_part_{q_num}"
        question_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate question.json
        question_data = generate_question(
            q_num,
            question_type,
            sample_data['questions'],
            sample_data['multiple_choice_options']
        )
        question_file = question_dir / "question.json"
        write_json(question_file, question_data)
        stats['total_files'] += 1
        
        # Generate responses.jsonl (for open/hybrid questions)
        if question_type in ['open', 'hybrid']:
            responses = generate_responses(
                respondent_ids,
                sample_data['responses'],
                coverage_percent=random.uniform(70, 90)  # Variable coverage
            )
            responses_file = question_dir / "responses.jsonl"
            write_jsonl(responses_file, responses)
            stats['total_free_text_responses'] += len(responses)
            stats['total_files'] += 1
        
        # Generate multi_choice.jsonl (for hybrid/multiple_choice questions)
        if question_type in ['hybrid', 'multiple_choice']:
            mc_responses = generate_multi_choice_responses(
                respondent_ids,
                question_data['multi_choice_options'],
                coverage_percent=random.uniform(75, 95)  # Variable coverage
            )
            mc_file = question_dir / "multi_choice.jsonl"
            write_jsonl(mc_file, mc_responses)
            stats['total_multi_choice_responses'] += len(mc_responses)
            stats['total_files'] += 1
    
    print(f"  ✓ Generated {stats['total_files']} files")
    print(f"    - Open questions: {stats['questions_by_type']['open']}")
    print(f"    - Hybrid questions: {stats['questions_by_type']['hybrid']}")
    print(f"    - Multiple choice questions: {stats['questions_by_type']['multiple_choice']}")
    print(f"    - Total free text responses: {stats['total_free_text_responses']}")
    print(f"    - Total multi-choice responses: {stats['total_multi_choice_responses']}")
    
    return stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate consultation data files for load testing"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="scripts/load_test_config.yaml",
        help="Path to load test configuration file (default: scripts/load_test_config.yaml)"
    )
    parser.add_argument(
        "--sample-data",
        type=str,
        default="scripts/sample_data.yaml",
        help="Path to sample data file (default: scripts/sample_data.yaml)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="scripts/temp_data",
        help="Output directory for generated files (default: scripts/temp_data)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output directory before generating (default: true)"
    )
    parser.add_argument(
        "--upload-to-s3",
        action="store_true",
        help="Upload generated files to S3 after generation"
    )
    parser.add_argument(
        "--environment",
        type=str,
        default=None,
        help="Environment for S3 bucket (dev/preprod/prod). Defaults to ENVIRONMENT env var or 'dev'"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform dry run (generate files but don't upload to S3)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to script directory
    script_dir = Path(__file__).parent
    
    # Handle relative paths
    if Path(args.config).is_absolute():
        config_path = Path(args.config)
    else:
        # Remove 'scripts/' prefix if present (since we're already in scripts dir)
        config_rel = args.config.replace('scripts/', '')
        config_path = script_dir / config_rel
    
    if Path(args.sample_data).is_absolute():
        sample_data_path = Path(args.sample_data)
    else:
        sample_rel = args.sample_data.replace('scripts/', '')
        sample_data_path = script_dir / sample_rel
    
    if Path(args.output_dir).is_absolute():
        output_dir = Path(args.output_dir)
    else:
        output_rel = args.output_dir.replace('scripts/', '')
        output_dir = script_dir / output_rel
    
    # Clean output directory if requested (default behavior)
    if output_dir.exists() and (args.clean or True):  # Always clean by default
        print(f"Cleaning output directory: {output_dir}")
        shutil.rmtree(output_dir)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load configuration
    print(f"Loading configuration from: {config_path}")
    config = load_config(config_path)
    
    # Load sample data
    print(f"Loading sample data from: {sample_data_path}")
    sample_data = load_sample_data(sample_data_path)
    
    # Generate data for each consultation
    all_stats = []
    consultations = config.get('consultations', [])
    
    print(f"\nGenerating data for {len(consultations)} consultation(s)...")
    print("=" * 80)
    
    for consultation in consultations:
        stats = generate_consultation_data(consultation, sample_data, output_dir)
        all_stats.append(stats)
    
    # Print summary
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"\nOutput directory: {output_dir.absolute()}")
    print(f"\nGenerated {len(all_stats)} consultation(s):")
    
    total_files = 0
    total_respondents = 0
    total_questions = 0
    total_free_text = 0
    total_mc = 0
    
    for stats in all_stats:
        print(f"\n  {stats['consultation_name']} ({stats['consultation_code']})")
        print(f"    - Respondents: {stats['num_respondents']}")
        print(f"    - Questions: {stats['num_questions']} "
              f"({stats['questions_by_type']['open']} open, "
              f"{stats['questions_by_type']['hybrid']} hybrid, "
              f"{stats['questions_by_type']['multiple_choice']} multiple choice)")
        print(f"    - Free text responses: {stats['total_free_text_responses']}")
        print(f"    - Multi-choice responses: {stats['total_multi_choice_responses']}")
        print(f"    - Files generated: {stats['total_files']}")
        
        total_files += stats['total_files']
        total_respondents += stats['num_respondents']
        total_questions += stats['num_questions']
        total_free_text += stats['total_free_text_responses']
        total_mc += stats['total_multi_choice_responses']
    
    print(f"\nTOTALS:")
    print(f"  - Total files: {total_files}")
    print(f"  - Total respondents: {total_respondents}")
    print(f"  - Total questions: {total_questions}")
    print(f"  - Total free text responses: {total_free_text}")
    print(f"  - Total multi-choice responses: {total_mc}")
    print(f"  - Total responses: {total_free_text + total_mc}")
    
    print(f"\n✓ Data generation complete!")
    
    # S3 Upload
    if args.upload_to_s3:
        print("\n" + "=" * 80)
        print("S3 UPLOAD")
        print("=" * 80)
        
        # Get bucket name
        bucket_name = get_s3_bucket_name(args.environment)
        environment_display = args.environment or os.environ.get('ENVIRONMENT', 'dev')
        print(f"\nEnvironment: {environment_display}")
        print(f"Bucket: {bucket_name}")
        
        # Validate S3 connection
        print(f"\nValidating S3 connection...")
        if not validate_s3_connection(bucket_name):
            print("\n✗ S3 upload aborted due to connection error")
            sys.exit(1)
        
        # Upload consultations
        consultation_codes = [stats['consultation_code'] for stats in all_stats]
        upload_results = upload_consultations_to_s3(
            consultation_codes,
            output_dir,
            bucket_name,
            dry_run=args.dry_run
        )
        
        # Print upload summary
        print("\n" + "=" * 80)
        print("UPLOAD SUMMARY")
        print("=" * 80)
        
        successful = sum(1 for success in upload_results.values() if success)
        failed = len(upload_results) - successful
        
        print(f"\nUploaded: {successful}/{len(upload_results)} consultation(s)")
        if failed > 0:
            print(f"Failed: {failed}")
            print("\nFailed consultations:")
            for code, success in upload_results.items():
                if not success:
                    print(f"  - {code}")
        
        if successful == len(upload_results):
            print(f"\n✓ All consultations uploaded successfully!")
        elif successful > 0:
            print(f"\n⚠ Some consultations failed to upload")
            sys.exit(1)
        else:
            print(f"\n✗ All uploads failed")
            sys.exit(1)
    
    print(f"\nNext steps:")
    if args.upload_to_s3 and not args.dry_run:
        print(f"  ✓ Files uploaded to S3")
        print(f"  → Trigger import via: POST /api/consultations/setup/")
        print(f"     with body: {{'consultation_name': '<name>', 'consultation_code': '<code>'}}")
    else:
        print(f"  1. Review generated files in: {output_dir}")
        print(f"  2. Upload to S3: app_data/consultations/{{consultation_code}}/inputs/")
        print(f"     (or run with --upload-to-s3 flag)")
        print(f"  3. Trigger import via: POST /api/consultations/setup/")



if __name__ == "__main__":
    main()
