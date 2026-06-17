# Release Workflows

There are two release workflows: `release-app` and `release-infra`. They are independent: application and infrastructure can be deployed separately. On merges to `main` they are orchestrated by `deploy-main` (see [Auto-deploy on merge to main](#auto-deploy-on-merge-to-main)).

## Triggers

| Event | Environment | Notes |
|---|---|---|
| Push to `release-ENV-**` tag | dev or preprod | e.g. `release-dev-1.0.0` |
| Merge to `main` (via `deploy-main`) | preprod → prod | Runs the full CI suite, then deploys preprod, then prod only if preprod succeeds |
| GitHub Release published | prod | Still available; deploys a specific tagged release to prod |
| `workflow_dispatch` | dev / preprod / prod | Manual trigger; prod requires the tag to be a published GitHub Release |

The release-tag guard in `release-app`/`release-infra` only applies to manual dispatches; the `workflow_call` path from `deploy-main` bypasses it, with the full CI suite acting as the gate instead.

On merge to main, `deploy-main` calls each release workflow with an explicit `environment`. Each still filters internally:
* `release-app` skips individual services whose git SHA matches what is already deployed, so only services with code changes are built and redeployed.
* `release-infra` skips the entire deployment if neither `terraform/` nor `lambda/` has changed.

## Auto-deploy on merge to main

`deploy-main` (`.github/workflows/deploy-main.yml`) is the entrypoint for every push to `main`. It enforces that nothing reaches an environment until the full test suite passes, and that prod is only reached after preprod deploys cleanly:

```
push to main
  ├─ backend-ci ─┐
  ├─ frontend-ci ┼─ (all must pass)
  └─ e2e-tests ──┘
        └─ preprod: release-infra → release-app
              └─ (success) prod: release-infra → release-app
```

* **Test gate**: `backend-ci`, `frontend-ci` and `e2e-tests` are invoked via `workflow_call`. When called this way their path filters do not apply, so each suite runs in full regardless of which files changed. If any fails, no deploy runs.
* **Infra before app**: within each environment, `release-infra` runs before `release-app` so infrastructure prerequisites (new env vars, IAM permissions, Terraform-run migrations) are in place before the new images roll out.
* **preprod gates prod**: `prod-infra` depends on `preprod-app` succeeding. A failed preprod deploy stops the pipeline before prod is touched.
* **No overlapping prod deploys**: a `concurrency` group serialises runs so rapid successive merges don't race each other to prod.

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

On **merge to main**, `deploy-main` already enforces this: within each environment it runs `release-infra` before `release-app`, so no manual sequencing is needed.

The **GitHub Release** trigger, by contrast, starts both workflows at the same time. When an infrastructure change is a prerequisite for the app, it is safest to trigger `release-infra` first via `workflow_dispatch` and wait for it to complete before triggering `release-app`.

## Deploying to prod

The standard route is to publish a GitHub Release on GitHub — this triggers both `release-app` and `release-infra` automatically.

Manual (`workflow_dispatch`) deployment to prod is available as an emergency fallback but requires the tag input to reference a published GitHub Release. Arbitrary SHAs or branch names are rejected.

## Rollback

Because every merge to `main` auto-deploys to prod, rolling back means getting `main` back to a known-good state and letting the pipeline redeploy it. The per-service SHA filtering means only the services that actually changed are rebuilt and rolled back.

### Preferred: revert the offending change

Revert the bad commit on `main` and let it flow through the normal pipeline:

1. Open a revert PR (`git revert <sha>`, or the "Revert" button on the merged PR).
2. Merge it to `main`. `deploy-main` runs the full CI gate, then deploys preprod and prod just like any other merge.
3. Confirm the Slack notification reports the expected SHA, and check `/api/health/`.

This is the cleanest path because it keeps `main` and prod in sync. Any other rollback that does not also revert `main` is temporary: the next merge re-deploys the broken code, and the SHA-based filter treats the reverted-to state as "already deployed", so it will not redeploy on its own.

### Emergency fast path: roll back the deployed artifact (no rebuild)

When prod is actively broken and you cannot wait for CI plus a deploy, point the broken service back at its previous artifact. The previous image is almost always still in ECR (images are tagged by commit SHA), so no rebuild is needed.

#### 1. Identify which service broke

A single "deploy" is actually several independent services, each built and rolled out separately. Work out which one is at fault before touching anything; the others are fine and should be left alone.

Names derive from `var.name = ${local.name}-<service>`, where `local.name = i-dot-ai-<env>-consult` (`terraform/ecs.tf`, `terraform/data.tf:39`). The shared modules then suffix it:

- ECS module: **service** `${var.name}-ecs-service`, **task definition** `${var.name}-task`
- Batch module: **job definition** `${var.name}-<platform>-batch-job-definition`

(The `i-dot-ai-prod-consult-task` / `…-consultations-*` entries you may also see are legacy/other stacks, not part of this pipeline.)

The ECS services run on the shared platform cluster `i-dot-ai-<env>-ecs-cluster` (e.g. `i-dot-ai-prod-ecs-cluster` for prod). Consult does not have its own cluster; it pulls it from platform remote state (`terraform/ecs.tf:42`). Other projects' services are listed alongside consult's in the same cluster.

| Service (in `service-config.json`) | Deployed as | AWS resource name | What it runs |
|---|---|---|---|
| `backend` | ECS service | `i-dot-ai-prod-consult-backend-ecs-service` (task def `…-backend-task`) | Django REST API |
| `backend` | ECS service | `i-dot-ai-prod-consult-worker-ecs-service` (task def `…-worker-task`) | RQ worker (shares the backend image + SSM tag) |
| `frontend` | ECS service | `i-dot-ai-prod-consult-frontend-ecs-service` (task def `…-frontend-task`) | Astro/Svelte web app |
| `pipeline-mapping` | AWS Batch job definition | `i-dot-ai-prod-consult-mapping-FARGATE-batch-job-definition` | Theme assignment batch job |
| `pipeline-sign-off` | AWS Batch job definition | `i-dot-ai-prod-consult-sign-off-FARGATE-batch-job-definition` | Theme discovery batch job |

How to narrow it down:

- **Check what actually deployed.** `release-app`'s `filter-services` step logs which services it built and redeployed; only those changed. If only `frontend` was redeployed, only `frontend` can be the regression.
- **Match the symptom to the service:**
  - Web UI / page errors → `frontend`
  - API 5xx, `/api/health/` failures, auth/data errors → `backend`
  - Stuck/failed RQ jobs (imports, embeddings) → `worker`
  - Theme discovery failures → `pipeline-sign-off`
  - Theme assignment failures → `pipeline-mapping`
- **Note `backend` ⇒ two ECS services.** `backend` and `worker` are built from the same image and share one SSM image-tag, so a bad backend image affects both. Roll back **both** the `-backend` and `-worker` services together.

#### 2. Roll back that service

**ECS services (`backend`, `worker`, `frontend`):** point the service back at the previous task-definition revision:

In the AWS console:

1. Go to **ECS → Clusters → `i-dot-ai-<env>-ecs-cluster`** (e.g. `i-dot-ai-prod-ecs-cluster` for prod; the shared platform cluster, see above).
2. Open the **Services** tab and select the affected service (e.g. `i-dot-ai-prod-consult-frontend-ecs-service`, listed alongside other projects' services).
3. Click **Update service**, select the prior task-definition revision, and tick **Force new deployment**.
4. Click **Update**.

If `backend` is at fault, repeat for **both** `…-backend` and `…-worker`.

**Batch jobs (`pipeline-mapping`, `pipeline-sign-off`):** there is no long-running service to revert; the job definition is read when the next batch job is submitted. Either:

- register/select the previous job-definition revision (which points at the previous image), or
- simply hold off triggering new find/assign-themes runs until the revert lands.

In-flight batch jobs are unaffected by a code revert.

This is out of band: the image tag in SSM/Terraform still references the bad version for every rolled-back service, so follow up immediately with the revert above or the next merge will reintroduce it.

### Database migrations

Code rollbacks do **not** roll back database migrations. If the bad release applied a migration, check whether it is backwards-compatible with the version you are rolling back to. If it is not, you must also reverse the migration (or roll forward with a fix), because redeploying older app code against a newer schema can fail. Prefer backwards-compatible migrations to keep rollback safe.

## Deployment status

The GitHub **Environment** badge (`dev` / `preprod` / `prod`) can show green before the application is actually serving the new code (the infra deploy greens the shared Environment while app containers are still rolling out). To confirm a deploy has actually completed, treat the `deploy-containers` job (not the Environment badge) as the signal:

- Watch the `deploy-containers` job finish in the run, and/or
- Check the running image tag in ECS/SSM matches the deployed commit SHA, then
- Hit `/api/health/`.
