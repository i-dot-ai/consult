# 10. Observability Improvements

Date: 2026-08-05

## Status

Accepted

## Context

For improved observability on the application, pipeline and infrastructure in the application,
we need to improve the logging throughout for each.

The intent of these improvements is to allow us to identify issues quicker in the future, and proactively fix issues
spotted by users, rather than rely on user reports.

## Decision

We will increase our logging capability throughout, use a standardised framework for logging and surface these logs.

Key decisions to enable that:

- We will increase the coverage of the current python logging package.
- Tracing IDs will be added where possible to enable log traces throughout the application.
- We will convert the logging package to use OTel format for logging.
- We will create an NPM package to increase logging surface to include the frontend.
- We will add relevant logging to the applications running in pipeline in batch, lambda and worker locations.
- We will increase the infrastructure alarms to include the pipeline, RDS and lambda and route these through slack.
- We will improve logging and tracing of LLM calls via Langfuse tracing improvements.

## Consequences

- Logs throughout will be interconnected where possible.
- Logs will follow a standardised pattern based on OTel.
- Changes will be implemented into the pip and npm packages to be used throughout i.ai.
- We will be able to spot more issues with the app before the users do.