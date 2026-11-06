"""LocalJSONDatasetAdapter - load eval cases from on-disk JSON fixtures."""

from datasets import DatasetConfig, load_local_data
from eval_types import Case, DatasetNotFoundError

from .base import DatasetPort, readable_case_id


class LocalJSONDatasetAdapter(DatasetPort):
    def _load_cases(self, config: DatasetConfig) -> list[Case]:
        """Load local fixture items and normalise them into `Case` objects."""
        try:
            return [
                self._to_case(item, index, config)
                for index, item in enumerate(load_local_data(config))
            ]
        except FileNotFoundError as exc:
            raise DatasetNotFoundError(
                f"Local dataset {config.local_path} not found or incomplete"
            ) from exc

    @staticmethod
    def _to_case(item: dict, index: int, config: DatasetConfig) -> Case:
        metadata = dict(item.get("metadata") or {})
        return Case(
            id=readable_case_id(config, metadata, fallback=f"case-{index + 1}"),
            inputs=item["input"],
            expected_output=item.get("expected_output"),
            metadata=metadata,
        )
