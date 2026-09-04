# 15. Dataset cards

Date: 2026-09-04

## Status

Accepted

## Context

We have numerous datasets from consultations, which are a mix of synthetic data generated
for evaluation, and real data from live consultations. These datasets vary in when they were
gathered, what they can be used for, and how long they can be retained. However, we don't have
a standard set of metadata fields that each dataset should be tagged with, or a system to record
and query this metadata.

## Decision

### Data Cards

We should use a simple JSON template to specify a "data card" that defines the metadata that each
dataset is required to be tagged with. The data card will have the following fields and hierarchy:

* Identity
    * dataset_id (stable unique ID)
    * name
    * description
    * owner (person or team)
    * created_at

* Provenance
    * source_type (user annotation / synthetic)
    * labeling_method (single human labeling / double human labeling / model-assisted)
    * transformations (normalization / dedupe / PII redaction / filtering)

* Permissions
    * contains_pii (yes / no)
    * allowed_uses (evaluation / fine-tuning)
    * sensitivity (public / internal)
    * retention_end_date (date)

* Usage boundaries
    * split_role (training / fine-tuning / eval / red-teaming / monitoring)

**NOTE**: we want to keep the balance between recording everything we need to use data in a compliant way,
and making the data cards as quick as possible to complete so that people actually fill them out.

### System of Record

We will use Langfuse as our system of record, passing the metadata JSON into calls to `Langfuse.create_dataset()`
via the `metadata` field. This will enable us to view and edit the metadata manually through the Langfuse portal,
or programatically through the Langfuse SDK. As a back-up, we should consider storing the JSON files in S3 too.

## Consequences

### Positive

1. We will remain compliant with our data usage agreements
2. We will have clear records of what data is being used to fine-tune and evaluate, preventing leakage

### Negative

1. Additional admin burden when ingesting data (but this can be minimised by using a standard template)
