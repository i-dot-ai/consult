"""Live checks that LLM-judge prompts work against a real LLM.

The fake-judge tests prove the plumbing; only a real model can show the prompt
actually separates a valid rewording from an unrelated theme. Skipped unless
gateway credentials are set.

The binary-match tests share one scenario: two original themes are refined into
two new ones. The clarity test separately checks clear and opaque wording.

    original                  refined
    ORIGINAL_BAN_ADVERTS  ->  REWORDED_BAN_ADVERTS   valid rewording, same information
    ORIGINAL_AGE_CHECKS   ->  (nothing)              LOST: no refined theme carries it
    (nothing)             <-  INVENTED_RAISE_TAX     INVENTED: no original behind it
"""

import pytest
from adapters.evaluators.clarity_evaluator import ClarityEvaluator
from adapters.evaluators.information_equivalence_evaluator import (
    InformationEquivalenceEvaluator,
)
from conftest import make_case
from run_eval import _create_default_llm
from settings import eval_settings


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

CLEAR_THEME = _theme(
    "Ban gambling adverts", "Gambling adverts should be banned to reduce their harm."
)
UNCLEAR_THEME = _theme(
    "Quasifractual operationalisation",
    (
        "The ontological and epistemic ramifications of policy-related modalities "
        "constitute a nontrivially ambiguous, semantically indeterminate constellation."
    ),
)

ORIGINAL_THEMES = [ORIGINAL_KEPT_BAN_ADVERTS, ORIGINAL_LOST_AGE_CHECKS]
REFINED_THEMES = [REWORDED_BAN_ADVERTS, INVENTED_RAISE_TAX]


@pytest.fixture
def judge():
    """The default gateway model, or a skip when credentials are not configured."""
    if not eval_settings.gateway.url or not eval_settings.gateway.api_key:
        pytest.skip("LLM gateway credentials not set")
    return _create_default_llm(eval_settings)


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


async def test_clarity_distinguishes_clear_and_unclear_theme_wording(judge):
    """The live judge accepts simple wording and rejects opaque jargon."""
    case = make_case(inputs={"themes": ORIGINAL_THEMES})

    (score,) = await ClarityEvaluator(judge).evaluate(
        case, {"themes": [CLEAR_THEME, UNCLEAR_THEME]}
    )

    assert score.name == "clarity"
    assert score.value == 0.5
    assert score.comment.startswith(
        "1/2 themes passed\nFailed:\n  Quasifractual operationalisation — "
    )
