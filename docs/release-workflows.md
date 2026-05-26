# Release Workflows

There are two release workflows: `release-app` and `release-infra`. They are independent — application and infrastructure can be deployed separately.

## Triggers

| Event | Environment | Notes |
|---|---|---|
| Push to `release-ENV-**` tag | dev or preprod | e.g. `release-dev-1.0.0` |
| Merge to `main` (via `workflow_run` on build) | preprod | Only runs if the build workflow succeeded; Filters for changes to relevant code ** |
| GitHub Release published | prod | The standard prod release route |
| `workflow_dispatch` | dev / preprod / prod | Manual trigger; prod requires the tag to be a published GitHub Release |

**Merges to main trigger both workflows, but each filters internally:
* `release-app` always runs, but skips individual services whose git SHA matches what is already deployed — only services with code changes are built and redeployed.
* `release-infra` skips the entire deployment if neither `terraform/` nor `lambda/` has changed.

## release-app

Builds Docker images for changed container services and deploys them to ECS.

### What it does

1. **set-vars** — determines the target environment and computes a per-service git SHA (the SHA of the last commit that touched each service directory)
2. **filter-services** — compares each service's computed SHA against the image tag currently stored in SSM Parameter Store; only services whose SHA has changed proceed
3. **build-images** — builds and pushes a Docker image for each changed service
4. **update-ssm-image-tags** — writes the new image tag to SSM so Terraform can read it
5. **deploy-containers** — runs `terraform apply -target=<module>` for each changed service's Terraform module

### Services and their Terraform modules

Defined in `.github/service-config.json`:

| Service | Terraform modules |
|---|---|
| `backend` | `module.backend`, `module.worker` |
| `frontend` | `module.frontend` |
| `pipeline-mapping` | `module.batch_job_mapping` |
| `pipeline-sign-off` | `module.batch_job_sign_off` |

Only services with changed image tags are built and deployed — if nothing in a service directory has changed since the last deploy, that service is skipped entirely.

---

## release-infra

Deploys infrastructure changes via Terraform and builds/deploys Lambda functions. Does not build container images.

### What it does

1. **set-vars** — determines the target environment and whether a deploy is needed
2. **build-lambdas** — builds Lambda artifacts (runs when Lambda files changed, or on any explicit trigger)
3. **build-infra** — runs `terraform apply` for the full infrastructure

---

## Adding a new container service

1. Add the service directory (e.g. `myservice/`) with its `Dockerfile`
2. Add an entry to `.github/service-config.json` mapping the service name to its Terraform module(s):
   ```json
   "myservice": ["module.myservice"]
   ```
3. Add the corresponding Terraform module in `terraform/`
4. `release-infra` must run successfully first — Terraform creates the SSM parameter for the service's image tag (along with the ECS service and supporting infrastructure) before `release-app` can read and update it
5. Once infra is deployed, `release-app` will build and deploy the container image for the new service

## Changes to an existing container service

For routine application code changes (no infrastructure changes required), running `release-app` alone is sufficient. It will build a new image for any service whose code has changed and redeploy it.

`release-infra` should also be run first if the change requires any supporting infrastructure updates, such as:
- New or changed environment variables provisioned via Terraform
- New IAM permissions
- Changes to ECS task definition resources (CPU, memory, etc.)

## Making infrastructure changes

Edit files under `terraform/` and either:
- Merge to `main` — `release-infra` will detect the Terraform changes and deploy to preprod automatically
- Push a `release-dev-**` tag to deploy to dev first
- Publish a GitHub Release to deploy to prod

For changes that only affect infrastructure (no application code change), `release-app` will skip all services since no image tags will have changed.

## Ordering

`release-infra` and `release-app` are independent and can run in parallel. However, if an infrastructure change is a prerequisite for a new version of the application (e.g. a new environment variable, IAM permission, or database migration run via Terraform), `release-infra` must complete successfully before `release-app` is triggered.

For automated triggers (GitHub Release, merge to main) both workflows start at the same time, so in these cases it is safest to trigger `release-infra` first and wait for it to complete before triggering `release-app` manually via `workflow_dispatch`.

## Deploying to prod

The standard route is to publish a GitHub Release on GitHub — this triggers both `release-app` and `release-infra` automatically.

Manual (`workflow_dispatch`) deployment to prod is available as an emergency fallback but requires the tag input to reference a published GitHub Release. Arbitrary SHAs or branch names are rejected.
