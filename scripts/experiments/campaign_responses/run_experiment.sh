#!/usr/bin/env bash
# Campaign Response Experiment Workflow
# =====================================
# Tests whether campaign responses skew theme discovery, by comparing themes
# found on datasets with different campaign/non-campaign ratios against two
# ground truth datasets (pure campaign and pure non-campaign).
#
# Usage: edit the variables in the CONFIG section, then run each step manually.
# Steps are NOT meant to be run end-to-end unattended — Consult app interactions
# are required between several steps.

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── CONFIG ──────────────────────────────────────────────────────────────────

# Directory holding all local experiment data (GT dirs and test dataset dirs live here)
DATA_DIR="/path/to/experiment/data"

# Names of the two ground truth datasets (subdirectories of DATA_DIR)
GT1_NAME="campaign_only"       # pure campaign responses
GT2_NAME="non_campaign_only"   # pure non-campaign responses

# Consultation code as it appears in S3 (e.g. dwp_7_ratio_1_4_campaign_vs_non)
# Used by pull_s3_outputs.py — set per-dataset when pulling results
CONSULTATION_CODE="<consultation_code_on_s3>"

# Directory containing the original consultation inputs exported from Consult
# (should contain question_part_* subdirectories with responses.jsonl)
ORIGINAL_INPUTS_DIR="$DATA_DIR/original_inputs"

# Number of find_themes runs to collect per dataset (for measuring variation)
NUM_RUNS=5

# ─── STEP 1: PREPARE DATASETS ────────────────────────────────────────────────
# Run find_duplicate_responses.py once per dataset you want to create.
# Interactive: it shows duplicate clusters found in the responses, you pick
# which cluster represents campaign responses, whether to include non-cluster
# (genuine) responses, and the ratio of campaign to non-campaign.
#
# Run this once for each experimental dataset, e.g.:
#   - GT1: campaign only (include_non_cluster=n, multiplier=1)
#   - GT2: non-campaign only (include_non_cluster=y, multiplier=0 equivalent — skip cluster)
#   - Mixed datasets at various ratios (include_non_cluster=y, multiplier=1,2,4...)
#
# Output lands in <output_dir>/inputs/question_part_*/responses.jsonl
# ready to be uploaded to Consult.

python "$SCRIPTS_DIR/find_duplicate_responses.py" \
    "$ORIGINAL_INPUTS_DIR" \
    "$DATA_DIR/$CONSULTATION_CODE"

# Repeat for GT2 and each test dataset:
# python "$SCRIPTS_DIR/find_duplicate_responses.py" "$ORIGINAL_INPUTS_DIR" "$DATA_DIR/$GT2_NAME"
# python "$SCRIPTS_DIR/find_duplicate_responses.py" "$ORIGINAL_INPUTS_DIR" "$DATA_DIR/ratio_1_1"
# python "$SCRIPTS_DIR/find_duplicate_responses.py" "$ORIGINAL_INPUTS_DIR" "$DATA_DIR/ratio_1_4"
# ...

# ─── STEP 2: GENERATE DEMOGRAPHIC DATA ───────────────────────────────────────
# Consult requires demographic data alongside responses at upload time.
# This generates a JSONL file with fixed demographic values for every
# themefinder_id in the dataset — run once per dataset you created above.

python "$SCRIPTS_DIR/generate_demographic_data.py" \
    "$DATA_DIR/$GT1_NAME/inputs" \
    "$DATA_DIR/$GT1_NAME/demographics.jsonl"

# Repeat for GT2 and each test dataset.

# ─── IN CONSULT: UPLOAD EACH DATASET AND RUN FIND THEMES ─────────────────────
# For each dataset directory created above:
#
#   1. Create a new consultation in the Consult app (or reuse one — see note below).
#   2. Upload the dataset: use the inputs/ directory produced by step 1
#      (responses.jsonl + question.json per question) alongside demographics.jsonl.
#      The consultation moves to SETUP stage once upload and embedding generation complete.
#   3. Trigger find_themes: POST /api/consultations/<id>/start_find_themes/
#      (or use the UI). The consultation moves to FINDING_THEMES, then to
#      FINALISING_THEMES when the Batch job completes.
#   4. Pull the outputs (step 3 below).
#   5. To get another run: reset the consultation stage back to SETUP via Django
#      admin (Consultations → change stage field), then repeat from step 3.
#      Each re-run writes a new timestamped output to S3.
#
# Tip: you need NUM_RUNS completed find_themes jobs per dataset before continuing.

# ─── STEP 3: PULL S3 OUTPUTS ─────────────────────────────────────────────────
# Run once after each find_themes job completes in Consult.
# Auto-increments the run number (run_1, run_2, ...) within the dataset directory.
# Set CONSULTATION_CODE to match the S3 key for the consultation you just ran.
#
# Repeat this NUM_RUNS times per dataset (once per completed Consult pipeline run).

python "$SCRIPTS_DIR/pull_s3_outputs.py" \
    "$CONSULTATION_CODE" \
    "$DATA_DIR/$GT1_NAME" \
    --date "2026-06-22"

# Repeat for every dataset and every run, updating --date to match each Consult pipeline run.

# ─── STEP 4: SANITY CHECK — THEME COUNT VARIATION ────────────────────────────
# Compare how many themes were generated across runs and datasets.
# Use this to confirm you have enough runs and to spot outliers before analysis.
# High stddev relative to mean suggests the pipeline is unstable for that dataset.

python "$SCRIPTS_DIR/compare_theme_counts.py" "$DATA_DIR"

# ─── STEP 5: BUILD CONSENSUS GROUND TRUTHS ───────────────────────────────────
# Consolidates all themes from all runs of each GT dataset into a single
# deduplicated consensus theme set via an LLM call.
# Writes to <gt_dir>/consensus/question_part_*/clustered_themes.json.
#
# Only needed if you want to use a consensus GT rather than a single run.
# Skip this step and pass --run <n> to analyse_theme_similarity.py instead
# if you prefer to analyse run-by-run.

python "$SCRIPTS_DIR/build_consensus_gt.py" \
    "$DATA_DIR" \
    "$GT1_NAME" "$GT2_NAME"

# ─── STEP 6: ANALYSE ─────────────────────────────────────────────────────────
# Compares each test dataset's themes against the two GT clusters.
# Each theme is assigned to GT1, GT2, or 'both' via normalised centroid distance
# and k-NN. Summary table printed to stdout; per-dataset detail written to
# $DATA_DIR/analysis_logs/.

# GTs are always loaded from their consensus/ subdirectory.
# Test datasets are run across all run_* subdirectories; results are mean±std proportions.
python "$SCRIPTS_DIR/analyse_theme_similarity.py" \
    "$DATA_DIR" \
    "$GT1_NAME" "$GT2_NAME"

# Optionally restrict to a specific test subdirectory:
# python "$SCRIPTS_DIR/analyse_theme_similarity.py" \
#     "$DATA_DIR" \
#     "$GT1_NAME" "$GT2_NAME" \
#     mixed_datasets
