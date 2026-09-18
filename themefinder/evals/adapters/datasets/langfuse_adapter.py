"""LangfuseDatasetAdapter - load eval cases from a Langfuse dataset."""

from typing import Any

from datasets import DatasetConfig
from eval_types import Case, DatasetNotFoundError

from .base import DatasetPort


class LangfuseDatasetAdapter(DatasetPort):
    def __init__(self, client: Any):
        self.client = client

    def load_cases(self, config: DatasetConfig) -> list[Case]:
        """Load a Langfuse dataset and normalise its items into `Case` objects."""
        try:
            dataset = self.client.get_dataset(config.name)
        except Exception as exc:
            raise DatasetNotFoundError(
                f"Langfuse dataset {config.name} not found or inaccessible"
            ) from exc

        return [self._to_case(item) for item in dataset.items]

    @staticmethod
    def _to_case(item: Any) -> Case:
        metadata = dict(getattr(item, "metadata", None) or {})
        metadata["langfuse_item_id"] = item.id
        return Case(
            id=item.id,
            inputs=item.input,
            expected_output=item.expected_output,
            metadata=metadata,
        )
