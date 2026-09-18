"""DatasetPort - the port every dataset adapter implements.

Concrete dataset adapters load component-specific cases from one backing store
and return them as framework-owned `Case` objects.
"""

from abc import ABC, abstractmethod

from datasets import DatasetConfig
from eval_types import Case


class DatasetPort(ABC):
    @abstractmethod
    def load_cases(self, config: DatasetConfig) -> list[Case]:
        """Load cases for a component/dataset config."""
