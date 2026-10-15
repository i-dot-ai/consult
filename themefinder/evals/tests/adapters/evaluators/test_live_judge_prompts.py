"""Live checks that the binary-match judge prompts work against a real LLM.

The fake-judge tests prove the plumbing; only a real model can show the prompt
actually separates a valid rewording from an unrelated theme. Skipped unless
gateway credentials are set.

Both tests share one scenario: two original themes are refined into two new ones.

    original                  refined
    ORIGINAL_BAN_ADVERTS  ->  REWORDED_BAN_ADVERTS   valid rewording, same information
    ORIGINAL_AGE_CHECKS   ->  (nothing)              LOST: no refined theme carries it
    (nothing)             <-  INVENTED_RAISE_TAX     INVENTED: no original behind it
"""

import pytest
from adapters.evaluators.ground_information_evaluator import (
    GroundednessInformationRetentionEvaluator,
)
from adapters.evaluators.information_equivalence_evaluator import (
    InformationEquivalenceEvaluator,
)
from conftest import make_case
from run_eval import _create_default_llm
from settings import get_settings


def _theme(label: str, description: str) -> dict[str, str]:
    return {"topic_id": label, "topic_label": label, "topic_description": description}


ORIGINAL_KEPT_BAN_ADVERTS = _theme(
    "Ban gambling adverts", "Gambling advertising should be banned outright."
)
ORIGINAL_LOST_AGE_CHECKS = _theme(
    "Stricter age checks", "Operators should verify customers are over 18."
)

# Same information as ORIGINAL_BAN_ADVERTS in different words: should match it.
REWORDED_BAN_ADVERTS = _theme(
    "Advertising restrictions", "Gambling adverts should be prohibited."
)
# Unrelated to either original: should match nothing.
INVENTED_RAISE_TAX = _theme("Raise betting tax", "Betting duty should be increased.")

ORIGINAL_THEMES = [ORIGINAL_KEPT_BAN_ADVERTS, ORIGINAL_LOST_AGE_CHECKS]
REFINED_THEMES = [REWORDED_BAN_ADVERTS, INVENTED_RAISE_TAX]


@pytest.fixture
def judge():
    """The default gateway model, or a skip when credentials are not configured."""
    settings = get_settings()
    if not settings.gateway.url or not settings.gateway.api_key:
        pytest.skip("LLM gateway credentials not set")
    return _create_default_llm(settings)


async def test_ground_information_flags_invented_and_lost_themes(judge):
    """The reworded theme counts as grounded and retained; the invented theme is
    reported ungrounded and the dropped original is reported lost."""
    case = make_case(expected_output={"themes": ORIGINAL_THEMES})

    scores = {
        s.name: s
        for s in await GroundednessInformationRetentionEvaluator(judge).evaluate(
            case, {"themes": REFINED_THEMES}
        )
    }

    # Groundedness: 1 of 2 refined themes has an original (the rewording).
    assert scores["groundedness"].value == 0.5
    assert (
        f"Ungrounded: {INVENTED_RAISE_TAX['topic_label']}"
        in scores["groundedness"].comment
    )
    # Retention: 1 of 2 originals survives (the rewording's original).
    assert scores["information_retention"].value == 0.5
    assert (
        f"Lost: {ORIGINAL_LOST_AGE_CHECKS['topic_label']}"
        in scores["information_retention"].comment
    )


async def test_information_equivalence_pairs_only_the_reworded_theme(judge):
    """Only the reworded theme pairs one-to-one with its original; the invented
    and lost themes leave the other half of each list unpaired."""
    case = make_case(inputs={"themes": ORIGINAL_THEMES})

    (score,) = await InformationEquivalenceEvaluator(judge).evaluate(
        case, {"themes": REFINED_THEMES}
    )

    assert score.name == "information_equivalence"
    assert not score.comment.startswith("Error:")
    # 1 reciprocal pair (ban adverts <-> advertising restrictions) out of 2.
    assert score.comment.startswith("1/2 reciprocal one-to-one pairs")
