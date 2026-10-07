"""Registry for constructing evaluation component configurations."""

from collections.abc import Callable
from typing import Any

from component_catalog import COMPONENT_NAMES
from eval_types import ComponentConfig

from .condensation import build_condensation_config
from .generation import build_generation_config
from .mapping import build_mapping_config
from .refinement import build_refinement_config

ComponentFactory = Callable[..., ComponentConfig]


COMPONENT_FACTORIES: dict[str, ComponentFactory] = {
    "mapping": build_mapping_config,
    "generation": build_generation_config,
    "condensation": build_condensation_config,
    "refinement": build_refinement_config,
}


def build_component_config(
    component: str,
    *,
    judge_llm: Any,
    question_num: int | None = None,
) -> ComponentConfig:
    """Construct a fresh configuration for the selected component."""
    if component not in COMPONENT_FACTORIES:
        raise ValueError(
            f"Unknown component '{component}'. Must be one of: {list(COMPONENT_NAMES)}"
        )
    if question_num is not None and component != "mapping":
        raise ValueError("question_num is only supported for the mapping component")
    if question_num is not None and question_num < 1:
        raise ValueError("question_num must be greater than zero")

    factory = COMPONENT_FACTORIES[component]
    if component == "mapping":
        return factory(question_num=question_num)
    return factory(judge_llm)
