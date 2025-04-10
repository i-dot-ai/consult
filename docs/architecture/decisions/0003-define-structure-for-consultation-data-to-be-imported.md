# 3. Define structure for consultation data to be imported

Date: 2025-04-10

## Status

Accepted


## Context

The issue motivating this decision, and any context that influences or constrains the decision.

We have data for the consultation that we need to import into the app. 

There is "input data", that is, the transformed raw data - information on respondents, responses and questions.

For free-text questions only, there is also "output data", that is, the output of the AI pipeline (ThemeFinder).

Therefore, we need a consistent format for this data to enable consistent imports for different consultations.

We also need to consider the fact that some consultations are very large e.g. ~100k rows.


## Decision

We will store data in S3 (in the bucket specified by `AWS_BUCKET_NAME`) in a standard structure, separating inputs and outputs.

Data will be saved in JSON files, or JSONL (JSON lines) files for longer files to allow us to read it line-by-line.


The structure should be:

```
<consultation-name>/
    ├── raw_data/
    │   └── ....
    ├── inputs/
    │   ├── question_part_<id>/
    │   │   ├── responses.jsonl
    │   │   └── question_part.json
    │   ├──  question_part_<id>/
    │   │   ├── responses.jsonl
    │   │   └── question_part.json
    │   ├── ...
    │   ...
    └── outputs/
        ├── mapping/
        │   ├── <timestamp>/
        │   │   ├── question_part_<id>/
        │   │   │   ├── meta.json
        │   │   │   ├── themes.json
        │   │   │   ├── position.jsonl
        │   │   │   └── mapping.jsonl
        │   │   ├── question_part_<id>/
        │   │   ├── ...
        │   ...  
        └── sign_off/
```
with separate folders for each question_part (sub-question).

Schema for each of these are in `/consultation_analyser/consultations/import_schema/`. For the JSONL files, the schema represent each line of the file.


## Consequences

This provides a consistent way to structure the data, allowing us to create an import process that will work for all consultations.

Changes to the file format to use JSONL will make it easier for dealing with large consultations.
