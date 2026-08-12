# Consult Runbook

Operational guide for responding to Consult alerts. This is a stub; add
sections as we work out the response steps for each alarm.

## Alerts

CloudWatch alarms notify the platform Slack channel via SNS, a Lambda, and the
`cloudwatch-slack-integration` module. Each alert links back here.

### RDS

Aurora PostgreSQL cluster (`consultations` DB). Alarms defined in
`terraform/rds.tf` via the shared `rds-alarms` module.

- **freeable_memory_low** / **database_connections_high**: TODO document triage.
- **cpu_high**, **read_latency_high** (p99), **write_latency_high** (p99),
  **aurora_replica_lag_high**: TODO document triage.

First checks: CloudWatch RDS metrics and Performance Insights (enabled outside
dev), recent deploys, and RQ job load (`/django-rq/`).

## Escalation

TODO: on-call rotation and escalation path.
