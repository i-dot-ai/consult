#!/usr/bin/env python
"""One-time migration of existing eval data to Langfuse datasets.

This script migrates all existing evaluation data to Langfuse datasets,
enabling the use of run_experiment() for systematic evaluation.

Usage:
    # Migrate all datasets for gambling_XS
    uv run python scripts/migrate_to_langfuse.py

    # Migrate specific dataset
    uv run python scripts/migrate_to_langfuse.py --dataset gambling_XS

    # Migrate specific component only
    uv run python scripts/migrate_to_langfuse.py --component generation
"""

import argparse
import os
import sys
from pathlib import Path

import dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import DatasetConfig, get_or_create_dataset, load_local_data


def get_langfuse_client():
    """Get Langfuse client, ensuring environment is configured."""
    dotenv.load_dotenv()

    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL")

    if not all([secret_key, public_key, base_url]):
        raise RuntimeError(
            "Langfuse not configured. Set LANGFUSE_SECRET_KEY, "
            "LANGFUSE_PUBLIC_KEY, and LANGFUSE_BASE_URL environment variables."
        )

    from langfuse import Langfuse

    return Langfuse(
        secret_key=secret_key,
        public_key=public_key,
        host=base_url,
    )


def migrate_component(client, dataset: str, component: str) -> None:
    """Migrate a single eval component to Langfuse.

    Args:
        client: Langfuse client
        dataset: Dataset identifier (e.g., "gambling_XS")
        component: Eval component (generation, mapping, condensation, refinement)
    """
    config = DatasetConfig(dataset=dataset, component=component)
    print(f"Migrating {config.name}...")

    # Load data using the unified loader
    try:
        items = load_local_data(config)
    except FileNotFoundError as e:
        print(f"  Skipping {config.name}: {e}")
        return

    # Create dataset in Langfuse
    get_or_create_dataset(client, config)

    # Create items
    for item in items:
        client.create_dataset_item(
            dataset_name=config.name,
            input=item["input"],
            expected_output=item.get("expected_output"),
            metadata={
                "dataset": dataset,
                "component": component,
                **item.get("metadata", {}),
            },
        )

    print(f"  Created dataset: {config.name} ({len(items)} items)")


def migrate_all(dataset: str = "gambling_XS", component: str | None = None) -> None:
    """Migrate all eval components for a dataset.

    Args:
        dataset: Dataset identifier (e.g., "gambling_XS")
        component: Optional specific component to migrate (None = all)
    """
    client = get_langfuse_client()

    components = ["generation", "mapping", "condensation", "refinement"]

    if component:
        if component not in components:
            raise ValueError(
                f"Unknown component: {component}. Valid components: {components}"
            )
        migrate_component(client, dataset, component)
    else:
        for c in components:
            try:
                migrate_component(client, dataset, c)
            except Exception as e:
                print(f"  Error migrating {c}: {e}")

    # Flush to ensure all data is sent
    client.flush()
    print("\nMigration complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate eval data to Langfuse datasets"
    )
    parser.add_argument(
        "--dataset",
        default="gambling_XS",
        help="Dataset identifier (e.g., gambling_XS)",
    )
    parser.add_argument(
        "--component", default=None, help="Specific component to migrate (optional)"
    )
    args = parser.parse_args()

    migrate_all(dataset=args.dataset, component=args.component)
