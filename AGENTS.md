# Consult Repository Guide

> **For AI coding assistants**: This document provides essential context about the Consult repository's architecture, intent, and organization.

## Pull Requests

Always use the PR template at `.github/PULL_REQUEST_TEMPLATE.md` when writing PR descriptions.

---

## Project Overview

**Consult** combines AI with human oversight to process public consultation responses at scale for UK government policy-making.

**Core workflow**:
1. Upload citizen responses to government consultations
2. AI automatically identifies themes across responses
3. Humans review, edit, and approve themes
4. AI assigns finalized themes to individual responses
5. Interactive dashboard for policy analysis

**Status**: Incubation project trialling across UK Civil Service  
**Repository**: `i-dot-ai/consult`

---

## Technology Stack

**Backend**: Python 3.12, Django 5.2.11, PostgreSQL with pgvector, Redis, Django RQ  
**Frontend**: Astro 5.16.6, Svelte, Tailwind CSS, TypeScript
**Infrastructure**: AWS ECS, AWS Batch, Lambda, S3, Terraform  
**AI Library**: `themefinder` 0.8.2 (theme discovery and assignment)  
**LLM**: Azure OpenAI (text-embedding-3-large for embeddings)

---

## Architecture

### High-Level Structure

```
Frontend (Astro/Svelte) ←→ Backend API (Django REST) ←→ PostgreSQL
                                      ↓
                        AWS Batch Jobs (Themefinder)
                                      ↓
                        S3 (data interchange)
                                      ↓
                        Lambda → RQ Jobs → Import results
```

### Project Structure

```
consult/
├── backend/                      # Django REST API
│   ├── consultations/            # Core domain models & views
│   ├── data_pipeline/            # Batch job orchestration & S3 sync
│   ├── authentication/           # JWT + OIDC auth
│   └── ingest/                   # Data import/deletion
│
├── frontend/                     # Astro + Svelte
│   └── src/
│       ├── components/           # Svelte components
│       ├── pages/                # Astro pages (routes)
│       └── middleware.ts         # Auth & security
│
├── pipeline-sign-off/            # AWS Batch: Find themes
├── pipeline-mapping/             # AWS Batch: Assign themes
├── lambda/                       # Event handlers (import results)
├── terraform/                    # Infrastructure as Code
└── docs/architecture/decisions/  # ADRs
```

---

## Core Domain Model

**Key entities** (see `backend/consultations/models.py`):

```
Consultation (title, stage, code)
  └─> Question (text, type: open/closed/demographic)
       ├─> Response (text, embedding[vector], search_vector)
       │    ├─> Respondent (demographics)
       │    └─> ResponseAnnotation (AI analysis: themes, sentiment)
       ├─> CandidateTheme (AI-generated, pre-approval)
       └─> SelectedTheme (human-approved, final)
```

**Key characteristics**:
- **UUIDs** as primary keys throughout
- **Denormalized response storage**: All response types in `Response.text` (see ADR-0006)
- **Vector embeddings**: 3072-dim pgvector for semantic search
- **Dual themes**: Separate CandidateTheme (AI) vs SelectedTheme (human-approved)
- **Audit trail**: Through model `ResponseAnnotationTheme` tracks AI vs human assignments

---

## Data Pipeline (Event-Driven)

### Consultation Stages

```
SETUP → FINDING_THEMES → FINALISING_THEMES → ASSIGNING_THEMES → ANALYSIS
```

### Pipeline Flow

**1. Setup** (`Consultation.Stage.SETUP`)
- Upload CSV/Excel → Parse → Load to PostgreSQL
- Generate embeddings for free-text responses
- Location: `backend/ingest/`, `backend/data_pipeline/jobs.py::import_consultation`

**2. Finding Themes** (`FINDING_THEMES`)
- Export data to S3 → AWS Batch job → Themefinder generates themes → S3
- EventBridge → Lambda → RQ job imports `CandidateTheme` records
- Location: `pipeline-sign-off/find_themes_script.py`, `lambda/import_candidate_themes/`

**3. Finalising Themes** (`FINALISING_THEMES`)
- Users review/edit candidate themes in UI
- Approve themes → create `SelectedTheme` records
- Location: `frontend/src/pages/consultations/[id]/questions/[qid]/themes/`

**4. Assigning Themes** (`ASSIGNING_THEMES`)
- Export selected themes to S3 → AWS Batch job → Assign themes to responses → S3
- EventBridge → Lambda → RQ job imports `ResponseAnnotation` records
- Location: `pipeline-mapping/assign_themes_script.py`, `lambda/import_response_annotations/`

**5. Analysis** (`ANALYSIS`)
- Dashboard shows theme distribution, filtered responses, sentiment
- Location: `frontend/src/pages/consultations/[id]/analysis/`

### S3 Data Contract

```
app_data/consultations/{code}/
├── inputs/
│   └── question_{id}/
│       ├── question.json
│       ├── responses.jsonl
│       └── themes.csv (for assign phase)
└── outputs/
    ├── find-themes/{timestamp}/
    │   └── question_{id}/candidate_themes.csv
    └── assign-themes/{timestamp}/
        └── question_{id}/response_annotations.jsonl
```

---

## Key Architectural Patterns

### 1. Event-Driven Pipeline
**Why**: Decouple batch processing, scale independently, fault-tolerant  
**How**: Django → AWS Batch → EventBridge → Lambda → RQ → PostgreSQL  
**Location**: `terraform/batch.tf`, `terraform/eventbridge.tf`

### 2. Denormalized Response Storage (ADR-0006)
**Why**: Simplify queries, flexible filtering, eliminate 4 tables  
**Tradeoff**: Consistency in app layer (not DB constraints)  
**Location**: `backend/consultations/models.py::Response`

### 3. Dual Theme Management
**Why**: Separate AI suggestions from human decisions, audit trail  
**Pattern**: `CandidateTheme` (AI) → User review → `SelectedTheme` (final)  
**Location**: `backend/consultations/models.py`

### 4. Through Models for Audit
**Why**: Track original AI assignments vs human edits  
**Pattern**: `ResponseAnnotationTheme` with `assigned_by` field + history  
**Location**: `backend/consultations/models.py::ResponseAnnotationTheme`

### 5. Staged Lifecycle
**Why**: Enforce workflow, prevent invalid operations  
**Pattern**: `Consultation.Stage` enum validates transitions  
**Location**: `backend/consultations/models.py::Consultation`

### 6. Semantic + Full-Text Search
**Why**: Find similar responses (embeddings) + keyword search (tsvector)  
**How**: `Response.embedding` (pgvector) + `Response.search_vector` (PostgreSQL)  
**Location**: `backend/consultations/models.py::Response`

---

## API Design

**Base URL**: `/api/`  
**Pattern**: Nested routes follow parent-child relationships  
**Auth**: JWT (local) or OIDC (deployed)

**Key endpoints** (see `backend/consultations/views.py`):
- `GET /consultations/` - List user's consultations
- `POST /consultations/{id}/start_find_themes/` - Trigger theme discovery
- `POST /consultations/{id}/questions/{qid}/confirm_themes/` - Finalize themes
- `POST /consultations/{id}/start_assign_themes/` - Trigger theme assignment
- `GET /consultations/{id}/responses/?question=X&demographics=Y` - Filtered responses

**OpenAPI schema**: `/api/schema/` (via drf-spectacular)

---

## Key Files & Locations

### Backend
- **Models**: `backend/consultations/models.py` (domain entities)
- **Views**: `backend/consultations/views.py` (API endpoints)
- **Serializers**: `backend/consultations/serializers/` (API serialization)
- **RQ Jobs**: `backend/data_pipeline/jobs.py` (async tasks)
- **S3 Sync**: `backend/data_pipeline/s3.py` (data interchange)
- **Batch Submit**: `backend/data_pipeline/batch.py` (AWS Batch orchestration)
- **Settings**: `backend/settings/` (base, local, production, test)

### Frontend
- **API Client**: `frontend/src/global/apiClient.ts` (HTTP wrapper)
- **Auth**: `frontend/src/middleware.ts` (JWT validation)
- **Types**: `frontend/src/global/types.ts` (TypeScript interfaces)
- **Pages**: `frontend/src/pages/` (file-based routing)

### Infrastructure
- **Terraform**: `terraform/` (AWS resources)
- **CI/CD**: `.github/workflows/` (deployment pipelines)

### Documentation
- **ADRs**: `docs/architecture/decisions/` (design decisions)
- **ERD**: `docs/erd.png` (database schema diagram)

---

## Development

### Quick Start
```bash
make dev          # Start all services (Postgres, Redis, Django, Astro)
make test         # Run all tests
make lint         # Run linters
```

**Local URLs**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Django Admin: http://localhost:8000/admin/
- RQ Dashboard: http://localhost:8000/django-rq/

### Testing
- **Backend**: `backend/tests/` (pytest, 35 test files)
- **Frontend**: `frontend/src/**/*.test.ts` (vitest, 248 test files)
- **E2E**: `e2e_tests/tests/` (Playwright)

### Key Commands
```bash
# Backend
python manage.py migrate          # apply DB migrations
python manage.py createsuperuser  # create admin user
python manage.py shell            # Django shell

# Frontend
npm run dev    # start dev server
npm run build  # production build
npm run test   # run vitest tests

# Infrastructure
cd terraform/ && terraform plan -var-file=dev.tfvars  # preview infra changes

# Linting & formatting (run before committing)
make check-python-code   # ruff lint + import sort (backend)
make format-python-code  # ruff fix + format auto-fix (backend)
cd frontend && npm run lint          # eslint check
cd frontend && npm run lint:fix      # eslint auto-fix
cd frontend && npm run typecheck     # svelte-check TypeScript
```

**Code quality tools**: Backend uses ruff (line length 100, Python 3.12). Frontend uses eslint + prettier + svelte-check. Avoid `any` in TypeScript — it bypasses type safety.

---

## Configuration

### Environment Variables
**Backend** (`.env` local, Secrets Manager deployed):
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_HOST` - Redis for RQ
- `AWS_BUCKET_NAME` - S3 bucket for data
- `OPENAI_API_KEY` - Azure OpenAI via LLM Gateway

**Frontend** (`.env`):
- `PUBLIC_API_URL` - Backend API URL

### Feature Flags
```python
# settings/base.py
FEATURE_FLAGS = {
    'ENABLE_EMBEDDINGS': env.bool('ENABLE_EMBEDDINGS', default=True),
    'ENABLE_BATCH_JOBS': env.bool('ENABLE_BATCH_JOBS', default=True),
}
```

---

## Security

- **Auth**: JWT + OIDC (AWS ALB handles auth in deployed envs)
- **Access Control**: Users only see consultations they're assigned to (M2M)
- **Secrets**: AWS Secrets Manager (DB creds, API keys)
- **Network**: ECS tasks in private subnets, ALB is public
- **Headers**: CSP, HSTS, X-Frame-Options (applied in middleware)

---

## Performance

- **Query Optimization**: `select_related`, `prefetch_related`, indexes
- **Pagination**: 100 items per page (DRF default)
- **Bulk Operations**: `bulk_create`, `bulk_update` for imports (batch size: 1000)
- **Caching**: Redis for query results
- **Vector Search**: HNSW index on `Response.embedding`

---

## Monitoring

- **Logs**: Structured logging (i-dot-ai-utilities), CloudWatch
- **Errors**: Sentry (backend + frontend)
- **Metrics**: CloudWatch (ECS, RDS, Batch)
- **Health**: `/api/health/` (DB, Redis, S3 connectivity)
- **RQ Jobs**: `/django-rq/` dashboard

---

## Common Issues

**Embeddings not generating**: Set `ENVIRONMENT=deployed` locally (only generated in deployed envs by default)  
**Batch job stuck**: Check Batch compute environment capacity, ECS task role permissions  
**RQ timeout**: Increase timeout in `@job("default", timeout=SECONDS)` decorator  
**403 on API**: Ensure user assigned to consultation, valid JWT token  

---

## Architecture Decision Records

**Location**: `docs/architecture/decisions/`

Key ADRs:
- **ADR-0002**: Database design for consultation data and pipeline outputs
- **ADR-0003**: Data import structure (JSONL, CSV formats)
- **ADR-0004**: Frontend/backend separation (Astro + Django REST)
- **ADR-0006**: Denormalized response storage (single Response.text field)

---

## Glossary

- **Consultation**: Government consultation with questions and responses
- **Response**: Citizen's answer to a question
- **Respondent**: Citizen who submitted responses
- **CandidateTheme**: AI-generated theme (pre-approval)
- **SelectedTheme**: Human-approved theme (final)
- **ResponseAnnotation**: AI analysis (themes, sentiment, evidence)
- **Stage**: Consultation lifecycle phase (SETUP, FINDING_THEMES, etc.)
- **Embedding**: 3072-dim vector representation of text
- **RQ**: Redis Queue (async jobs)
- **Batch Job**: Long-running AWS Batch process (find/assign themes)

---

## Resources

- **README**: `/README.md` - Setup instructions
- **ADRs**: `/docs/architecture/decisions/` - Design decisions
- **ERD**: `/docs/erd.png` - Database diagram
- **OpenAPI**: `/api/schema/` - API docs (when running)

---

**Status**: Incubation project (v0.8.2)  
**Maintained By**: i-dot-ai (Cabinet Office, UK Government)  
**License**: MIT (Crown Copyright)
