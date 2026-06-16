#!/usr/bin/env python3
"""Run find_themes locally on a consultation directory, skipping S3 and Slack."""

import asyncio
import logging
import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "pipeline-sign-off"))
sys.path.insert(0, str(repo_root.parent / "themefinder" / "src"))

from find_themes_script import process_consultation  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

DEFAULT_MODEL = "gpt-4o"

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run find_themes locally on a consultation directory.")
    parser.add_argument("consultation_dir", help="Path to the consultation directory")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name to use (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    consultation_dir = args.consultation_dir
    model_name = args.model

    output_dir = asyncio.run(process_consultation(consultation_dir, model_name))
    print(f"Output written to: {output_dir}")
