# 7. Consolidate job processing onto SQS

Date: 2026-03-30

## Status

Accepted

## Context

The consult data pipeline requires redesign to support the Data Setup project, Finalising Themes V2 project, and the tests we have defined for finding themes. Its current organic growth has created operational complexity that hinders local development, debugging, and maintenance.

The existing architecture is composed of two job systems plus an S3-based bridge:

- Redis Queue (RQ) handles database sync jobs.
- AWS Batch with Fargate runs finding themes and assigning themes.
- EventBridge rules detect batch completion and Lambda functions enqueue database sync back into RQ.
- S3 is used as the cross-system data store, meaning every pipeline run depends on S3 reads/writes.

This creates several problems:

- Dual processing system: independent failure domains across RQ, Batch, EventBridge, and Lambda.
- S3 as orchestration backbone: a separate sync step reads AI output from S3 and writes it back to the database.
- Per consultation processing: finding themes and assigning themes run at consultation scope, so a single failure forces a full rerun.
- No local development path: AWS Batch prevents end-to-end local pipeline execution.
- Two-pass theme assignment: users cannot review themes and see response assignments in one coherent pipeline run.

This decision is informed by the Data Pipeline Architecture Brief, Data Pipeline documentation, ADR 0006, and the Data Setup and Finalising Themes V2 project goals.

## Decision

We will move the new AI pipeline submission path to SQS while keeping the existing RQ system unchanged for current async work. Existing RQ continues to service ingest, clone, dummy-data, embedding creation, and import-of-batch-output jobs. Only the new find-themes / assign-themes pipeline submission path is moved to SQS, and the two systems will coexist during migration.

The decision includes:

- Replace AWS Batch, EventBridge, and Lambda for the pipeline path with an SQS-based job queue.
- Maintain the existing `default` RQ queue and current RQ workers for existing jobs.
- Add a new SQS queue for AI pipeline jobs and a dedicated SQS worker service with a larger task definition and longer timeout.
- Enqueue new AI pipeline jobs from Django to SQS.
- Use PostgreSQL as the single source of truth for pipeline reads and writes.
- Store snapshot and raw pipeline output in PostgreSQL instead of relying on S3; the DB owns run data and traceability.
- Process each question as an independent pipeline job, matching the Finalising Themes V2 question-by-question experience.
- Combine finding themes and assigning themes into a single per-question job, with carry-forward delta logic for unchanged, edited, and user-created themes.
- Introduce the `jobs` table to capture run metadata and make pipeline execution auditable.
- Extend the existing `Question.status` lifecycle with `finding_themes` and `assigning_themes`.

## Database Changes

### 5.1 Jobs

A new `jobs` table tracks each pipeline execution, recording one row per question per run.

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | UUID PK | no | Primary key |
| `question_id` | UUID FK → `Question` | no | Links the pipeline execution to a question |
| `type` | VARCHAR(16) | no | `candidate` or `final` |
| `status` | VARCHAR(16) | no | `queued`, `running`, `completed`, or `failed` |
| `external_id` | VARCHAR(64) | yes | Queue job ID (provider-agnostic) |
| `context` | JSONB | yes | Error messages, model versions, metrics, optional traceability data |
| `started_at` | TIMESTAMP | yes | When the worker picked up the job |
| `completed_at` | TIMESTAMP | yes | When the job finished |
| `created_at` | TIMESTAMP | no | Auto-generated timestamp |
| `modified_at` | TIMESTAMP | no | Auto-generated timestamp |

### 5.2 Existing Tables Changes

| Table | Change | Details |
| --- | --- | --- |
| `Question` | Add `finding_themes` and `assigning_themes` to the existing `status` field | Two new lifecycle values: `draft` → `configured` → `finding_themes` → `assigning_themes` → `finalising_themes` → `confirmed_themes` |
| `CandidateTheme` | Add `representative_responses` column | JSONField, nullable; list of response UUIDs that represent the most relevant responses for this theme in the review UI |

## Consequences

Positive consequences:

- Simpler architecture: a single queue system reduces cross-service failure points.
- Better local development: the pipeline can run locally against Redis and PostgreSQL.
- Fault isolation: failures are contained to individual questions rather than whole consultations.
- Faster feedback: per-question status allows the frontend to show progress and error states in real time.
- No S3 dependency: raw pipeline output and snapshots are stored in PostgreSQL rather than in S3.
- Better observability: the `jobs` table captures status, attempts, error details, timing, and token usage.

Negative consequences and risks:

- The new SQS pipeline worker becomes a scaling dependency; its ECS service must be sized and autoscaled carefully.
- A new ECS service and autoscaling policy are required for the `pipeline` queue.
- The migration is non-trivial: new tables and fields must be introduced without breaking existing Batch-based flows.
- Storing raw pipeline output in PostgreSQL requires schema design, retention policy, and careful indexing to avoid table bloat.

## Review

This architectural review confirms that the consolidated pipeline design is aligned with the project goals:

- It supports self-serve data setup by reading consultation data directly from PostgreSQL.
- It enables the Finalising Themes V2 experience through per-question jobs and explicit `Question.status` lifecycle tracking.
- It resolves the current two-pass theme assignment problem by producing candidate themes and response mappings in one combined run.
- It improves traceability by storing raw pipeline run data in PostgreSQL keyed by consultation/question/run.

The following areas still require validation during implementation:

- SQS worker autoscaling and queue-length monitoring for large pipeline workloads.
- Behaviour when pipeline output writes to PostgreSQL fail: the database remains authoritative, but observability and retry paths must be solid.
- Migration for existing consultations and selected themes that were created before the new pipeline metadata model was introduced.
- Coexistence during rollout: keep the current RQ/Batch path available and unchanged until the new SQS pipeline is fully validated.

## Related

- `docs/architecture/decisions/0006-database-redesign-for-self-serve-data-setup.md`
- Data Pipeline Architecture Brief
- Data Pipeline documentation
- [Data Pipeline Design](https://incubatorforartificialintelligence.atlassian.net/wiki/spaces/Consult/pages/147357714/Data+Pipeline+Design)
- Data Setup - Project Overview
- Finalising Themes V2 - Project Overview
- Defining tests for assessing Finding Themes
