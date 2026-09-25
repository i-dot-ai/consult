import json
from types import SimpleNamespace

import datasets as datasets_module
import pytest
from datasets import DatasetConfig, load_local_data, publish_local_dataset_to_langfuse
from synthetic.config import (
    GenerationConfig,
    QuestionConfig,
    ResponseLength,
    ResponseType,
)
from synthetic.generator import SyntheticDatasetGenerator
from synthetic.llm_generators.response_generator import RespondentSpec
from synthetic.validators import validate_dataset


class DummyClient:
    def __init__(self, items_by_name=None):
        self.items_by_name = items_by_name or {}
        self.created_datasets = []
        self.created_items = []
        self.flushed = False

    def get_dataset(self, name):
        if name not in self.items_by_name:
            raise RuntimeError("missing")
        return SimpleNamespace(items=self.items_by_name[name])

    def create_dataset(self, name, description, metadata):
        self.created_datasets.append(
            {"name": name, "description": description, "metadata": metadata}
        )
        self.items_by_name[name] = []
        return SimpleNamespace(items=[])

    def create_dataset_item(self, dataset_name, input, expected_output, metadata):
        self.created_items.append(
            {
                "dataset_name": dataset_name,
                "input": input,
                "expected_output": expected_output,
                "metadata": metadata,
            }
        )

    def flush(self):
        self.flushed = True


class DummyRng:
    def __init__(self):
        self.shuffled = None

    def shuffle(self, items):
        self.shuffled = list(items)


class FakeParsedCompletions:
    def __init__(self):
        self.calls = []
        self.response_count = 0

    async def parse(self, model, messages, response_format, reasoning_effort):
        self.calls.append(
            {
                "model": model,
                "messages": messages,
                "response_format": response_format,
                "reasoning_effort": reasoning_effort,
            }
        )

        prompt = messages[-1]["content"]
        if response_format.__name__ == "ThemeSet":
            if "Raw Themes to Consolidate" in prompt:
                payload = {
                    "themes": [
                        {
                            "topic_id": "A",
                            "topic_label": "Implementation support",
                            "topic_description": "Supports the proposal because it is practical and easier to deliver consistently.",
                        }
                    ]
                }
            else:
                payload = {
                    "themes": [
                        {
                            "topic_id": "A",
                            "topic_label": "Implementation support",
                            "topic_description": "Supports the proposal because it is practical and easier to deliver consistently.",
                        }
                    ]
                }
        else:
            self.response_count += 1
            payload = {
                "response": f"Synthetic response {self.response_count}",
                "sentiment": "AGREE",
                "evidence_rich": True,
            }

        parsed = response_format.model_validate(payload)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))]
        )


class FakeAsyncLLMClient:
    def __init__(self):
        self.completions = FakeParsedCompletions()
        self.beta = SimpleNamespace(chat=SimpleNamespace(completions=self.completions))


def _patch_dataset_root(monkeypatch, tmp_path):
    dataset_root = tmp_path / "data"
    monkeypatch.setattr(datasets_module, "DATA_DIR", dataset_root)
    monkeypatch.setattr(
        GenerationConfig,
        "output_dir",
        property(lambda self: dataset_root / self.dataset_name),
    )
    return dataset_root


def _read_json(path):
    with open(path) as f:
        return json.load(f)


def _read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def test_build_respondent_specs_uses_override(monkeypatch):
    """Verify `build_respondent_specs()` honours its explicit override count.

    This test checks the public method boundary rather than internal respondent
    construction details. When a caller passes `3`, the generator should:
    - sample demographics for exactly 3 respondents
    - forward those sampled demographics into `_create_respondent_specs`
    - pass `n_responses=3` into `_create_respondent_specs` rather than falling
      back to `config.n_responses`

    The returned value is a sentinel from the patched helper so the test stays
    focused on argument plumbing, not spec creation internals.
    """
    config = GenerationConfig(
        dataset_name="synthetic_test",
        topic="Topic",
        n_responses=10,
        questions=[QuestionConfig(number=1, text="Question 1")],
        demographic_fields=[],
    )
    generator = SyntheticDatasetGenerator(
        config=config,
        llm=(object(), "test-model"),
    )

    observed = {}

    def fake_sample_demographics(fields, n_samples, rng):
        observed["sampled_count"] = n_samples
        return [{"Persona": f"Person {i}"} for i in range(n_samples)]

    def fake_create_respondent_specs(demographics, n_responses=None):
        observed["demographics"] = demographics
        observed["n_responses"] = n_responses
        return ["sentinel-spec"]

    monkeypatch.setattr(
        "synthetic.generator.sample_demographics", fake_sample_demographics
    )
    monkeypatch.setattr(
        generator,
        "_create_respondent_specs",
        fake_create_respondent_specs,
    )

    specs = generator.build_respondent_specs(3)

    assert specs == ["sentinel-spec"]
    assert observed["sampled_count"] == 3
    assert observed["n_responses"] == 3
    assert len(observed["demographics"]) == 3


def test_create_respondent_specs_ids(monkeypatch):
    """Verify `_create_respondent_specs()` assigns stable sequential IDs.

    This test confirms that respondent specs are created with incrementing IDs
    starting at 1001 and that the same specs are handed to the RNG's shuffle
    step. Disposition, length, noise, and stance-modifier sampling are patched
    to be deterministic.
    """
    config = GenerationConfig(
        dataset_name="synthetic_test",
        topic="Topic",
        n_responses=10,
        questions=[QuestionConfig(number=1, text="Question 1")],
        demographic_fields=[],
    )
    generator = SyntheticDatasetGenerator(
        config=config,
        llm=(object(), "test-model"),
    )
    generator.rng = DummyRng()

    monkeypatch.setattr(
        "synthetic.generator.calculate_stance_modifier", lambda *args: 0.0
    )
    monkeypatch.setattr(
        generator,
        "_sample_disposition",
        lambda probs: ResponseType.NUANCED,
    )
    monkeypatch.setattr(
        generator,
        "_sample_length",
        lambda length_counts: ResponseLength.MEDIUM,
    )
    monkeypatch.setattr(generator, "_sample_noise", lambda: (False, None))

    specs = generator._create_respondent_specs(
        [
            {"Persona": "Person 0"},
            {"Persona": "Person 1"},
            {"Persona": "Person 2"},
        ],
        n_responses=3,
    )

    assert [spec.response_id for spec in specs] == [1001, 1002, 1003]
    assert [spec.persona for spec in specs] == [
        {"Persona": "Person 0"},
        {"Persona": "Person 1"},
        {"Persona": "Person 2"},
    ]
    assert [spec.response_id for spec in generator.rng.shuffled] == [1001, 1002, 1003]


@pytest.mark.asyncio
async def test_write_full_dataset_persists_expected_files(monkeypatch, tmp_path):
    """Verify `write_full_dataset()` writes a valid on-disk dataset structure.

    This is a file-output flow test for the persistence layer around response
    generation. It avoids any real LLM calls by patching respondent-spec creation,
    batch response generation, and the small async sleep between batches.

    The test checks that a full dataset run:
    - writes input question files for each configured question
    - writes respondents metadata
    - streams response and mapping JSONL files to the expected directories
    - produces a dataset that passes `validate_dataset()`
    - removes its checkpoint file after successful completion
    """
    _patch_dataset_root(monkeypatch, tmp_path)

    config = GenerationConfig(
        dataset_name="synthetic_write_flow",
        topic="Topic",
        n_responses=2,
        questions=[
            QuestionConfig(number=1, text="Question 1"),
            QuestionConfig(number=2, text="Question 2"),
        ],
        demographic_fields=[],
    )
    generator = SyntheticDatasetGenerator(
        config=config,
        llm=(object(), "test-model"),
    )

    respondent_specs = [
        RespondentSpec(
            response_id=1001,
            persona={"Persona": "Person 1"},
            base_disposition=ResponseType.AGREE,
            length=ResponseLength.SHORT,
            apply_noise=False,
        ),
        RespondentSpec(
            response_id=1002,
            persona={"Persona": "Person 2"},
            base_disposition=ResponseType.DISAGREE,
            length=ResponseLength.MEDIUM,
            apply_noise=False,
        ),
    ]
    themes_by_question = {
        1: [
            {
                "topic_id": "A",
                "topic_label": "Support",
                "topic_description": "Supports the proposal for practical reasons.",
                "topic": "Support: Supports the proposal for practical reasons.",
            },
            {
                "topic_id": "XX",
                "topic_label": "None of the Above",
                "topic_description": "Response discusses a topic not covered by listed themes",
                "topic": "None of the Above: Response discusses a topic not covered by listed themes",
            },
            {
                "topic_id": "XY",
                "topic_label": "No Reason Given",
                "topic_description": "Response does not provide a substantive answer",
                "topic": "No Reason Given: Response does not provide a substantive answer",
            },
        ],
        2: [
            {
                "topic_id": "A",
                "topic_label": "Implementation",
                "topic_description": "Focuses on delivery and administration concerns.",
                "topic": "Implementation: Focuses on delivery and administration concerns.",
            },
            {
                "topic_id": "XX",
                "topic_label": "None of the Above",
                "topic_description": "Response discusses a topic not covered by listed themes",
                "topic": "None of the Above: Response discusses a topic not covered by listed themes",
            },
            {
                "topic_id": "XY",
                "topic_label": "No Reason Given",
                "topic_description": "Response does not provide a substantive answer",
                "topic": "No Reason Given: Response does not provide a substantive answer",
            },
        ],
    }

    async def fake_generate_respondent_batch(**kwargs):
        assert kwargs["respondents"] == respondent_specs
        return [
            {
                "response_id": 1001,
                "question_number": 1,
                "response": "Response 1 to question 1",
                "position": "AGREE",
                "evidence_rich": "YES",
                "labels": ["A"],
                "stances": ["POSITIVE"],
            },
            {
                "response_id": 1002,
                "question_number": 1,
                "response": "Response 2 to question 1",
                "position": "DISAGREE",
                "evidence_rich": "NO",
                "labels": ["A"],
                "stances": ["NEGATIVE"],
            },
            {
                "response_id": 1001,
                "question_number": 2,
                "response": "Response 1 to question 2",
                "position": "AGREE",
                "evidence_rich": "YES",
                "labels": ["A"],
                "stances": ["POSITIVE"],
            },
            {
                "response_id": 1002,
                "question_number": 2,
                "response": "Response 2 to question 2",
                "position": "DISAGREE",
                "evidence_rich": "YES",
                "labels": ["A"],
                "stances": ["NEGATIVE"],
            },
        ]

    async def fake_sleep(_seconds):
        return None

    monkeypatch.setattr(generator, "build_respondent_specs", lambda n: respondent_specs)
    monkeypatch.setattr(
        "synthetic.generator.generate_respondent_batch",
        fake_generate_respondent_batch,
    )
    monkeypatch.setattr("synthetic.generator.asyncio.sleep", fake_sleep)

    output_path = await generator.write_full_dataset(themes_by_question)

    assert output_path == config.output_dir
    assert validate_dataset(output_path).is_valid is True
    assert not (output_path / ".checkpoint.json").exists()

    question_1 = output_path / "inputs" / "question_part_1"
    question_2 = output_path / "inputs" / "question_part_2"
    outputs_root = output_path / "outputs" / "mapping" / generator.writer.date_str

    assert _read_json(question_1 / "question.json") == {
        "question_number": 1,
        "question_text": "Question 1",
    }
    assert _read_json(question_2 / "question.json") == {
        "question_number": 2,
        "question_text": "Question 2",
    }
    assert _read_jsonl(output_path / "inputs" / "respondents.jsonl") == [
        {"response_id": 1001, "demographic_data": {"Persona": "Person 1"}},
        {"response_id": 1002, "demographic_data": {"Persona": "Person 2"}},
    ]
    assert _read_jsonl(question_1 / "responses.jsonl") == [
        {"response_id": 1001, "response": "Response 1 to question 1"},
        {"response_id": 1002, "response": "Response 2 to question 1"},
    ]
    assert _read_jsonl(outputs_root / "question_part_2" / "mapping.jsonl") == [
        {"response_id": 1001, "labels": ["A"], "stances": ["POSITIVE"]},
        {"response_id": 1002, "labels": ["A"], "stances": ["NEGATIVE"]},
    ]


@pytest.mark.asyncio
async def test_generate_round_trip(monkeypatch, tmp_path):
    """Verify a generated dataset can be loaded back through all local loaders.

    This exercises the synthetic generation path end to end while using a tiny
    fake async LLM client that implements only the `parse(...)` interface needed
    by theme and response generation. Because the client returns canned parsed
    objects, the test performs no network calls and consumes no tokens.

    After generation, the test confirms the dataset round-trips through the
    `generation`, `mapping`, `condensation`, and `refinement` local dataset
    loaders, and that the returned structures contain the expected question,
    responses, mappings, and condensed theme payloads.
    """
    _patch_dataset_root(monkeypatch, tmp_path)

    config = GenerationConfig(
        dataset_name="synthetic_round_trip",
        topic="Housing policy",
        n_responses=2,
        questions=[
            QuestionConfig(number=1, text="What are your views on the proposal?")
        ],
        demographic_fields=[],
    )
    fake_client = FakeAsyncLLMClient()
    generator = SyntheticDatasetGenerator(
        config=config,
        llm=(fake_client, "fake-model"),
    )

    def fake_sample_demographics(fields, n_samples, rng):
        return [{"Persona": f"Respondent {i}"} for i in range(n_samples)]

    async def fake_sleep(_seconds):
        return None

    monkeypatch.setattr(
        "synthetic.generator.sample_demographics", fake_sample_demographics
    )
    monkeypatch.setattr(generator, "_sample_noise", lambda: (False, None))
    monkeypatch.setattr("synthetic.generator.asyncio.sleep", fake_sleep)

    output_path = await generator.generate()

    assert output_path == config.output_dir
    assert validate_dataset(output_path).is_valid is True

    generation_items = load_local_data(
        DatasetConfig(dataset=config.dataset_name, component="generation")
    )
    mapping_items = load_local_data(
        DatasetConfig(dataset=config.dataset_name, component="mapping")
    )
    condensation_items = load_local_data(
        DatasetConfig(dataset=config.dataset_name, component="condensation")
    )
    refinement_items = load_local_data(
        DatasetConfig(dataset=config.dataset_name, component="refinement")
    )

    assert len(generation_items) == 1
    assert len(mapping_items) == 1
    assert len(condensation_items) == 1
    assert len(refinement_items) == 1

    assert (
        generation_items[0]["input"]["question"]
        == "What are your views on the proposal?"
    )
    assert len(generation_items[0]["input"]["responses"]) == 2
    assert generation_items[0]["expected_output"]["themes"][0]["topic_id"] == "A"

    assert (
        mapping_items[0]["input"]["topics"][0]["topic_label"]
        == "Implementation support"
    )
    assert sorted(mapping_items[0]["expected_output"]["mappings"].keys()) == [
        "1001",
        "1002",
    ]

    assert condensation_items[0]["expected_output"] is None
    assert condensation_items[0]["input"]["themes"] == [
        {
            "topic_label": "Implementation support",
            "topic_description": "Supports the proposal because it is practical and easier to deliver consistently.",
        },
        {
            "topic_label": "None of the Above",
            "topic_description": "Response discusses a topic not covered by listed themes",
        },
        {
            "topic_label": "No Reason Given",
            "topic_description": "Response does not provide a substantive answer",
        },
    ]
    assert refinement_items == condensation_items
    assert fake_client.completions.calls


def test_publish_local_dataset_to_langfuse_skips_existing_items(monkeypatch):
    """Verify Langfuse upload skips components whose datasets already contain items.

    The upload helper should leave non-empty remote datasets untouched to avoid
    duplicating eval items on repeated publishes. This test simulates an existing
    `generation` dataset while the other components are empty or missing, then
    checks that:
    - `generation` reports zero uploaded items
    - the remaining components each upload one item
    - the client is flushed once at the end
    """

    def fake_load_local_data(config):
        return [
            {
                "input": {"component": config.component},
                "expected_output": {"ok": True},
                "metadata": {"question_part": "question_part_1"},
            }
        ]

    monkeypatch.setattr("datasets.load_local_data", fake_load_local_data)

    client = DummyClient(items_by_name={"eval/synthetic_test/generation": [{}]})

    uploaded = publish_local_dataset_to_langfuse(client, "synthetic_test")

    assert uploaded["generation"] == 0
    assert uploaded["mapping"] == 1
    assert uploaded["condensation"] == 1
    assert uploaded["refinement"] == 1
    assert client.flushed is True
    assert len(client.created_items) == 3
