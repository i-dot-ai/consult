"""Tests for cross-run statistics: consistency scores and theme tracking."""

import numpy as np
import pytest
from utils import stats

# Themes in the same group are rewordings of one another; different groups are unrelated.
_GROUPS = {
    "Ad bans": 0,
    "Advertising restrictions": 0,
    "Age checks": 1,
    "Age verification": 1,
    "Betting tax": 2,
    "Problem gambling support": 3,
}


def _fake_embed(texts: list[str]) -> np.ndarray:
    """One-hot vector per group, so rewordings have similarity 1 and others 0."""
    vectors = np.zeros((len(texts), len(set(_GROUPS.values()))))
    for row, text in enumerate(texts):
        vectors[row, _GROUPS[text.split(":")[0]]] = 1.0
    return vectors


def _run(*labels: str) -> dict:
    # No description, so the embedded text is the label itself
    return {"themes": [{"topic_label": label} for label in labels]}


def _consistency(*runs: dict) -> dict:
    return stats.output_consistency(list(runs), embed=_fake_embed)


class TestOutputConsistency:
    def test_identical_runs_score_one(self):
        result = _consistency(
            _run("Ad bans", "Age checks"), _run("Ad bans", "Age checks")
        )

        assert (result["f1"], result["count"]) == (1, 1)

    def test_rewording_still_counts_as_the_same_theme(self):
        result = _consistency(
            _run("Ad bans", "Age checks"),
            _run("Advertising restrictions", "Age checks"),
        )

        assert result["f1"] == 1.0

    def test_extra_theme_lowers_both_f1_and_count(self):
        result = _consistency(
            _run("Ad bans", "Age checks"), _run("Ad bans", "Age checks", "Betting tax")
        )

        # 2 shared themes over 2 + 3 themes
        assert result["f1"] == pytest.approx(0.8)
        assert result["count"] == pytest.approx(2 / 3)

    def test_swapped_theme_lowers_f1_not_count(self):
        result = _consistency(
            _run("Ad bans", "Age checks"), _run("Ad bans", "Betting tax")
        )

        assert result["f1"] == 0.5
        assert result["count"] == 1.0

    def test_scores_average_over_every_pair_of_runs(self):
        result = _consistency(_run("Ad bans"), _run("Ad bans"), _run("Betting tax"))

        # Pairs (0,1)=1, (0,2)=0, (1,2)=0
        assert result["f1"] == pytest.approx(1 / 3)

    def test_f1_comes_from_tracks_so_a_dropped_theme_still_links_up(self):
        """Run 2 brings back run 0's theme after run 1 dropped it: one track, so runs
        0 and 2 share it."""
        result = _consistency(
            _run("Ad bans", "Betting tax"),
            _run("Ad bans"),
            _run("Ad bans", "Betting tax"),
        )

        # Pairs (0,1)=2/3, (0,2)=1, (1,2)=2/3
        assert result["f1"] == pytest.approx((2 / 3 + 1 + 2 / 3) / 3)

    def test_reports_theme_count_spread(self):
        result = _consistency(
            _run("Ad bans"), _run("Ad bans", "Age checks", "Betting tax")
        )

        assert result["n_themes"]["mean"] == 2.0
        assert result["n_themes"]["stdev"] == pytest.approx(1.4142, rel=1e-3)

    def test_both_empty_is_fully_consistent(self):
        result = _consistency(_run(), _run())

        assert (result["f1"], result["count"]) == (1, 1)

    def test_one_empty_scores_zero(self):
        result = _consistency(_run("Ad bans"), _run())

        assert result["f1"] == 0.0
        assert result["count"] == 0.0

    def test_needs_two_outputs(self):
        assert _consistency(_run("Ad bans")) is None

    def test_mapping_labels_match_exactly(self):
        result = stats.output_consistency(
            [{"labels": {"r1": ["A", "B"]}}, {"labels": {"r1": ["A"]}}]
        )

        # 1 shared pair over 2 + 1 pairs
        assert result["f1"] == pytest.approx(2 / 3)
        assert result["count"] == 0.5
        assert "tracks" not in result

    def test_missing_embedding_model_keeps_count(self, monkeypatch):
        monkeypatch.setattr(stats, "find_spec", lambda name: None)

        result = stats.output_consistency(
            [_run("Ad bans"), _run("Ad bans", "Age checks")]
        )

        assert result["f1"] is None
        assert result["count"] == 0.5

    def test_import_error_inside_custom_embed_is_raised(self):
        def _broken(texts):
            raise ImportError("bad internal import")

        with pytest.raises(ImportError, match="bad internal import"):
            stats.output_consistency(
                [_run("Ad bans"), _run("Ad bans", "Age checks")], embed=_broken
            )


class TestTrackThemes:
    def test_rewording_is_one_reworded_track(self):
        tracks = _consistency(_run("Ad bans"), _run("Advertising restrictions"))[
            "tracks"
        ]

        assert tracks["counts"] == {"stable": 0, "reworded": 1, "intermittent": 0}
        assert tracks["themes"] == [
            {"status": "reworded", "labels": ["Ad bans", "Advertising restrictions"]}
        ]
        assert tracks["changes"][0]["reworded"] == [
            ["Ad bans", "Advertising restrictions"]
        ]
        assert tracks["changes"][0]["dropped"] == []

    def test_description_only_rewording_shows_descriptions(self):
        tracks = _consistency(
            {
                "themes": [
                    {"topic_label": "Ad bans", "topic_description": "Ban all ads"}
                ]
            },
            {"themes": [{"topic_label": "Ad bans", "topic_description": "Limit ads"}]},
        )["tracks"]

        assert tracks["counts"]["reworded"] == 1
        assert tracks["changes"][0]["reworded"] == [
            ["Ad bans: Ban all ads", "Ad bans: Limit ads"]
        ]

    def test_theme_dropped_then_back_is_one_intermittent_track(self):
        tracks = _consistency(
            _run("Ad bans", "Betting tax"),
            _run("Ad bans"),
            _run("Ad bans", "Betting tax"),
        )["tracks"]

        assert tracks["counts"] == {"stable": 1, "reworded": 0, "intermittent": 1}
        assert {
            "status": "intermittent",
            "labels": ["Betting tax", None, "Betting tax"],
        } in (tracks["themes"])
        assert tracks["changes"][0]["dropped"] == ["Betting tax"]
        assert tracks["changes"][1]["appeared"] == ["Betting tax"]

    def test_new_theme_in_last_run_appears(self):
        tracks = _consistency(
            _run("Ad bans"), _run("Ad bans", "Problem gambling support")
        )["tracks"]

        assert tracks["changes"] == [
            {
                "from_run": 0,
                "to_run": 1,
                "dropped": [],
                "appeared": ["Problem gambling support"],
                "reworded": [],
            }
        ]
