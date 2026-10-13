import json

import pytest
from ci import build_baselines, check_metrics
from components import COMPONENT_NAMES


class BuildBaselinesBase:
    """Writes fake eval runs then hands them to whichever entry point a subclass tests."""

    @staticmethod
    def write_run(root, f1, *, error=None, metric="f1"):
        for component in COMPONENT_NAMES:
            path = root / component / "d" / "results.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "outcomes": [
                            {
                                "error": error,
                                "scores": [
                                    {"name": metric, "value": f1, "comment": ""}
                                ],
                            }
                        ],
                        "errors": {},
                    }
                ),
                encoding="utf-8",
            )

    @classmethod
    def write_runs(cls, root, f1s, *, metric="f1", error=None):
        """Write one run per score and return the run directories.

        `error` is set on the last run only, since one bad run is enough to reject.
        """
        runs = [root / f"run{i}" for i in range(len(f1s))]
        for i, (run, f1) in enumerate(zip(runs, f1s)):
            bad = error if i == len(runs) - 1 else None
            cls.write_run(run, f1, metric=metric, error=bad)
        return runs

    def run(self, tmp_path, f1s, *, metric="f1", error=None, **kwargs):
        runs = self.write_runs(tmp_path, f1s, metric=metric, error=error)
        return self.execute(runs, tmp_path, **kwargs)

    def execute(self, runs, tmp_path, **kwargs):
        raise NotImplementedError


class TestBuildBaseline(BuildBaselinesBase):
    def execute(self, runs, tmp_path, *, k=3.0, floor=0.05, judge_floor=0.5):
        return build_baselines.build_baseline(
            "mapping", runs, "d", k, floor, judge_floor
        )

    def test_baseline_is_mean_and_tolerance_scales_with_spread(self, tmp_path):
        metrics = self.run(tmp_path, (0.5, 0.7, 0.9), k=1.0)

        assert metrics == {"f1": {"baseline": 0.7, "tolerance": 0.2}}

    def test_tolerance_floor_depends_on_metric_scale(self, tmp_path):
        unit = self.run(tmp_path / "unit", (0.8, 0.8))
        judge = self.run(tmp_path / "judge", (5.0, 5.0))

        assert unit["f1"]["tolerance"] == 0.05
        assert judge["f1"]["tolerance"] == 0.5

    def test_lower_is_better_metrics_record_their_direction(self, tmp_path):
        metrics = self.run(tmp_path, (0.0, 0.0), metric="redundancy")

        assert metrics["redundancy"]["direction"] == "lower"

    def test_runs_with_errors_are_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="errors"):
            self.run(tmp_path, (0.8, 0.8), error="boom")


class TestBuildBaselineMain(BuildBaselinesBase):
    def execute(self, runs, tmp_path):
        """Build baselines via the CLI, then return the gate's exit code against them."""
        out = tmp_path / "baselines"
        build_baselines.main(
            ["--dataset", "d", "--runs", *map(str, runs), "--out", str(out)]
        )
        return check_metrics.main(
            [
                "--dataset",
                "d",
                "--results-dir",
                str(runs[0]),
                "--baselines-dir",
                str(out),
            ]
        )

    def test_main_writes_files_the_gate_accepts(self, tmp_path):
        assert self.run(tmp_path, (0.78, 0.8, 0.82)) == 0
