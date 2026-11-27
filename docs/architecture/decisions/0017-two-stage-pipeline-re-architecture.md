# 17. Two-stage pipeline re-architecture

Date: 2026-11-25

## Status

In Review

Partially supersedes [0003](0003-define-structure-for-consultation-data-to-be-imported.md): its S3 data contract
no longer applies to pipeline inputs and outputs once stage 1 is complete (see negative consequence 5).

## Context

From January 2027, up to six departments will run their own consultations on Consult without i.AI engineers
on hand. The current jobs pipeline was not built for that:

- Find themes and assign themes are split across the ECS worker (RQ), AWS Batch, S3, EventBridge and Lambda.
  S3 is the hand-off between them, so it is effectively the source of truth while a job is running.
- Each job processes every question in a consultation sequentially as one long job. Finding themes for our
  largest consultation took up to 16 hours, and a failure at any point means re-running the whole consultation.
- The pipeline handles about two jobs at once. A second large job can overload the workers.
- When a job fails, the consultation stays stuck until an engineer fixes it by hand.

The target for launch is four jobs running at once, with every failure visible and retryable.

The October 2026 spike into pipeline options compared five options. Two conclusions from it frame this decision:

- Patching the current pipeline as a final solution is ruled out, because it will not scale as more departments join.
- Temporal is where we want to end up, but moving the whole pipeline to it in one step carries too much
  time risk for the January roll-out, while we also have to keep a live service running.

## Decision

We will re-architect the pipeline in two stages. Stage 1 is the minimum needed to meet the roll-out deadline.
Stage 2 moves the pipeline to Temporal, and does not block roll-out.

### Stage 1: remove Batch and S3, and break down the jobs (target 2026-12-11)

1. **Run everything on the ECS worker.** Find themes and assign themes move off AWS Batch and into the backend
   as ordinary RQ worker jobs, triggered the same way as the existing jobs (for example set up). The job logic is
   preserved as far as possible in this step.
2. **The database is the only source of truth.** The jobs stop reading from and writing to S3, and consultation
   data is no longer exported to S3 after set up. Anything that was only held in S3 gets a home in the database.
   Jobs write to the database at regular intervals rather than only at the end, so current state is saved.
3. **Break the jobs into smaller chunks.** A consultation is no longer one long job. Find themes and assign
   themes run at least per question, so a failure costs one chunk rather than the whole consultation.
4. **Remove the Lambdas.** Slack notifications for completed and failed jobs are sent directly from the worker
   jobs, and all Lambdas are deleted.
5. **Size and scale the worker for the heavier load.** We will confirm the worker's resources and autoscaling
   are sufficient for work that previously ran in Batch, investigate scaling on RQ queue depth, and add a load
   test that any team member can run.

RQ stays as the queue for stage 1. We are deliberately not changing the queueing technology and the shape of
the jobs at the same time.

### Stage 2: replace RQ with Temporal (target 2027-01-22)

1. **Set up a Temporal server** in our AWS stack and locally, following the pattern already used by Minute.
2. **Establish one pattern first.** A foundational piece of work defines how a worker job runs as a Temporal
   activity or workflow, with tests. Every other job copies that pattern.
3. **Build the Temporal jobs in parallel, not as replacements.** The import, delete, clone, find-themes and
   assign-themes jobs each get a Temporal implementation alongside the existing RQ job, which stays in place
   and unchanged. Each Temporal job must be idempotent and unit tested.
4. **Cut over once.** A single final piece of work wires in the Temporal jobs and removes RQ from the pipeline.
   Until then, production keeps running on RQ.
5. **Configure Temporal for our expected load**, so that small consultations are not blocked by large ones and
   the worker autoscales on queue depth.

We considered rebuilding the workers on SQS with dead-letter queues in this stage, and pushing the move to
Temporal to a later milestone or project. We dropped this in favour of going to Temporal directly. Temporal is
where we want to end up, and an SQS implementation would be a lot of work that is then thrown away without
bringing us any closer to it. The changes in stage 1 reduce the gap to Temporal without much throwaway work.

### Out of scope

Job visibility for users and engineers is the third milestone of the project and is not covered by this ADR.

## Consequences

### Positive

1. The roll-out deadline depends only on stage 1, which changes where the jobs run and how they are split,
   but keeps the queue we already operate.
2. Stage 1 removes Batch, EventBridge, Lambda and the S3 data contract from the pipeline, so there is less
   infrastructure to run and one place to look for the state of a job.
3. A failure costs one chunk instead of a whole consultation, before Temporal arrives.
4. The smaller, database-backed jobs from stage 1 are what the Temporal activities in stage 2 are built from,
   so stage 1 is not throwaway work.
5. Building the Temporal jobs in parallel with a single cut-over means the live service is not affected until
   the new path is complete and tested.

### Negative

1. The batch jobs are handled twice: once to move them onto the worker and break them down, and again to move them
   to Temporal. However, the existing worker jobs are only changed once.
2. Between the two stages we still rely on RQ, which does not give us durable execution or automatic retries.
   A failed chunk is cheaper to re-run, but may still need an engineer.
3. During stage 2 there are two implementations of each job to keep in step until the cut-over.
4. Heavy jobs that used to be isolated in Batch now share the ECS worker with everything else, so worker sizing,
   autoscaling and the load test are required for stage 1 rather than optional.
5. The S3 data contract described in [ADR-0003](0003-define-structure-for-consultation-data-to-be-imported.md)
   no longer applies to pipeline inputs and outputs once stage 1 is complete.
