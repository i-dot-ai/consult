"""DatasetPort - the port every dataset adapter implements.

Concrete dataset adapters load component-specific cases from one backing store
and return them as framework-owned `Case` objects.
"""

from abc import ABC, abstractmethod
from collections import Counter

from datasets import DatasetConfig
from eval_types import Case


class DatasetPort(ABC):
    def load_cases(self, config: DatasetConfig) -> list[Case]:
        """Load cases, refusing a dataset that repeats a question part: results are
        reported per question, so two cases claiming one question would be mixed."""
        cases = self._load_cases(config)
        counts = Counter(
            part for case in cases if (part := case.metadata.get("question_part"))
        )
        duplicates = sorted(part for part, n in counts.items() if n > 1)
        if duplicates:
            raise ValueError(
                f"dataset {config.name} repeats question parts: {duplicates}"
            )
        return cases

    @abstractmethod
    def _load_cases(self, config: DatasetConfig) -> list[Case]:
        """Load cases for a component/dataset config from the backing store."""
