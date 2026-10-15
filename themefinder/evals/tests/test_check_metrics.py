import json

from ci import check_metrics
from components import COMPONENT_NAMES


def payload(scores, *, error=None, comment=""):
    return {
        "component": "x",
        "dataset": "d",
        "results": {},
        "errors": {},
        "outcomes": [
            {
                "case": {"id": f"c{i}"},
                "output": None,
                "error": error,
                "scores": [
                    {"name": n, "value": v, "comment": comment} for n, v in s.items()
                ],
            }
            for i, s in enumerate(scores)
        ],
    }


BASELINE = {"metrics": {"f1": {"baseline": 0.8, "tolerance": 0.1}}}

LOWER = {
    "metrics": {
        "redundancy": {"baseline": 0.1, "tolerance": 0.05, "direction": "lower"}
    }
}


class TestCheckComponent:
    @staticmethod
    def run_component(p, baseline=BASELINE):
        """Run check_component on a payload so tests only state the scenario."""
        return check_metrics.check_component("mapping", p, baseline)

    def test_within_tolerance_passes(self):
        v = self.run_component(payload([{"f1": 0.75}, {"f1": 0.77}]))
        assert not v.invalid and not v.regressions
        assert v.rows[0].status == "OK"

    def test_mean_across_cases_is_used(self):
        v = self.run_component(payload([{"f1": 0.9}, {"f1": 0.5}]))  # mean 0.7
        assert not v.regressions

    def test_drop_beyond_tolerance_regresses(self):
        v = self.run_component(payload([{"f1": 0.6}]))
        assert v.regressions and v.rows[0].status == "REGRESSED"

    def test_improvement_is_flagged_not_failed(self):
        v = self.run_component(payload([{"f1": 0.99}]))
        assert not v.regressions and v.rows[0].status == "IMPROVED"

    def test_lower_is_better_metric_regresses_when_it_rises(self):
        v = self.run_component(payload([{"redundancy": 0.3}]), LOWER)
        assert v.regressions and v.rows[0].status == "REGRESSED"

    def test_missing_metric_regresses(self):
        v = self.run_component(payload([{"other": 1.0}]))
        assert v.rows[0].status == "MISSING" and v.regressions

    def test_case_error_is_invalid(self):
        assert self.run_component(payload([{"f1": 0.8}], error="boom")).invalid

    def test_zeroed_judge_score_is_invalid_not_a_low_score(self):
        v = self.run_component(payload([{"f1": 0.0}], comment="Error: judge timed out"))
        assert v.invalid

    def test_no_cases_is_invalid(self):
        assert self.run_component(payload([])).invalid

    def test_fallback_shaped_results_are_invalid(self):
        assert self.run_component(
            {"component": "x", "dataset": "d", "results": {}}
        ).invalid

    def test_missing_files_are_invalid(self):
        assert self.run_component(None).invalid
        assert self.run_component(payload([{"f1": 0.8}]), baseline=None).invalid


class TestCheckMetrics:
    @staticmethod
    def write_all(tmp_path, f1):
        results, baselines = tmp_path / "runs", tmp_path / "baselines"
        baselines.mkdir(parents=True)
        for c in COMPONENT_NAMES:
            (results / c / "d").mkdir(parents=True)
            (results / c / "d" / "results.json").write_text(
                json.dumps(payload([{"f1": f1}])), encoding="utf-8"
            )
            (baselines / f"{c}_d.json").write_text(
                json.dumps(BASELINE), encoding="utf-8"
            )
        return results, baselines

    @staticmethod
    def args(results, baselines, *extra):
        return [
            "--dataset",
            "d",
            "--results-dir",
            str(results),
            "--baselines-dir",
            str(baselines),
            *extra,
        ]

    def test_main_exit_codes_and_summary_file(self, tmp_path, capsys):
        results, baselines = self.write_all(tmp_path, 0.8)
        summary = tmp_path / "summary.md"
        argv = self.args(results, baselines, "--summary-file", str(summary))
        assert check_metrics.main(argv) == 0
        assert "| mapping | f1 |" in summary.read_text(encoding="utf-8")

        results, baselines = self.write_all(tmp_path / "bad", 0.1)
        assert check_metrics.main(self.args(results, baselines)) == 1

        (results / COMPONENT_NAMES[0] / "d" / "results.json").unlink()
        assert check_metrics.main(self.args(results, baselines)) == 2

    def test_every_component_is_checked(self, tmp_path):
        results, baselines = self.write_all(tmp_path, 0.8)
        code, summary = check_metrics.run(results, baselines, "d")
        assert code == 0
        assert all(f"| {c} |" in summary for c in COMPONENT_NAMES)
