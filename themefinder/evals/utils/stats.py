"""Statistics across repeated runs of an eval, so run-to-run variance is visible
alongside the per-run scores."""

from collections import defaultdict
from collections.abc import Callable
from itertools import combinations
from statistics import mean, stdev
from typing import Any

import numpy as np
from eval_types import CaseOutcome
from scipy.optimize import linear_sum_assignment
from utils.embeddings import get_sentence_model
from utils.logging_config import get_logger

logger = get_logger(__name__)

CONSISTENCY_METRIC = "output_consistency"
PAIR_METRICS = ("f1", "count")
TRACK_STATUSES = ("stable", "reworded", "intermittent")
# shortcut: untuned guess at "same theme, reworded"; tune on real repeated runs.
MATCH_THRESHOLD = 0.75

Embed = Callable[[list[str]], np.ndarray]


def summarise_runs(
    outcomes: list[CaseOutcome],
) -> dict[str, dict[str, float | int | None]]:
    """Mean, stdev and run count per metric, taking the case-mean within each run first."""
    per_run: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for outcome in outcomes:
        for score in outcome.scores:
            per_run[score.name][outcome.run_index].append(score.value)

    summary: dict[str, dict[str, float | int | None]] = {}
    for name, runs in per_run.items():
        run_means = [mean(values) for values in runs.values()]
        # Averaging within a run before comparing runs means stdev reflects run-to-run variance
        summary[name] = {
            "mean": mean(run_means),
            "stdev": stdev(run_means) if len(run_means) > 1 else None,
            "n": len(run_means),
        }
    return summary


def _default_embed(texts: list[str]) -> np.ndarray:
    """Unit-normalised sentence embeddings, so a dot product is cosine similarity."""
    return get_sentence_model().encode(texts, normalize_embeddings=True)


def _theme_label(theme: dict) -> str:
    return str(theme.get("topic_label") or theme.get("topic") or "").strip()


def _theme_text(theme: dict) -> str:
    """Label plus description, so two themes with the same title but different meaning differ."""
    description = str(theme.get("topic_description") or "").strip()
    label = _theme_label(theme)
    return f"{label}: {description}" if description else label


def _match(emb_a: np.ndarray, emb_b: np.ndarray) -> list[tuple[int, int, float]]:
    """One-to-one pairing of two embedding sets that maximises total similarity,
    keeping only pairs similar enough to count as the same theme."""
    if len(emb_a) == 0 or len(emb_b) == 0:
        return []
    similarity = emb_a @ emb_b.T
    rows, cols = linear_sum_assignment(similarity, maximize=True)
    return [
        (int(i), int(j), float(similarity[i, j]))
        for i, j in zip(rows, cols)
        if similarity[i, j] >= MATCH_THRESHOLD
    ]


def _pair_scores(n_a: int, n_b: int, shared: int | None) -> dict[str, float | None]:
    """f1: items both runs share, symmetric so neither run is the reference;
    count: how close the two list lengths are. Two empty runs agree completely."""
    if n_a + n_b == 0:
        return {"f1": 1.0, "count": 1.0}
    count = min(n_a, n_b) / max(n_a, n_b)
    f1 = None if shared is None else 2 * shared / (n_a + n_b)
    return {"f1": f1, "count": count}


def _mean_pair_scores(pairs: list[dict[str, float | None]]) -> dict[str, float | None]:
    return {m: _mean_or_none([pair[m] for pair in pairs]) for m in PAIR_METRICS}


def _mean_or_none(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    return mean(present) if present else None


def _label_consistency(outputs: list[dict]) -> dict[str, Any]:
    """Mapping outputs: labels come from a fixed set, so exact (response, label) pairs
    are matched rather than embeddings."""
    sets = [
        {
            (response_id, label)
            for response_id, labels in output["labels"].items()
            for label in labels
        }
        for output in outputs
    ]
    pairs = [_pair_scores(len(a), len(b), len(a & b)) for a, b in combinations(sets, 2)]
    return {**_mean_pair_scores(pairs), "n_items": _spread([len(s) for s in sets])}


def _spread(counts: list[int]) -> dict[str, float | None]:
    return {
        "mean": mean(counts),
        "stdev": stdev(counts) if len(counts) > 1 else None,
    }


def _assign_tracks(
    themes_per_run: list[list[dict]], embeddings: list[np.ndarray]
) -> np.ndarray:
    """Group themes across runs into tracks, one track per distinct theme.

    Returns assignment[track, run]: the index of that track's theme in that run, or -1
    if absent. Runs are taken in order: each run is matched one-to-one against the
    existing tracks, a matched theme extends its track and an unmatched one starts a
    new track.
    """
    n_runs = len(themes_per_run)
    # assignment[track, run]: index of the track's theme in that run, or -1 if absent
    assignment = np.empty((0, n_runs), dtype=int)
    # One row per track: the embedding of its most recently seen theme.
    # shortcut: compares against a track's latest theme, not its centroid; switch to
    # a centroid if long chains of small rewordings start drifting apart.
    latest: np.ndarray | None = None

    for run, run_embeddings in enumerate(embeddings):
        n_themes = len(themes_per_run[run])
        if n_themes == 0:
            continue

        matches = _match(latest, run_embeddings) if latest is not None else []
        matched_tracks = [track for track, _, _ in matches]
        matched_themes = [theme for _, theme, _ in matches]
        if matches:
            assignment[matched_tracks, run] = matched_themes
            latest[matched_tracks] = run_embeddings[matched_themes]

        new_themes = np.setdiff1d(np.arange(n_themes), matched_themes)
        new_tracks = np.full((len(new_themes), n_runs), -1)
        new_tracks[:, run] = new_themes
        assignment = np.vstack([assignment, new_tracks])
        new_latest = run_embeddings[new_themes]
        latest = new_latest if latest is None else np.vstack([latest, new_latest])

    return assignment


def _track_f1(present: np.ndarray) -> list[dict[str, float | None]]:
    """Pairwise scores for every pair of runs: tracks present in both runs are the
    themes those runs share."""
    as_int = present.astype(int)
    shared = as_int.T @ as_int  # shared[i, j]: tracks present in both run i and run j
    n_themes = present.sum(axis=0)
    return [
        _pair_scores(int(n_themes[i]), int(n_themes[j]), int(shared[i, j]))
        for i, j in combinations(range(present.shape[1]), 2)
    ]


def _describe_tracks(
    themes_per_run: list[list[dict]], assignment: np.ndarray
) -> dict[str, Any]:
    """Each track's status and labels per run, plus what changed between consecutive
    runs, so the consistency score can be traced back to individual themes."""
    n_runs = len(themes_per_run)
    present = assignment >= 0
    labels = np.full(assignment.shape, None, dtype=object)
    texts = np.full(assignment.shape, None, dtype=object)
    for track, run in zip(*np.nonzero(present)):
        theme = themes_per_run[run][assignment[track, run]]
        labels[track, run] = _theme_label(theme)
        texts[track, run] = _theme_text(theme)

    in_every_run = present.all(axis=1)
    unchanged = (texts == texts[:, :1]).all(axis=1)
    status = np.where(
        ~in_every_run, "intermittent", np.where(unchanged, "stable", "reworded")
    )

    changes = []
    for run in range(1, n_runs):
        before, after = present[:, run - 1], present[:, run]
        reworded = before & after & (texts[:, run - 1] != texts[:, run])
        changes.append(
            {
                "from_run": run - 1,
                "to_run": run,
                "dropped": labels[before & ~after, run - 1].tolist(),
                "appeared": labels[after & ~before, run].tolist(),
                "reworded": labels[reworded][:, [run - 1, run]].tolist(),
            }
        )

    return {
        "counts": {s: int((status == s).sum()) for s in TRACK_STATUSES},
        "themes": [
            {"status": s, "labels": row}
            for s, row in zip(status.tolist(), labels.tolist())
        ],
        "changes": changes,
    }


def _theme_consistency(outputs: list[dict], embed: Embed) -> dict[str, Any]:
    themes_per_run = [list(output.get("themes", [])) for output in outputs]
    counts = [len(themes) for themes in themes_per_run]
    result: dict[str, Any] = {"n_themes": _spread(counts)}

    try:
        embeddings = [
            embed([_theme_text(theme) for theme in themes])
            if themes
            else np.empty((0, 0))
            for themes in themes_per_run
        ]
    except ImportError:
        logger.warning(
            "sentence-transformers not installed, theme content consistency skipped"
        )
        pairs = [_pair_scores(a, b, None) for a, b in combinations(counts, 2)]
        return {**_mean_pair_scores(pairs), **result}

    assignment = _assign_tracks(themes_per_run, embeddings)
    return {
        **_mean_pair_scores(_track_f1(assignment >= 0)),
        **result,
        "tracks": _describe_tracks(themes_per_run, assignment),
    }


def output_consistency(
    outputs: list[Any], embed: Embed | None = None
) -> dict[str, Any] | None:
    """How alike a case's outputs are across runs, scored over every pair of runs.

    `f1` asks whether the same themes appear (matched by meaning, so rewordings count
    as the same) and `count` whether the same number appear. None when fewer than two
    runs produced an output.
    """
    present = [output for output in outputs if isinstance(output, dict)]
    if len(present) < 2:
        return None
    if all("labels" in output for output in present):
        return _label_consistency(present)
    return _theme_consistency(present, embed or _default_embed)


def consistency_by_case(
    outcomes: list[CaseOutcome], embed: Embed | None = None
) -> dict[str, dict[str, Any]]:
    """output_consistency per case key, for cases with at least two successful runs."""
    outputs: dict[str, list[Any]] = defaultdict(list)
    for outcome in outcomes:
        if outcome.error is None:
            outputs[outcome.case.key].append(outcome.output)
    return {
        case_key: value
        for case_key, case_outputs in outputs.items()
        if (value := output_consistency(case_outputs, embed)) is not None
    }


def aggregate(
    outcomes: list[CaseOutcome], embed: Embed | None = None
) -> dict[str, Any]:
    """The per-metric summary plus output consistency, as one block for the results."""
    consistency = consistency_by_case(outcomes, embed)
    return {
        "metrics": summarise_runs(outcomes),
        CONSISTENCY_METRIC: {
            **_mean_pair_scores(list(consistency.values())),
            "by_case": consistency,
        },
    }
