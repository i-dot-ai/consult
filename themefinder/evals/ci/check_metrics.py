"""Gate eval results against committed baselines.

LLM evals never fail on their own when quality drops, so CI needs a separate verdict.
Exit codes: 0 pass, 1 metric regression, 2 invalid results or missing baseline.
"""

import argparse
import json
import math
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from components import COMPONENT_NAMES
from utils.results import count_errors

PASS, REGRESSION, INVALID = 0, 1, 2
EPSILON = (
    1e-9  # avoids float noise flipping scores that sit exactly on the tolerance edge
)


@dataclass
class Row:
    component: str
    metric: str
    score: float | None
    baseline: float
    tolerance: float
    status: str


@dataclass
class ComponentVerdict:
    component: str
    rows: list[Row] = field(default_factory=list)
    invalid: str | None = None
    regressions: list[str] = field(default_factory=list)


def summarise_payload(payload: dict) -> tuple[dict[str, float], int, int]:
    """Return per-metric means, case count and error count from a full results payload."""
    outcomes = payload["outcomes"]
    values: dict[str, list[float]] = {}
    for outcome in outcomes:
        for score in outcome.get("scores", []):
            values.setdefault(score["name"], []).append(score["value"])
    means = {
        name: sum(vals) / len(vals)
        for name, vals in values.items()
        if all(isinstance(v, int | float) and math.isfinite(v) for v in vals)
    }
    non_finite = sorted(set(values) - set(means))
    if non_finite:
        raise ValueError(f"non-finite or non-numeric scores for {non_finite}")
    return means, len(outcomes), count_errors(payload)


def metric_means(payload: dict | None, baseline: dict | None) -> dict[str, float]:
    """Return per-metric means, or raise ValueError with the first reason the run can't be judged."""
    if payload is None or baseline is None:
        raise ValueError("cannot read results or baseline file")
    try:
        means, n_cases, n_errors = summarise_payload(payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"malformed results, {exc!r} (was the local artefact store used?)"
        ) from exc
    if n_errors or not n_cases:
        raise ValueError(
            f"{n_cases} cases evaluated, {n_errors} case or evaluator errors"
        )
    return means


def check_component(
    component: str, payload: dict | None, baseline: dict | None
) -> ComponentVerdict:
    verdict = ComponentVerdict(component)
    try:
        means = metric_means(payload, baseline)
    except ValueError as exc:
        verdict.invalid = str(exc)
        return verdict

    for metric, spec in sorted(baseline["metrics"].items()):
        score = means.get(metric)
        base, tol = spec["baseline"], spec["tolerance"] + EPSILON
        if score is None:
            verdict.rows.append(Row(component, metric, None, base, tol, "MISSING"))
            verdict.regressions.append(f"{component}.{metric} missing from results")
            continue

        # How much worse than baseline; metrics like redundancy are worse when they rise.
        worse = score - base if spec.get("direction") == "lower" else base - score

        if abs(worse) < tol:
            result = "OK"
        else:
            result = "REGRESSED" if worse > tol else "IMPROVED"

        verdict.rows.append(Row(component, metric, score, base, tol, result))

        if result == "REGRESSED":
            verdict.regressions.append(f"{component}.{metric} regressed by {worse:.3f}")

    return verdict


def render_summary(verdicts: Sequence[ComponentVerdict], dataset: str) -> str:
    lines = [
        f"### Eval metrics vs baseline (`{dataset}`)",
        "",
        "| Component | Metric | Score | Baseline | Tolerance | Status |",
        "|---|---|---|---|---|---|",
    ]
    for verdict in verdicts:
        for r in verdict.rows:
            score = "n/a" if r.score is None else f"{r.score:.3f}"
            lines.append(
                f"| {r.component} | {r.metric} | {score} | {r.baseline:.3f} "
                f"| {r.tolerance:.3f} | {r.status} |"
            )
    problems = [f"- **{v.component}**: {v.invalid}" for v in verdicts if v.invalid]
    if problems:
        lines += ["", "Invalid results:", *problems]
    if any(r.status == "IMPROVED" for v in verdicts for r in v.rows):
        lines += [
            "",
            "Some metrics improved beyond tolerance: consider updating the baseline.",
        ]
    return "\n".join(lines) + "\n"


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def run(results_dir: Path, baselines_dir: Path, dataset: str) -> tuple[int, str]:
    verdicts = [
        check_component(
            component,
            _load_json(results_dir / component / dataset / "results.json"),
            _load_json(baselines_dir / f"{component}_{dataset}.json"),
        )
        for component in COMPONENT_NAMES
    ]
    summary = render_summary(verdicts, dataset)
    if any(v.invalid for v in verdicts):
        return INVALID, summary
    if any(v.regressions for v in verdicts):
        return REGRESSION, summary
    return PASS, summary


def main(argv: Sequence[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--results-dir", type=Path, default=root / "local_eval_runs")
    parser.add_argument("--baselines-dir", type=Path, default=root / "baselines")
    parser.add_argument(
        "--summary-file",
        type=Path,
        help="Append the Markdown table here (GITHUB_STEP_SUMMARY)",
    )
    args = parser.parse_args(argv)

    code, summary = run(args.results_dir, args.baselines_dir, args.dataset)
    print(summary)
    if args.summary_file:
        with args.summary_file.open("a", encoding="utf-8") as handle:
            handle.write(summary)
    return code


if __name__ == "__main__":
    sys.exit(main())
