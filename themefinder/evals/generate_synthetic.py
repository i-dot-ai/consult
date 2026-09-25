#!/usr/bin/env python
"""Interactive CLI for generating synthetic consultation datasets.

Usage:
    cd evals && uv run python generate_synthetic.py

This tool guides you through creating a synthetic dataset for ThemeFinder evaluation,
including:
- Defining the consultation topic and questions
- Configuring number of responses
- Configuring demographic fields
- Reviewing generated themes before committing to a full run
- Previewing example responses before committing to a full run
- Generating diverse responses with controlled characteristics
"""

import asyncio
import os
import sys
from contextlib import nullcontext
from typing import Any

import openai

# Add parent to path for imports
sys.path.insert(0, str(os.path.dirname(__file__)))

from synthetic.cli import (
    create_progress_bar,
    print_error,
    review_generated_themes,
    review_preview_samples,
    print_success,
    run_interactive_cli,
)
from datasets import publish_local_dataset_to_langfuse
from synthetic.config import RESPONSE_GENERATION_MODEL
from synthetic.generator import SyntheticDatasetGenerator
from utils import gateway

# Optional Langfuse integration
try:
    from langfuse.openai import AsyncOpenAI as _LangfuseOpenAI
    from utils import langfuse

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


def _create_gateway_client() -> tuple[Any, str, str]:
    """Create the gateway-routed OpenAI-compatible client used by the script."""
    client_class: Any = openai.AsyncOpenAI
    if LANGFUSE_AVAILABLE:
        client_class = _LangfuseOpenAI

    base_url, api_key = gateway.gateway_credentials()
    client = client_class(
        base_url=base_url,
        api_key=api_key,
        timeout=600,
    )
    return client, base_url, api_key


async def main() -> None:
    """Main entry point for synthetic dataset generation."""
    # Collect configuration interactively
    try:
        config = await run_interactive_cli()
    except SystemExit as e:
        print(str(e))
        return

    client, base_url, _ = _create_gateway_client()

    # Optional Langfuse tracking
    langfuse_ctx = None

    if LANGFUSE_AVAILABLE:
        langfuse_ctx = langfuse.get_langfuse_context(
            session_id=f"synthetic_{config.dataset_name}",
            eval_type="synthetic_generation",
            metadata={
                "dataset": config.dataset_name,
                "n_responses": config.n_responses,
                "gateway_base_url": base_url,
                "response_generation_model": RESPONSE_GENERATION_MODEL,
            },
            tags=[config.dataset_name, "synthetic"],
        )

    # Initialise generator
    generator = SyntheticDatasetGenerator(
        config=config,
        llm=(client, RESPONSE_GENERATION_MODEL),
    )

    # Calculate total responses for summary
    total_responses = config.n_responses * len(config.questions)

    # Run generation with explicit review checkpoints between phases.
    progress = create_progress_bar()
    output_path = None
    n_themes = 0

    _trace = (
        langfuse.trace_context(langfuse_ctx, name="synthetic_generation")
        if langfuse_ctx
        else nullcontext()
    )

    try:
        with _trace:
            with progress:
                themes_by_question = await generator.generate_themes(progress)

            while True:
                action, question_number = review_generated_themes(
                    config.questions,
                    themes_by_question,
                )
                if action == "approve":
                    break
                if action == "regenerate_all":
                    progress = create_progress_bar()
                    continue

                progress = create_progress_bar()
                with progress:
                    themes_by_question[
                        question_number
                    ] = await generator.regenerate_themes_for_question(
                        question_number,
                        progress,
                    )

            while True:
                progress = create_progress_bar()
                with progress:
                    preview_responses = await generator.generate_preview_samples(
                        themes_by_question,
                        progress,
                    )

                preview_action = review_preview_samples(
                    config.questions,
                    preview_responses,
                    themes_by_question,
                )
                if preview_action == "continue":
                    break
                if preview_action == "regenerate_preview":
                    continue

                while True:
                    action, question_number = review_generated_themes(
                        config.questions,
                        themes_by_question,
                    )
                    if action == "approve":
                        break
                    if action == "regenerate_all":
                        progress = create_progress_bar()
                        with progress:
                            themes_by_question = await generator.generate_themes(
                                progress
                            )
                        continue

                    progress = create_progress_bar()
                    with progress:
                        themes_by_question[
                            question_number
                        ] = await generator.regenerate_themes_for_question(
                            question_number,
                            progress,
                        )

                continue

            progress = create_progress_bar()
            with progress:
                output_path = await generator.write_full_dataset(
                    themes_by_question,
                    progress,
                )

            if langfuse_ctx and langfuse_ctx.client:
                publish_local_dataset_to_langfuse(
                    langfuse_ctx.client,
                    config.dataset_name,
                )

        # Count themes from first question for summary (after progress bar closes)
        themes_file = (
            output_path
            / "outputs"
            / "mapping"
            / generator.writer.date_str
            / "question_part_1"
            / "themes.json"
        )
        if themes_file.exists():
            import json

            with open(themes_file) as f:
                n_themes = len(json.load(f))

        print_success(str(output_path), n_themes, total_responses)

    except Exception as e:
        print_error(e)
        raise

    finally:
        if LANGFUSE_AVAILABLE and langfuse_ctx:
            langfuse.flush(langfuse_ctx)


if __name__ == "__main__":
    asyncio.run(main())
