"""Minimal check that a key/model works with themefinder's LLM.

Run:  uv run python scripts/test_keys_and_models.py
Reads LLM_GATEWAY_URL / LITELLM_CONSULT_OPENAI_API_KEY from the repo-root .env.
Override the model with MODEL=... (gateway model name, e.g. gpt-4o-sweden).
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from themefinder import LLM
from themefinder.models import ThemeGenerationResponses

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MODEL = os.environ.get("MODEL", "gpt-4.1")


async def main() -> None:
    llm = LLM(
        MODEL,
        base_url=os.environ["LLM_GATEWAY_URL"],
        api_key=os.environ["LITELLM_CONSULT_OPENAI_API_KEY"],
        temperature=0,
    )

    text = await llm.ainvoke("Reply with exactly the single word: pong")
    print("text:", text.parsed)

    structured = await llm.ainvoke(
        "Extract up to two themes from: 'Ban gambling ads, they harm children' "
        "and 'Don't ban them, clubs need the sponsorship money'.",
        output_model=ThemeGenerationResponses,
    )
    for theme in structured.parsed.responses:
        print("theme:", theme.topic_label, "-", theme.position.value)


if __name__ == "__main__":
    asyncio.run(main())
