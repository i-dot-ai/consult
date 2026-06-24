# Campaign Response Experiment

Tests whether campaign responses (near-duplicate submissions, e.g. from a
campaign template) skew AI theme discovery, by comparing themes found on
datasets with different campaign/non-campaign ratios against two ground
truth datasets: one pure campaign, one pure non-campaign.

Steps are **not** meant to be run end-to-end unattended — several steps
require manual interaction with the Consult app in between script runs.

## Configuration

Set these once before starting:

| Variable | Meaning |
|---|---|
| `DATA_DIR` | Local directory holding all experiment data (GT dirs and test dataset dirs live here) |
| `GT1_NAME` | Name of the pure-campaign ground truth dataset (subdirectory of `DATA_DIR`) |
| `GT2_NAME` | Name of the pure-non-campaign ground truth dataset (subdirectory of `DATA_DIR`) |
| `CONSULTATION_CODE` | Consultation code as it appears in S3, e.g. `dwp_7_ratio_1_4_campaign_vs_non`. Set per-dataset when pulling results |
| `ORIGINAL_INPUTS_DIR` | Directory containing the original consultation inputs exported from Consult (should contain `question_part_*` subdirectories with `responses.jsonl`) |
| `NUM_RUNS` | Number of `find_themes` runs to collect per dataset, for measuring run-to-run variation (e.g. 5) |

## Step 1 — Prepare datasets

Run `find_duplicate_responses.py` once per dataset you want to create:

```bash
python find_duplicate_responses.py "$ORIGINAL_INPUTS_DIR" "$DATA_DIR/<dataset_name>"
```

It's interactive: it shows duplicate clusters found in the responses (groups
of near-identical text), and asks you to choose:
- which cluster represents the campaign responses
- whether to also include the non-cluster (genuine) responses
- the multiplier for how many campaign responses to include, relative to
  the number of non-cluster responses

Run this once for each dataset you need, e.g.:
- **GT1** (campaign only): `include_non_cluster=n`, `multiplier=1`
- **GT2** (non-campaign only): skip the cluster, include only non-cluster responses
- **Mixed test datasets** at various ratios: `include_non_cluster=y`,
  `multiplier=1,2,4...`

Output lands in `<output_dir>/inputs/question_part_*/responses.jsonl`
(with `question.json` copied alongside), ready to be uploaded to Consult.

## Step 2 — Generate demographic data

Consult requires demographic data alongside responses at upload time. Run
this once per dataset created in Step 1:

```bash
python generate_demographic_data.py "$DATA_DIR/<dataset_name>/inputs" "$DATA_DIR/<dataset_name>/demographics.jsonl"
```

This scans the `inputs/` directory recursively for `responses.jsonl` files
and writes a JSONL file with fixed demographic values for every
`themefinder_id` found.

## Step 3 — In Consult: upload each dataset and run find themes

For each dataset directory created above:

1. Create a new consultation in the Consult app (or reuse one).
2. Upload the dataset: use the `inputs/` directory produced by Step 1
   (`responses.jsonl` + `question.json` per question) alongside
   `demographics.jsonl`. The consultation moves to `SETUP` stage once
   upload and embedding generation complete.
3. Trigger find_themes: `POST /api/consultations/<id>/start_find_themes/`
   (or use the UI). The consultation moves to `FINDING_THEMES`, then to
   `FINALISING_THEMES` when the Batch job completes.
4. Pull the outputs (Step 4 below).
5. To get another run: reset the consultation stage back to `SETUP` via
   Django admin (Consultations → change stage field), then repeat from
   step 3. Each re-run writes a new timestamped output to S3.

You need `NUM_RUNS` completed `find_themes` jobs per dataset before
continuing to Step 5.

## Step 4 — Pull S3 outputs

Run once after each `find_themes` job completes in Consult. Auto-increments
the run number (`run_1`, `run_2`, ...) within the dataset directory. Set
`CONSULTATION_CODE` to match the S3 key for the consultation you just ran:

```bash
python pull_s3_outputs.py "$CONSULTATION_CODE" "$DATA_DIR/<dataset_name>" --date "<YYYY-MM-DD>"
```

`--date` defaults to today and should match the date of the `find_themes`
run on S3. Repeat this `NUM_RUNS` times per dataset (once per completed
Consult pipeline run from Step 3).

## Step 5 — Sanity check: theme count variation

Compare how many themes were generated across runs and datasets, to confirm
you have enough runs and spot outliers before analysis. A high stddev
relative to the mean suggests the pipeline is unstable for that dataset:

```bash
python compare_theme_counts.py "$DATA_DIR"
```

Prints a per-question table of mean/stddev theme counts across runs, for
every dataset found under `DATA_DIR`. If a dataset already has a
`consensus/` ground truth built (Step 6), its theme count is shown in a
separate `Consensus` column and excluded from the mean/stddev.

## Step 6 — Build consensus ground truths

Consolidates all themes from all runs of each GT dataset into a single
deduplicated consensus theme set via an LLM call. Only needed if you want to
use a consensus GT rather than a single run — skip this step and pass
`--run <n>` to `analyse_theme_similarity.py` instead if you prefer to
analyse run-by-run:

```bash
python build_consensus_gt.py "$DATA_DIR/$GT1_NAME"
python build_consensus_gt.py "$DATA_DIR/$GT2_NAME"
```

Writes to `<gt_dir>/consensus/question_part_*/clustered_themes.json`.

If you're unsure what `--distance-threshold` to use, run
`sweep_consensus_params.py --llm-as-judge` instead: it sweeps every
candidate distance threshold, uses an LLM to strip outlier themes out of
each resulting cluster, rechecks `min_coverage` on what's left, then picks
the threshold with the most surviving clusters and writes the consensus
itself (same output path as above), e.g.:

```bash
python sweep_consensus_params.py "$DATA_DIR/$GT1_NAME" --llm-as-judge \
    --distance-thresholds 0.05,0.10,0.15,0.20,0.25 --min-coverages 0.5
```

## Step 7 — Analyse

Compares each test dataset's themes against the two GT clusters. Each theme
is assigned to GT1, GT2, or 'both' via normalised centroid distance and
k-NN. Per-dataset detail is written to `$DATA_DIR/analysis_logs/`.

GTs are always loaded from their `consensus/` subdirectory. Test datasets
are run across all `run_*` subdirectories; results are aggregated as
mean±std **theme counts** (converted back from proportions using each
dataset's mean theme count per run), so they're directly comparable to the
number of themes in each GT's consensus:

```bash
python analyse_theme_similarity.py "$DATA_DIR" "$GT1_NAME" "$GT2_NAME"
```

Optionally restrict to a specific test subdirectory:

```bash
python analyse_theme_similarity.py "$DATA_DIR" "$GT1_NAME" "$GT2_NAME" <test_subdir>
```

For each question, the number of themes in each GT's consensus is printed
first, followed by two tables:
- the exclusive table (`Norm/kNN→GT1`, `Norm/kNN→both`, `Norm/kNN→GT2`) —
  each theme counted in exactly one column
- an inclusive table (`Norm/kNN→GT1(+both)`, `Norm/kNN→GT2(+both)`,
  `Norm/kNN overlap`) — themes classed as 'both' are folded into each
  overlapping group, so the two group columns compare directly against the
  GT1/GT2 consensus counts printed above

Useful flags:
- `--knn-num-neighbours` (default 5): k for k-NN classification
- `--norm-both-threshold` (default 0.9): how close (as a ratio of the two
  normalised centroid distances) a theme's distances to GT1/GT2 must be
  before it's classed as ambiguous ('both') rather than assigned to one
  group
- `--dataset-order`: comma-separated dataset numbers (matched against the
  first integer in each dataset directory name) giving the left-to-right
  order for chart x-axes, e.g. `--dataset-order 4,10,8,9,3,5,6,7`. Datasets
  not listed fall back to natural sort order (`dwp_9` before `dwp_10`),
  after any listed ones

A Plotly chart is also written per question to
`$DATA_DIR/charts/question_part_<N>.html`, plotting the inclusive kNN theme
counts per dataset (mean±std) against horizontal reference lines for each
GT's consensus size — a quick visual check of which dataset ratios pull
closest to each ground truth.
