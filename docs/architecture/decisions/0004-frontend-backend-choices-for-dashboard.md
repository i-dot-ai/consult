# 4. Frontend/backend choices for dashboard

Date: 2025-05-15

## Status

Accepted

## Context

We are considering options for the dashboard. With a lot of results (potentially over 100k) page loads take a long time when not paginated.

## Decision

We will assume that all users have JavaScript (there are limited users).

Have a minimal non-JS page (details to be decided).

Frontend will prepare and send query string with filters, pagination (page and page size), backend will apply these choices and return as JSON. 


## Consequences

There will not be a non-JavaScript version with full functionality.
