# 14. Sentry vs Logging for Exceptions

Date: 2026-09-09

## Status

In Review

## Context

Sentry captures any uncaught exception in the system, but there are ways to include custom events into sentry exceptions
with function calls. Following a discussion with the team we have reached a consensus on what to do with exceptions.

## Decision

Following a conversation in slack, it was decided that the observability stack will be able to surface excessive caught exceptions
to the team, so pushing everything into sentry is duplicated traces, and extra noise.

To achieve the desired outcome, we will remove the functions used to manually push events into sentry that bypass the sentry filter,
and remove the calls to this function throughout the code.

## Consequences

- Sentry will only capture uncaught exceptions
- Caught exceptions will continue to get logged into the observability stack
- When the platform log collector is fully functional, this will enable us to build a dashboard and alerting for uncaught and caught exceptions