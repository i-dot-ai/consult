"""LocalJSONDatasetAdapter - load eval cases from on-disk JSON fixtures."""

from datasets import DatasetConfig, load_local_data
from eval_types import Case

from .base import DatasetPort


class LocalJSONDatasetAdapter(DatasetPort):
    def load_cases(self, config: DatasetConfig) -> list[Case]:
        """Load local fixture items and normalise them into `Case` objects."""
        return [
            self._to_case(item, index)
            for index, item in enumerate(load_local_data(config))
        ]

    @staticmethod
    def _to_case(item: dict, index: int) -> Case:
        metadata = dict(item.get("metadata") or {})
        case_id = metadata.get("question_part") or f"case-{index + 1}"
        return Case(
            id=case_id,
            inputs=item["input"],
            expected_output=item.get("expected_output"),
            metadata=metadata,
        )
