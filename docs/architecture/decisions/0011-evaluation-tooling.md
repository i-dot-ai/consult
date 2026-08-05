# 11. Evaluation Tooling

Date: 2026-08-05

## Status

Accepted

## Context

There are three main driving forces for improved evaluation tooling within Consult:

- The model we use is nearing deprecation, so we need to find a suitable replacement
- We want to create a suitable evaluation suite for us to use to evaluate models on a rolling basis,
and for when a model gets deprecated in future
- We want to unify our evaluation capability across the team

To achieve these points, we need to research available tooling and methods, and settle on an approach
that will work for us now and in the future. Doing so would allow us as a team to have more
confidence in the models we have access to, and unlock more features for our various applications.

## Decision

Georgia has done some excellent work researching our various options. Following documentation created
and discussions had around evaluation, the outcome is:

- Use langfuse as the evaluation application as we already have it, but investigate other options, e.g. Laminar, if
needed
- Use pydantic-evals for LAJ (LLM-as-a-judge), with DeepEval if needed later
- Use Langfuse for storing evaluation datasets
- Use LiteLLM for the model provider
- Use this to try to get a consensus on which model provides an equal or improved result, aiming to switch before
October 2026
- Try get anonymised datasets from departments instead of using fully synthetic data for evaluations

## Consequences

- A plan to create an evaluation framework and the tooling used for it has been decided on
- The ability to switch model before October should be achievable
- Time will have to be dedicated to acquiring sufficient evaluation data to make a sound decision
- Dependent on outcome, application performance will have to be monitored and communicated
- New features, e.g. model select, should be more achievable