# 7. Separate app and infrastructure release workflows

Date: 2026-05-26

## Status

Accepted

## Context

The previous release setup had two workflows:

- **`release-infra`** — deployed infrastructure via Terraform and built Docker images, combining both concerns in a single workflow
- **`release-prod`** — a separate workflow for prod-only deployments, duplicating much of the logic in `release-infra`

This caused several problems:

- Every deployment, regardless of what changed, rebuilt and redeployed all container services together. There was no way to deploy just the backend without also deploying the frontend, or vice versa.
- `release-prod` was largely a copy of `release-infra` with the environment hardcoded to `prod`, creating drift risk and maintenance overhead.
- The `workflow_dispatch` input in `release-prod` accepted a `tag` parameter but silently ignored it, always checking out the last release tag — making the input misleading.
- Infrastructure and application deployments could not be triggered or rolled back independently.

## Decision

We replaced `release-infra` + `release-prod` with two complementary workflows:

- **`release-app`** — responsible solely for building Docker images and deploying container services to ECS. It compares each service's current git SHA against the image tag stored in SSM Parameter Store and only builds and deploys services that have changed. Services are deployed individually via `terraform apply -target`, so a frontend change does not trigger a backend redeployment.

- **`release-infra`** — responsible solely for infrastructure changes (Terraform) and Lambda functions. It no longer builds or pushes Docker images. On `workflow_run` triggers (merge to main), it checks whether Terraform or Lambda files have actually changed and skips the deployment if neither has.

Both workflows share the same trigger structure (tag push for dev, `workflow_run` on main for preprod, GitHub Release for prod, and `workflow_dispatch` for manual deploys). Both validate that manual prod deployments reference a published GitHub Release rather than an arbitrary git ref.

The mapping from service name to Terraform module(s) is defined in `.github/service-config.json`, making it straightforward to add new services without modifying the workflow itself.

Documentation of the new release workflows can be viewed [here](../../release-workflows.md).

## Consequences

- Container services can be deployed independently. A change to the frontend no longer triggers a backend image build or ECS task update.
- Infrastructure and application deployments are decoupled. A Terraform change can be applied without touching container images, and vice versa.
- The prod deployment route is consolidated — `release-prod` is deleted and prod is handled by the same workflows as other environments, removing the duplication and drift risk.
- Adding a new container service requires adding an entry to `.github/service-config.json` and a corresponding Terraform module; no workflow changes are needed.
- The first deployment of a new service is handled gracefully: if the SSM parameter does not yet exist, the service is treated as changed and deployed.
