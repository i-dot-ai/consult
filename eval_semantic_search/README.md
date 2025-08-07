# Semantic Search Evaluation

A framework for evaluating semantic search precision in consultation responses.

## Overview

This tool measures how well semantic search (using OpenAI text-embedding-3-small) can identify responses that belong to specific themes. For each theme, it:

1. Creates a search query: "theme name: theme description"
2. Generates an embedding for the query
3. Finds the top-k most similar responses
4. Calculates precision by comparing with ground truth theme assignments

## Setup

1. Ensure your `.env` file contains:
   ```
   AZURE_OPENAI_API_KEY=your-key
   AZURE_OPENAI_ENDPOINT=your-endpoint
   AZURE_OPENAI_API_VERSION=2024-02-01
   ```

2. Create a config file:
   ```yaml
   consultation_code: my_consultation
   output_file: results.json
   output_dir_timestamp: "2025-05-22"  # Timestamp folder containing themes
   k: 20
   use_question_prefix: false  # Whether to prefix responses with question text
   ```

## Usage

Run from the repository root:

```bash
# Single config file
poetry run python eval_semantic_search/run_eval.py --config path/to/my_config.yaml

# Directory of config files (batch mode)
poetry run python eval_semantic_search/run_eval.py --config path/to/configs/

# Skip data import
poetry run python eval_semantic_search/run_eval.py --config path/to/config --no-import-data
```

## Data Structure

Data must be placed in the `eval_semantic_search/data` directory. Expected structure:
```
eval_semantic_search/
└── data/
    └── consultation_code/
        ├── inputs/
        │   ├── respondents.jsonl
        │   ├── question_part_1/
        │   │   ├── question.json
        │   │   └── responses.jsonl
        │   └── question_part_2/
        │       ├── question.json
        │       └── responses.jsonl
        └── outputs/
            └── mapping/
                └── [timestamp]/  # e.g., "2025-05-22"
                    ├── question_part_1/
                    │   ├── themes.json
                    │   └── mapping.jsonl
                    └── question_part_2/
                        ├── themes.json
                        └── mapping.jsonl
```

## Configuration

- `consultation_code`: Identifier for the consultation
- `output_file`: Where to save results (automatically goes to eval_semantic_search/results/)
- `output_dir_timestamp`: Timestamp folder containing themes (e.g., "2025-05-22")
- `k`: Number of top results to evaluate
- `use_question_prefix`: Whether to prefix responses with question text
- `import_data`: Whether to import data before evaluation (default: true)

## Output

Results are saved as JSON with:
- Overall precision across all themes
- Per-question breakdown
- Per-theme precision scores

Example:
```json
{
  "consultation": "My Consultation",
  "overall_precision": 0.725,
  "total_questions": 5,
  "total_themes": 25,
  "questions": [
    {
      "question_number": 1,
      "question_text": "What do you think about...",
      "average_precision": 0.8,
      "themes": [...]
    }
  ]
}
```