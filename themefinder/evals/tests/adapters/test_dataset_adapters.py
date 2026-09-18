"""Tests for the dataset port and its concrete adapters."""

import types

import pytest
from adapters.datasets.base import DatasetPort
from adapters.datasets.langfuse_adapter import LangfuseDatasetAdapter
from adapters.datasets.local_json_adapter import LocalJSONDatasetAdapter
from datasets import DatasetConfig, load_local_data
from eval_types import Case, DatasetNotFoundError


def test_local_json_dataset_adapter_is_dataset_port():
    assert isinstance(LocalJSONDatasetAdapter(), DatasetPort)


def test_langfuse_dataset_adapter_is_dataset_port():
    client = types.SimpleNamespace(get_dataset=lambda name: None)
    assert isinstance(LangfuseDatasetAdapter(client), DatasetPort)


def test_dataset_port_enforces_load_cases_implementation():
    class _IncompleteDatasetAdapter(DatasetPort):
        pass

    with pytest.raises(TypeError):
        _IncompleteDatasetAdapter()


@pytest.mark.parametrize(
    ("component", "expected_input_keys", "expects_output"),
    [
        pytest.param("generation", {"question", "responses"}, True, id="generation"),
        pytest.param(
            "mapping", {"question", "topics", "responses"}, True, id="mapping"
        ),
        pytest.param("condensation", {"question", "themes"}, False, id="condensation"),
        pytest.param("refinement", {"question", "themes"}, False, id="refinement"),
    ],
)
def test_local_json_dataset_adapter_loads_gambling_xs_cases(
    component, expected_input_keys, expects_output
):
    cases = LocalJSONDatasetAdapter().load_cases(
        DatasetConfig(dataset="gambling_XS", component=component)
    )

    assert cases
    assert all(isinstance(case, Case) for case in cases)
    assert all(case.id.startswith("question_part_") for case in cases)
    assert all(case.metadata.get("question_part") == case.id for case in cases)
    assert all("langfuse_item_id" not in case.metadata for case in cases)

    first_case = cases[0]
    assert expected_input_keys.issubset(first_case.inputs.keys())
    if expects_output:
        assert first_case.expected_output is not None
    else:
        assert first_case.expected_output is None


def test_langfuse_dataset_adapter_converts_items_to_cases():
    source_items = load_local_data(
        DatasetConfig(dataset="gambling_XS", component="mapping")
    )
    fake_items = [
        types.SimpleNamespace(
            id=f"lf-item-{index + 1}",
            input=item["input"],
            expected_output=item.get("expected_output"),
            metadata=item.get("metadata"),
        )
        for index, item in enumerate(source_items)
    ]
    client = types.SimpleNamespace(
        get_dataset=lambda name: types.SimpleNamespace(items=fake_items)
    )

    cases = LangfuseDatasetAdapter(client).load_cases(
        DatasetConfig(dataset="gambling_XS", component="mapping")
    )

    assert len(cases) == len(fake_items)
    assert all(isinstance(case, Case) for case in cases)
    assert cases[0].id == "lf-item-1"
    assert cases[0].inputs == fake_items[0].input
    assert cases[0].expected_output == fake_items[0].expected_output
    assert cases[0].metadata["question_part"] == fake_items[0].metadata["question_part"]
    assert cases[0].metadata["langfuse_item_id"] == "lf-item-1"


def test_langfuse_dataset_adapter_raises_dataset_not_found_error():
    class _MissingDatasetClient:
        def get_dataset(self, name):
            raise RuntimeError("missing")

    adapter = LangfuseDatasetAdapter(_MissingDatasetClient())

    with pytest.raises(DatasetNotFoundError, match="eval/gambling_XS/generation"):
        adapter.load_cases(DatasetConfig(dataset="gambling_XS", component="generation"))
