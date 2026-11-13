#!/usr/bin/env python
"""Review the redundancy threshold against theme pairs with known labels.

``build`` takes a dataset's themes, asks an LLM for variants of each one at
three distances plus a distinct theme that shares its vocabulary, and saves the
themes with their labels for ``publish`` to upsert into Langfuse, the dataset's
home. ``sweep`` scores every pair the way
``RedundancyEvaluator`` does and reports precision, recall and F1 per threshold.

Usage:
    uv run --extra eval python scripts/redundancy_threshold.py build --dataset gambling_XS [--publish]
    uv run --extra eval python scripts/redundancy_threshold.py publish --dataset gambling_XS
    uv run --extra eval python scripts/redundancy_threshold.py sweep --dataset gambling_XS [--text title_description]
"""

import argparse
import asyncio
import csv
import itertools
import json
import sys
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import numpy as np
from pydantic import BaseModel, Field
from themefinder.llm import OpenAILLM

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datasets import DATA_DIR, DatasetConfig, _get_question_parts, _load_themes
from scripts.migrate_to_langfuse import get_langfuse_client
from settings import eval_settings
from utils import gateway
from utils.embeddings import get_sentence_model
from utils.logging_config import get_logger

logger = get_logger(__name__)

LANGFUSE_DATASET_PREFIX = "eval/redundancy_threshold"
LOCAL_DIR = DATA_DIR / "redundancy_threshold"
SWEEP_DIR = (
    Path(__file__).resolve().parent.parent / "local_eval_runs" / "redundancy_threshold"
)

SOURCE_KIND = "source"
REDUNDANT_KINDS = ("rewording", "reframing", "narrower")
DISTINCT_KIND = "hard_negative"


class Theme(BaseModel):
    topic_label: str = Field(
        description="A short title, in the style of the source themes"
    )
    topic_description: str = Field(description="One or two sentences")


class ThemeVariants(BaseModel):
    rewording: Theme = Field(description="The same theme in different words")
    reframing: Theme = Field(
        description="The same viewpoint approached from a different angle or emphasis"
    )
    narrower: Theme = Field(
        description="A sub-theme that sits wholly inside the source theme"
    )
    hard_negative: Theme = Field(
        description="A genuinely different viewpoint on the same subject, sharing vocabulary"
    )


VARIANT_PROMPT = """You are helping test a redundancy check for consultation analysis themes.
Themes are redundant when a reader would say they make the same point.

Source theme:
Title: {label}
Description: {description}

Other themes already in this set, which every variant must stay distinct from:
{others}

Write four themes, each with a title and a one or two sentence description:
- rewording: the same theme in different words.
- reframing: the same viewpoint approached from a different angle or emphasis.
- narrower: a sub-theme that sits wholly inside the source theme.
- hard_negative: a genuinely different viewpoint on the same subject that shares the
  source theme's vocabulary, so it looks similar but is not redundant with it.
"""


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser(
        "build", help="Generate labelled theme pairs from a dataset"
    )
    build.add_argument(
        "--dataset", default="gambling_XS", help="Local dataset whose themes to use"
    )
    build.add_argument(
        "--model",
        default=eval_settings.judge_model,
        help="Gateway model that writes the variants (default: AUTO_EVAL_JUDGE_MODEL)",
    )
    build.add_argument(
        "--publish", action="store_true", help="Also upsert into Langfuse"
    )

    publish = commands.add_parser(
        "publish", help="Upsert the saved pairs into Langfuse"
    )
    publish.add_argument("--dataset", default="gambling_XS")

    sweep = commands.add_parser(
        "sweep", help="Score thresholds against the labelled pairs"
    )
    sweep.add_argument("--dataset", default="gambling_XS")
    sweep.add_argument(
        "--source",
        choices=("local", "langfuse"),
        default="langfuse",
        help="Where to read the pairs; local is what build saved on this machine",
    )
    sweep.add_argument(
        "--text",
        choices=("title", "title_description"),
        default="title",
        help="What to embed; the evaluator embeds titles only",
    )
    sweep.add_argument(
        "--exclude-kind",
        action="append",
        default=[],
        choices=REDUNDANT_KINDS,
        help="Leave pairs involving this variant kind out of the labels",
    )
    sweep.add_argument("--start", type=float, default=0.50)
    sweep.add_argument("--stop", type=float, default=0.95)
    sweep.add_argument("--step", type=float, default=0.05)

    args = parser.parse_args(argv)
    if args.command == "build" and not args.model:
        parser.error("--model or AUTO_EVAL_JUDGE_MODEL is required")
    if args.command == "sweep":
        if args.step <= 0:
            parser.error("--step must be positive")
        if args.stop < args.start:
            parser.error("--stop must not be below --start")
    return args


# --- build -----------------------------------------------------------------


def _as_theme(source: dict, theme: Theme, kind: str) -> dict:
    """A variant keeps its source's group unless it is the distinct one."""
    topic_id = f"{source['topic_id']}.{kind}"
    return {
        "topic_id": topic_id,
        "topic_label": theme.topic_label,
        "topic_description": theme.topic_description,
        "group": topic_id if kind == DISTINCT_KIND else source["group"],
        "kind": kind,
    }


async def _variants_for(source: dict, others: list[dict], llm: Any) -> list[dict]:
    prompt = VARIANT_PROMPT.format(
        label=source["topic_label"],
        description=source["topic_description"],
        others="\n".join(f"- {theme['topic_label']}" for theme in others),
    )
    variants = (await llm.ainvoke(prompt, ThemeVariants)).parsed
    return [
        _as_theme(source, getattr(variants, kind), kind)
        for kind in (*REDUNDANT_KINDS, DISTINCT_KIND)
    ]


async def build_items(
    sources: list[dict], llm: Any, concurrency: int = 5
) -> list[dict]:
    """Return the source themes and their variants, each carrying ``group`` and ``kind``.

    Source themes are taken as distinct from one another, so each is its own group.
    """
    themes = [
        {
            "topic_id": source["topic_id"],
            "topic_label": source["topic_label"],
            "topic_description": source["topic_description"],
            "group": source["topic_id"],
            "kind": SOURCE_KIND,
        }
        for source in sources
    ]
    limit = asyncio.Semaphore(concurrency)

    async def expand(source: dict) -> list[dict]:
        async with limit:
            others = [
                theme for theme in themes if theme["topic_id"] != source["topic_id"]
            ]
            return await _variants_for(source, others, llm)

    for variants in await asyncio.gather(*(expand(source) for source in themes)):
        themes.extend(variants)
    return themes


def redundant_pairs(themes: list[dict]) -> list[list[str]]:
    return [
        [first["topic_id"], second["topic_id"]]
        for first, second in itertools.combinations(themes, 2)
        if first["group"] == second["group"]
    ]


def _local_path(dataset: str, question_part: str) -> Path:
    return LOCAL_DIR / dataset / f"{question_part}.json"


def _create_llm(model: str) -> OpenAILLM:
    base_url, api_key = gateway.gateway_credentials(settings=eval_settings)
    return OpenAILLM(model=model, base_url=base_url, api_key=api_key)


async def build(dataset: str, model: str, publish: bool) -> dict[str, int]:
    """Build one item per question part, save it locally and optionally publish it."""
    config = DatasetConfig(dataset=dataset, component="mapping")
    client = get_langfuse_client() if publish else None
    llm = _create_llm(model)
    items: dict[str, list[dict]] = {}
    for question_part in _get_question_parts(config):
        themes = await build_items(_load_themes(config, question_part), llm)
        path = _local_path(dataset, question_part)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"themes": themes, "model": model}, indent=2) + "\n")
        items[question_part] = themes
        logger.info("Saved %s themes for %s to %s", len(themes), question_part, path)
    if client is not None:
        publish_items(client, dataset, items, model)
    return {question_part: len(themes) for question_part, themes in items.items()}


def publish_items(
    client: Any, dataset: str, items: dict[str, list[dict]], model: str
) -> None:
    name = f"{LANGFUSE_DATASET_PREFIX}/{dataset}"
    try:
        client.get_dataset(name)
    except Exception:
        client.create_dataset(
            name=name,
            description=f"Theme pairs with known redundancy labels, built from {dataset}",
            metadata={"dataset": dataset},
        )
    for question_part, themes in items.items():
        # Langfuse upserts on id, so a rerun updates items instead of duplicating them.
        client.create_dataset_item(
            id=str(uuid5(NAMESPACE_URL, f"{name}:{question_part}")),
            dataset_name=name,
            input={"themes": themes},
            expected_output={"redundant_pairs": redundant_pairs(themes)},
            metadata={
                "dataset": dataset,
                "question_part": question_part,
                "model": model,
            },
        )
    client.flush()
    logger.info("Published %s item(s) to %s", len(items), name)


# --- sweep -----------------------------------------------------------------


def load_items(dataset: str, source: str) -> dict[str, list[dict]]:
    if source == "langfuse":
        langfuse_items = (
            get_langfuse_client()
            .get_dataset(f"{LANGFUSE_DATASET_PREFIX}/{dataset}")
            .items
        )
        return {
            item.metadata["question_part"]: item.input["themes"]
            for item in langfuse_items
        }
    return {
        question_part: saved["themes"]
        for question_part, saved in load_saved(dataset).items()
    }


def load_saved(dataset: str) -> dict[str, dict]:
    paths = sorted((LOCAL_DIR / dataset).glob("question_part_*.json"))
    if not paths:
        raise FileNotFoundError(
            f"No labelled pairs under {LOCAL_DIR / dataset}; run build first"
        )
    return {path.stem: json.loads(path.read_text()) for path in paths}


def _text(theme: dict, text: str) -> str:
    if text == "title":
        return theme["topic_label"]
    return f"{theme['topic_label']}. {theme['topic_description']}"


def similarities(themes: list[dict], text: str) -> np.ndarray:
    """Pairwise cosine similarity, as the evaluator computes it."""
    embeddings = get_sentence_model().encode(
        [_text(theme, text) for theme in themes], normalize_embeddings=True
    )
    return np.asarray(embeddings) @ np.asarray(embeddings).T


def labelled_pairs(
    themes: list[dict], similarity: np.ndarray, exclude_kinds: tuple[str, ...] = ()
) -> list[tuple[float, bool]]:
    """Every pair's similarity and whether its themes share a group."""
    pairs = []
    for (i, first), (j, second) in itertools.combinations(enumerate(themes), 2):
        if first["kind"] in exclude_kinds or second["kind"] in exclude_kinds:
            continue
        pairs.append((float(similarity[i][j]), first["group"] == second["group"]))
    return pairs


def thresholds(start: float, stop: float, step: float) -> list[float]:
    values = []
    value = start
    # A little slack so float drift does not drop the stop value itself
    while value <= stop + step / 1000:
        values.append(round(value, 4))
        value += step
    return values


def score_threshold(
    pairs: list[tuple[float, bool]], threshold: float
) -> dict[str, float]:
    flagged = [redundant for similarity, redundant in pairs if similarity >= threshold]
    true_positives = sum(flagged)
    false_positives = len(flagged) - true_positives
    false_negatives = sum(redundant for _, redundant in pairs) - true_positives
    precision = true_positives / len(flagged) if flagged else 0.0
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "threshold": threshold,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def sweep(args: argparse.Namespace) -> list[dict[str, float]]:
    pairs: list[tuple[float, bool]] = []
    for question_part, themes in load_items(args.dataset, args.source).items():
        pairs.extend(
            labelled_pairs(
                themes, similarities(themes, args.text), tuple(args.exclude_kind)
            )
        )
        logger.info(
            "%s: %s themes, %s pairs so far", question_part, len(themes), len(pairs)
        )

    rows = [
        score_threshold(pairs, threshold)
        for threshold in thresholds(args.start, args.stop, args.step)
    ]
    path = (
        SWEEP_DIR
        / args.dataset
        / f"sweep_{args.text}{''.join(f'_no_{kind}' for kind in sorted(args.exclude_kind))}.csv"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("| Threshold | Precision | Recall | F1 | TP | FP | FN |")
    print("|---|---|---|---|---|---|---|")
    for row in rows:
        print(
            f"| {row['threshold']:g} | {row['precision']:.3f} | {row['recall']:.3f} | {row['f1']:.3f} "
            f"| {row['true_positives']} | {row['false_positives']} | {row['false_negatives']} |"
        )
    best = max(rows, key=lambda row: row["f1"])
    print(
        f"\nBest F1 {best['f1']:.3f} at threshold {best['threshold']:g}; written to {path}"
    )
    return rows


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.command == "build":
        counts = asyncio.run(build(args.dataset, args.model, args.publish))
        print(json.dumps(counts, indent=2))
    elif args.command == "publish":
        saved = load_saved(args.dataset)
        items = {
            question_part: entry["themes"] for question_part, entry in saved.items()
        }
        model = next(iter(saved.values()))["model"]
        publish_items(get_langfuse_client(), args.dataset, items, model)
    else:
        sweep(args)


if __name__ == "__main__":
    main()
