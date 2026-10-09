# Internal i.AI contributors to ThemeFinder

At present we are not accepting contributions to `themefinder` as it is undergoing rapid development within i.AI. If you have a suggestion, please raise an [issue](https://github.com/i-dot-ai/consult/issues) or email us at [packages@cabinetoffice.gov.uk](mailto:packages@cabinetoffice.gov.uk).


## Architecture decisions

`themefinder` was migrated from its standalone repo into the consult monorepo as a uv workspace member — see [ADR 0009](../architecture/decisions/0009-merge-themefinder-into-consult-as-a-uv-workspace.md). That ADR also records the **source provenance**: the exact upstream commit this copy was taken from ([`09918eb213e0`](https://github.com/i-dot-ai/themefinder/commit/09918eb213e0)) and how to diff the in-repo copy against upstream.

## Developing the package locally

Ensure you have installed `pre-commit` in the repo: `pre-commit install`. This includes hooks to prevent you committing sensitive data. This will not catch everything; always take care when working in the open.

`themefinder` is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) member of the consult monorepo. Run `uv sync` from the repository root to install all workspace dependencies.

Within the monorepo, `themefinder` is already installed editable for the other members (backend and the pipelines) via `[tool.uv.sources] themefinder = { workspace = true }`, so a change in `themefinder/src/` is immediately visible to them with no extra step.

If you wish to install your local development version of the package into a project *outside* this monorepo to test it, install in "editable" mode:
```
uv pip install -e <FILE_PATH>
```
where `<FILE_PATH>` is the location of your local version of `themefinder`.


## Evaluation

The `evals/` directory contains our benchmarking evaluation suite used to measure system performance. When you make a change to the `themefinder` pipeline, run the evaluations to ensure you haven't reduced performance.

Shared evaluation datasets are stored in Langfuse and require Langfuse credentials. Local JSON datasets can also be used without Langfuse. The `make run-evals` command does not require AWS access.

These evaluations access models through the LLM gateway.

### Running the evaluations

Copy `themefinder/.env.example` to `themefinder/.env` and configure the LLM gateway credentials and evaluation model. To use shared datasets or store results in Langfuse, select the Langfuse backends and provide the corresponding credentials:

```env
THEMEFINDER_EVAL_DATASET_SOURCE=langfuse
THEMEFINDER_EVAL_ARTEFACT_STORE=langfuse
LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_BASE_URL=...
```

Set either backend to `local`, or leave it unset, to use local JSON data or result storage instead.

Install packages for this repo: `uv sync` from the repository root.

These evaluations can be executed either:

- By running `make run-evals` from the repo root to execute the complete evaluation suite
- By running `uv run --extra eval python run_eval.py --component <name> --dataset <dataset>` from `themefinder/evals/`

The model is selected through `AUTO_EVAL_MODEL` or the benchmark command's model arguments.


## Releasing to PyPi

Creating a GitHub release will push that version of the package to TestPyPi and then PyPi.

1. Check with the Consult engineering team in Slack that it is ok to do a release.
2. Update the version number in themefinder's [`themefinder/pyproject.toml`](https://github.com/i-dot-ai/consult/blob/main/themefinder/pyproject.toml) - note that we are using SemVer.
3. From the `main` branch, create a [pre-release](https://github.com/i-dot-ai/consult/releases) by ticking the box at the bottom of the release. The release should have the tag `vX.Y.Z` where `X.Y.Z` is the version number in [`themefinder/pyproject.toml`](https://github.com/i-dot-ai/consult/blob/main/themefinder/pyproject.toml).
4. Use the "Generate release notes" button to get you started on writing a suitable release note.
5. Creating the pre-release should trigger a deployment to [TestPyPi](https://test.pypi.org/project/themefinder/). Check the GitHub Actions and TestPyPi to ensure that this happens.
6. Once you're happy, go back to the pre-release and turn it into a [release](https://github.com/i-dot-ai/consult/releases).
7. When you publish the release, this will trigger a deployment to PyPi. You can check the GitHub actions and [PyPi](https://pypi.org/project/themefinder/) itself to confirm the deployment has worked.


## Docs

These docs are built using [MkDocs](https://www.mkdocs.org/). They are stored as Markdown files in the top-level `docs/themefinder/` directory of the consult monorepo (`themefinder/mkdocs.yml` points its `docs_dir` there).

To test your changes locally, from the `themefinder/` directory:
```
uv run mkdocs build
uv run mkdocs serve
```
and go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in the browser.


## Architecture decision records (ADR)

If you are making significant changes, please record them in the architecure documents. We are using [adr-tools](https://github.com/npryce/adr-tools) - see the ADR tools repo for how to install and use.




## Langfuse integration

Langfuse can be used to monitor costs and log LLM calls. This can be initialised from outside of the ThemeFinder package when the LLM is instantiated. 

Set up:
Add to the `.env` file:
```
# Langfuse
LANGFUSE_SECRET_KEY=""
LANGFUSE_PUBLIC_KEY=""
LANGFUSE_HOST=""
```
using the keys from you own langfuse instance.

```python
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
 
dotenv.load_dotenv() 

# Initialize Langfuse CallbackHandler for Langchain (tracing)
# Use the session id to group calls
langfuse_callback_handler = CallbackHandler(session_id="run_1")

# Initialise your LLM of choice using langchain
llm = AzureChatOpenAI(
    model="gpt-4o",
    temperature=0,
    callbacks=[langfuse_callback_handler],
    model_kwargs={"response_format": {"type": "json_object"}},
)
```

Use as you would normally. Your langfuse dashboard should log the llm calls including the inputs, outputs, model name, costs, and more.
