"""Copy find-themes outputs from S3 into a new run directory, auto-incrementing the run number.

S3 path structure:
  s3://i-dot-ai-preprod-consult-data/app_data/consultations/<name>/outputs/sign_off/<date>/
"""

import subprocess
import sys
from datetime import date
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

    parser = argparse.ArgumentParser(
        description="Copy find-themes outputs from S3 into a new run directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python pull_s3_outputs.py my_consultation ./data/my_gt --date 2026-06-22",
    )
    parser.add_argument("consultation_name", help="Consultation directory name on S3 (e.g. dwp_7_ratio_1_4_campaign_vs_non)")
    parser.add_argument("output_dir", help="Local base directory to write run_N subdirectory into")
    parser.add_argument("--date", default=date.today().isoformat(), help="Date of the find-themes run on S3 (YYYY-MM-DD, default: today)")
    args = parser.parse_args()

    s3_source = f"{S3_ROOT}{args.consultation_name}/outputs/sign_off/{args.date}/"
    local_base = Path(args.output_dir)
    run_dir = next_run_dir(local_base)
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Copying {s3_source} → {run_dir}")
    result = subprocess.run(
        ["aws", "s3", "cp", s3_source, str(run_dir), "--recursive"],
        check=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
