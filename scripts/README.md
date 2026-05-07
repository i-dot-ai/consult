# Consultation setup scripts

Standalone CLI tools for preparing a new consultation for the
ThemeFinder pipeline. They run outside the Django backend but reuse its
`uv` environment for dependencies.

| Script | Purpose |
| --- | --- |
| `setup_consultation.py` | Validate a Q.U. workbook against a response file, build the ThemeFinder input layout (`respondents.jsonl`, `question_part_<n>/...`), and upload the result to S3. |
| `build_consult_data_template.py` | Generate `consult_data_template.xlsx` — an opinionated Q.U. workbook skeleton with live in-sheet validation rules and a pre-populated dummy Responses sheet. |
| `build_consult_data_dummy_content.py` | Static word lists used as dummy content by the template builder. Not run directly. |

The full set of validation rules implemented in both
`setup_consultation.py` and the in-sheet checks in
`consult_data_template.xlsx` is documented in
[`setup_consultation_checks.md`](./setup_consultation_checks.md).

## Running the scripts

From the repo root:

```bash
# Build the opinionated Q.U. template (writes consult_data_template.xlsx
# next to the script):
make build-consultation-template

# Set up a new consultation end-to-end (validate → build inputs → upload to S3):
make setup-consultation name=my_consultation
```

Stop early with `until=validate` (just print the validation report) or
`until=build` (build inputs locally, skip the S3 upload).

To run the scripts directly:

```bash
cd backend
uv run python ../scripts/build_consult_data_template.py
uv run python ../scripts/setup_consultation.py my_consultation --until validate
```

## How `setup_consultation.py` finds files

`setup_consultation.py` works from a per-consultation directory at
`scripts/consultations/<name>/`. The first run creates the directory
and prompts you to drop the response data and Q.U. workbook into it;
subsequent runs auto-discover them. Pass `--responses` / `--qu` to
point at files anywhere on disk.

The S3 upload requires AWS credentials in the environment (e.g. via
`aws-vault exec ...`). Use `until=build` to skip the upload step when
working without credentials.

## Tests

```bash
cd backend
uv run pytest ../scripts/tests/
```

Fixtures in `tests/fixtures/setup_consultation/` cover the three
response-file layouts and two Q.U. workbook formats we've seen in real
consultations.
