"""Copy outputs from S3 into a new run directory, auto-incrementing the run number."""

import subprocess
import sys
from pathlib import Path

S3_ROOT = "s3://i-dot-ai-preprod-consult-data/app_data/consultations/"


def next_run_dir(base: Path) -> Path:
    existing = [d for d in base.glob("run_*") if d.is_dir()]
    nums = []
    for d in existing:
        try:
            nums.append(int(d.name.split("_")[1]))
        except (IndexError, ValueError):
            pass
    next_num = max(nums, default=0) + 1
    return base / f"run_{next_num}"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Copy consultation outputs from S3 into a new run directory.")
    parser.add_argument("consultation_name", help="Consultation directory name (e.g. dwp_7_ratio_1_4_campaign_vs_non)")
    parser.add_argument("output_dir", help="Local base directory to store outputs (default: <consultation_name>/outputs)")
    args = parser.parse_args()

    name = args.consultation_name
    s3_source = f"{S3_ROOT}{name}/outputs/"
    local_base = Path(args.output_dir) if args.output_dir else Path(name) / "outputs"
    run_dir = next_run_dir(local_base)
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Copying {s3_source} -> {run_dir}")
    result = subprocess.run(
        ["aws", "s3", "cp", s3_source, str(run_dir), "--recursive"],
        check=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
