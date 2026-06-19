"""Live inference tests that make real LLM calls through the Consult LiteLLM gateway.

They run as part of the normal suite. They skip (rather than fail) only when
gateway credentials are absent, so CI without secrets stays green while a
developer with a configured ``.env`` runs them automatically.

Credentials are read from the repo-root ``.env`` (``LLM_GATEWAY_URL`` and
``LITELLM_CONSULT_OPENAI_API_KEY`` — the same vars the production pipeline uses).
The model defaults to ``gpt-4.1`` (the Consult default) and can be overridden with
``LIVE_TEST_MODEL``. Real data comes from the tracked synthetic ``gambling_XS``
evaluation dataset.
"""

import json
import os
from pathlib import Path

import pandas as pd
import pytest
from dotenv import load_dotenv
from pydantic_ai import Agent, NativeOutput, ToolOutput

from themefinder import (
    detail_detection,
    find_themes,
    theme_generation,
    theme_mapping,
)
from themefinder.llm import LLM
from themefinder.models import (
    EvidenceRich,
    ThemeGenerationResponses,
)

# Load env from the repo root (.../consult/.env) and the package dir if present.
_PACKAGE_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _PACKAGE_DIR.parent
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_PACKAGE_DIR / ".env")

GATEWAY_URL = os.environ.get("LLM_GATEWAY_URL")
API_KEY = os.environ.get("LITELLM_CONSULT_OPENAI_API_KEY")
MODEL = os.environ.get("LIVE_TEST_MODEL", "gpt-4.1")

DATA_DIR = _PACKAGE_DIR / "evals" / "data" / "gambling_XS"
QUESTION = "Should gambling advertising during live sporting events be banned?"

pytestmark = pytest.mark.skipif(
    not (GATEWAY_URL and API_KEY),
    reason="LLM_GATEWAY_URL / LITELLM_CONSULT_OPENAI_API_KEY not set",
)

# A tiny self-contained structured-output prompt (no template machinery needed).
STRUCTURED_PROMPT = (
    "You are analysing public consultation responses about banning gambling "
    "advertising. Extract up to three distinct themes from these responses, each "
    "with a short topic_label, a one-sentence topic_description, and a position of "
    "AGREEMENT, DISAGREEMENT or UNCLEAR.\n"
    "Responses:\n"
    "1. Ban all gambling adverts, they normalise betting for children.\n"
    "2. A ban is overkill — sports clubs rely on this sponsorship money.\n"
    "3. Only restrict adverts during live sport when families are watching.\n"
)


@pytest.fixture(scope="module")
def llm() -> LLM:
    """Gateway-backed LLM at temperature 0 for repeatable output."""
    return LLM(MODEL, base_url=GATEWAY_URL, api_key=API_KEY, temperature=0)


@pytest.fixture(scope="module")
def responses_df() -> pd.DataFrame:
    """A small slice of the tracked synthetic gambling_XS responses."""
    path = DATA_DIR / "inputs" / "question_part_1" / "responses.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    df = pd.DataFrame(rows).head(12)
    return df[["response_id", "response"]]


# --- basic connectivity ------------------------------------------------------


async def test_gateway_returns_text_response(llm):
    """A plain (unstructured) call returns a non-empty text response."""
    result = await llm.ainvoke("Reply with exactly the single word: pong")
    assert isinstance(result.parsed, str)
    assert result.parsed.strip() != ""


# --- structured output: native vs tool (pydantic) mode -----------------------


async def test_wrapper_native_structured_output(llm):
    """The LLM wrapper's own path (NativeOutput) returns a validated model."""
    result = await llm.ainvoke(STRUCTURED_PROMPT, output_model=ThemeGenerationResponses)
    assert isinstance(result.parsed, ThemeGenerationResponses)
    assert len(result.parsed.responses) >= 1


@pytest.mark.parametrize(
    "output_type_factory",
    [
        pytest.param(NativeOutput, id="native"),
        pytest.param(ToolOutput, id="tool"),
    ],
)
async def test_structured_output_modes_through_gateway(llm, output_type_factory):
    """OpenAI structured output works through the gateway in BOTH modes:
    native JSON-schema (NativeOutput, the wrapper's choice) and tool-calling
    (ToolOutput, Pydantic AI's default). Exercises the same validator-bearing
    *Responses model both ways to surface provider variability."""
    agent = Agent(llm._model)
    result = await agent.run(
        STRUCTURED_PROMPT,
        output_type=output_type_factory(ThemeGenerationResponses),
        model_settings=llm._settings,
    )
    assert isinstance(result.output, ThemeGenerationResponses)
    assert len(result.output.responses) >= 1
    for theme in result.output.responses:
        assert theme.topic_label.strip()
        assert theme.topic_description.strip()


# --- individual tasks on real gambling_XS data -------------------------------


async def test_theme_generation_live(llm, responses_df):
    themes_df, unprocessable = await theme_generation(
        responses_df, llm, question=QUESTION, concurrency=5
    )
    assert not themes_df.empty
    assert {"topic_label", "topic_description", "position"}.issubset(themes_df.columns)
    assert unprocessable.empty


async def test_theme_mapping_live(llm, responses_df):
    refined_themes_df = pd.DataFrame(
        {
            "topic_id": ["A", "B", "C"],
            "topic": [
                "Support ban: The respondent supports banning gambling advertising.",
                "Oppose ban: The respondent opposes banning gambling advertising.",
                "Partial restriction: The respondent wants limits rather than a full ban.",
            ],
        }
    )
    mapped_df, unprocessable = await theme_mapping(
        responses_df,
        llm,
        question=QUESTION,
        refined_themes_df=refined_themes_df,
        concurrency=5,
    )
    assert not mapped_df.empty
    assert {"response_id", "labels"}.issubset(mapped_df.columns)
    # Integrity check is on: every input response should be mapped.
    assert unprocessable.empty
    assert set(mapped_df["response_id"]) == set(responses_df["response_id"])
    # Every assigned label is one of the known theme ids.
    known = set(refined_themes_df["topic_id"])
    for labels in mapped_df["labels"]:
        assert set(labels).issubset(known)


async def test_detail_detection_live(llm, responses_df):
    detail_df, unprocessable = await detail_detection(
        responses_df, llm, question=QUESTION, concurrency=5
    )
    assert not detail_df.empty
    assert "evidence_rich" in detail_df.columns
    assert unprocessable.empty
    valid = {EvidenceRich.YES, EvidenceRich.NO, "YES", "NO"}
    assert all(value in valid for value in detail_df["evidence_rich"])


# --- end-to-end pipeline -----------------------------------------------------


async def test_find_themes_end_to_end_live(llm, responses_df):
    result = await find_themes(
        responses_df, llm, question=QUESTION, concurrency=5, verbose=False
    )
    assert {
        "question",
        "themes",
        "mapping",
        "detailed_responses",
        "unprocessables",
    }.issubset(result)
    assert result["question"] == QUESTION
    assert not result["themes"].empty
    assert not result["mapping"].empty


# --- direct-provider sanity (only if a provider key is present) --------------


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set (direct-provider mode)",
)
async def test_direct_anthropic_structured_output():
    """Direct-to-provider routing (no gateway) via a provider-prefixed string."""
    llm = LLM("anthropic:claude-haiku-4-5", temperature=0)
    result = await llm.ainvoke(STRUCTURED_PROMPT, output_model=ThemeGenerationResponses)
    assert isinstance(result.parsed, ThemeGenerationResponses)
    assert len(result.parsed.responses) >= 1
