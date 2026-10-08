"""Build regression baselines from several repeated eval runs.

LLM evals are stochastic, so a single run is a poor reference. Using the spread across
repeated runs sets tolerances that match real noise instead of a guess.
"""

import argparse
import json
import statistics
import sys
from collections.abc import Sequence
from pathlib import Path

import yaml
from ci.check_metrics import summarise_payload
from components import COMPONENT_NAMES

EVALS_DIR = Path(__file__).resolve().parents[1]
LOWER_IS_BETTER = frozenset({"redundancy"})
REQUIRED_RUNS = 3


def build_baseline(
    component: str,
    run_dirs: Sequence[Path],
    dataset: str,
    k: float,
    floor: float,
    judge_floor: float,
) -> dict:
    per_run: dict[str, list[float]] = {}
    for run_dir in run_dirs:
        path = run_dir / component / dataset / "results.json"
        means, n_cases, n_errors = summarise_payload(
            json.loads(path.read_text("utf-8"))
        )
        if n_errors or not n_cases:
            raise ValueError(f"{path} has {n_errors} errors and {n_cases} cases")
        for metric, value in means.items():
            per_run.setdefault(metric, []).append(value)

    # shortcut: a score above 1 means a 1-5 judge metric; a judge metric that only ever
    # scores exactly 1.0 gets the stricter 0-1 floor. Upgrade if evaluators declare a scale.
    return {
        name: {
            "baseline": round(statistics.mean(values), 4),
            "tolerance": round(
                max(
                    judge_floor if max(values) > 1 else floor,
                    k * statistics.stdev(values),
                ),
                4,
            ),
            **({"direction": "lower"} if name in LOWER_IS_BETTER else {}),
        }
        for name, values in sorted(per_run.items())
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="gambling_XS")
    parser.add_argument(
        "--runs", nargs="+", type=Path, required=True, help="local_eval_runs copies"
    )
    parser.add_argument(
        "--component", choices=COMPONENT_NAMES, help="Only build one component"
    )
    parser.add_argument(
        "--k", type=float, default=3.0, help="Tolerance in standard deviations"
    )
    parser.add_argument(
        "--floor", type=float, default=0.05, help="Minimum tolerance, 0-1 metrics"
    )
    parser.add_argument(
        "--judge-floor",
        type=float,
        default=0.5,
        help="Minimum tolerance, 1-5 judge metrics (one case moving a point on 2 cases)",
    )
    parser.add_argument("--out", type=Path, default=EVALS_DIR / "baselines")
    args = parser.parse_args(argv)
    if len(args.runs) < REQUIRED_RUNS:
        parser.error(
            f"At least {REQUIRED_RUNS} runs are required to build a baseline, got {len(args.runs)}"
        )

    params = yaml.safe_load((EVALS_DIR / "params.yaml").read_text("utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)

    components = [args.component] if args.component else COMPONENT_NAMES

    for component in components:
        baseline = {
            "header": {
                "dataset": args.dataset,
                "dataset_revision": params["dataset"]["revision"],
                "model": params["evals"][component]["model"],
                "n_runs": len(args.runs),
                "tolerance": (
                    f"max({args.floor} for 0-1 metrics or {args.judge_floor} for 1-5 "
                    f"judge metrics, {args.k} * stdev across runs)"
                ),
            },
            "metrics": build_baseline(
                component,
                args.runs,
                args.dataset,
                args.k,
                args.floor,
                args.judge_floor,
            ),
        }
        path = args.out / f"{component}_{args.dataset}.json"
        path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
