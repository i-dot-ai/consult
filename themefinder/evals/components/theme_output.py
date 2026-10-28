"""Normalise component theme output for evaluator consumption."""

from typing import Any

import pandas as pd


def build_themes_output(themes_df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    """Normalise themes into the shape consumed by the evaluators."""
    themes = []
    for record in themes_df.to_dict(orient="records"):
        if "topic" in record and ":" in record["topic"]:
            label, description = record["topic"].split(":", 1)
            record["topic_label"] = label.strip()
            record["topic_description"] = description.strip()
        themes.append(record)
    return {"themes": themes}
