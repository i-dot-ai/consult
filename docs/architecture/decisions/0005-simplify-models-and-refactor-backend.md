# 5. Simplify models and refactor backend

Date: 2025-06-16

## Status

Accepted

## Context

We currently have a unique window of opportunity to undertake a significant refactoring of our Django models. With no active users on the application, we can make breaking changes without impacting production usage or requiring complex migration strategies.

The original Django models were designed with a hyper-normalized structure that introduced unnecessary complexity. This over-normalization was based on anticipated requirements that never materialized in practice. The current model structure creates several pain points:

1. **Performance overhead**: Multiple table joins are required for common queries, impacting response times
2. **Development friction**: Simple features require complex ORM queries across many related tables
3. **Maintenance burden**: The intricate relationships between models make changes risky and time-consuming
4. **API complexity**: Frontend endpoints must aggregate data from numerous sources, leading to inefficient data fetching patterns

## Decision

We will simplify and partially denormalize the Django models while maintaining appropriate levels of normalization where it provides value. This refactoring will:

1. **Consolidate related models**: Merge tightly-coupled models that are always queried together
2. **Denormalize frequently-accessed data**: Store commonly-retrieved fields directly on primary models to reduce joins
3. **Simplify relationships**: Remove unnecessary many-to-many relationships and intermediate tables
4. **Streamline API endpoints**: Redesign endpoints to return pre-aggregated data efficiently

The refactoring scope includes:
- Core Django application models
- Data ingestion pipelines
- Evaluation application interfaces
- Dashboard frontend endpoints


## Consequences

### Positive Consequences

1. **Improved performance**: Fewer database joins will result in faster query execution and reduced latency
2. **Simpler codebase**: Developers can implement features with straightforward ORM queries
3. **Easier iteration**: Reduced model complexity makes future changes less risky and faster to implement
4. **Better API performance**: Frontend endpoints can retrieve data more efficiently
5. **Reduced cognitive load**: New developers can understand the data model more quickly

### Negative Consequences

1. **Migration complexity**: The refactoring would be hard to migrate and instead we may have to wipe prod db
2. **Temporary disruption**: All dependent systems must be updated simultaneously
