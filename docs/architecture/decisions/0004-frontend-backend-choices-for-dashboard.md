# 4. Frontend/backend choices for dashboard

Date: 2025-05-15

## Status

Accepted

## Context

We are considering options for the dashboard. With a lot of results (potentially over 100k) page loads take a long time when not paginated.

## Decision

We will assume that all users have JavaScript (there are limited users).

We will do all the filtering in the frontend. Keep the existing page as backup (though we don't need to do all the filtering in the non-JS page).

We will still paginate results in the backend, and the frontend will fetch these.


## Consequences

There will not be a non-JavaScript version with full functionality.
