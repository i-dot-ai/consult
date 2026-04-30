# 8. Per-question pipeline with DB as source of truth

Date: 2026-03-30

## Status

Accepted

## Context

The current consult pipeline processes each consultation as a unit and relies on S3 as a shared orchestration layer. That design adds complexity, reduces fault isolation, and makes local debugging difficult.

The Data Setup and Finalising Themes V2 work requires:

- a question-by-question workflow that fits the user experience of stepping through free-text questions one at a time
- a single source of truth for pipeline state and outputs
- better visibility into pipeline progress and failures
- the ability to retry or rerun individual questions without rerunning the whole consultation

The existing architecture is therefore being redesigned to move per-question processing onto a new pipeline, with PostgreSQL as the authoritative store and S3 removed from the critical path.

## Decision

We will adopt a per-question pipeline model with the database as the primary source of truth.

Key decisions:

- Process pipeline work at the level of individual questions instead of entire consultations.
- Store all pipeline read/write state in PostgreSQL, not S3, for critical path processing and traceability.
- Use the existing `Question.status` field and extend it with new pipeline lifecycle states.
- Record every pipeline execution in a dedicated `jobs` table.
- Persist intermediate pipeline metadata and annotations through the database, using existing candidate theme and response annotation structures where possible.
- Use the database to capture raw pipeline output, metrics, and metadata, rather than writing those artifacts to S3.
- Rate limit concurrent question processing to protect the backend, the LLM service, and downstream database writes.

### Per-question processing

Each free-text question is treated as a separate pipeline job. The pipeline should:

- read responses for the target question from PostgreSQL
- generate candidate themes and assign responses in the same job
- write pipeline outputs back to PostgreSQL in a transaction
- update `Question.status` to reflect the current stage

This allows:

- fault isolation for failed questions
- parallel processing across questions when capacity allows
- more granular UI progress reporting
- smaller retries and faster recovery

### DB as source of truth

PostgreSQL is the authoritative datastore for:

- question pipeline status
- pipeline run metadata
- candidate theme mappings
- response annotations
- raw pipeline output and metrics

S3 is removed from the critical path. If S3 is retained for off-line audit or archival purposes, it is strictly a secondary store and optional.

### Question lifecycle

A question lifecycle is stored on `Question.status` and moves through the following stages:

- `draft`
- `configured`
- `finding_themes`
- `assigning_themes`
- `finalising_themes`
- `confirmed_themes`
- `error`

This lifecycle supports the Finalising Themes V2 user journey and provides a stable boundary for retries and reprocessing.

### Jobs table

The `jobs` table tracks one execution per question per pipeline run.

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | UUID PK | no | Primary key |
| `question_id` | UUID FK → `Question` | no | Associates the job with a question |
| `type` | VARCHAR(16) | no | `candidate` or `final` |
| `status` | VARCHAR(16) | no | `queued`, `running`, `completed`, or `failed` |
| `external_id` | VARCHAR(64) | yes | Queue job ID (provider-agnostic) |
| `context` | JSONB | yes | Error messages, model versions, metrics, optional traceability data |
| `attempts` | integer | yes | Retry attempt count |
| `started_at` | TIMESTAMP | yes | When the worker picked up the job |
| `completed_at` | TIMESTAMP | yes | When the job finished |
| `parameters_json` | JSONB | yes | Pipeline inputs and configuration |
| `metrics_json` | JSONB | yes | Usage and performance metrics |
| `output_json` | JSONB | yes | Raw pipeline output or final payloads |

Using a dedicated `jobs` table makes the pipeline auditable, enables retries, and keeps run metadata available for debugging and reporting.

### Rate limiting strategy

The pipeline must avoid overloading downstream systems and the LLM API. This requires a rate limiting strategy for concurrent question jobs:

- limit the number of in-flight question jobs per consultation
- limit the total number of concurrent pipeline jobs across the service
- enforce backpressure via SQS queue visibility and worker concurrency settings
- use configurable thresholds so the rate limiting policy can be tuned in staging and production

This ensures that busy consultations do not monopolise compute, and that the system can degrade gracefully when the LLM or database is under pressure.

## Consequences

Positive consequences:

- simpler pipeline semantics: per-question jobs are smaller and easier to reason about
- better failure isolation and retry granularity
- more accurate progress tracking in the UI
- reduced coupling between pipeline orchestration and S3
- a single authoritative store for pipeline state and output

Negative consequences and risks:

- the database schema becomes more complex and must support additional pipeline run payloads
- raw pipeline output persisted in PostgreSQL will require retention and storage management
- concurrent question execution must be controlled carefully to avoid overwhelming the database or LLM
- migration of existing consultation data and pipeline state is required
- `CandidateTheme` requires a new nullable `representative_responses` JSONField for review UI support

## Review

This ADR defines a stronger alignment between the data setup user journey and the underlying pipeline architecture. By moving the pipeline to question-level granularity and storing state in PostgreSQL, we improve visibility, local debugging, and fault isolation.

The implementation needs to validate:

- that `Question.status` supports the expected UI workflow
- that `PipelineRun` captures enough metadata for debugging and metrics
- that per-question concurrency limits are effective in practice
- that existing consultations can be migrated without data loss or workflow disruption

## Related

- `docs/architecture/decisions/0006-database-redesign-for-self-serve-data-setup.md`
- `docs/architecture/decisions/0007-consolidate-job-processing-onto-sqs.md`
- [Data Pipeline Design](https://incubatorforartificialintelligence.atlassian.net/wiki/spaces/Consult/pages/147357714/Data+Pipeline+Design)
- Data Setup - Project Overview
- Finalising Themes V2 - Project Overview
