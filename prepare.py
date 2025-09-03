#!/usr/bin/python3
# /// script
# ///

import argparse
import logging
import os
import subprocess
from pathlib import Path

logging.basicConfig(level="INFO")
logger = logging.getLogger(Path(__file__).name)


def main(args: argparse.Namespace) -> None:
    repo_path: Path = args.workdir / "repo"
    repo_path.mkdir(exist_ok=True)

    logger.info(f"""
    Preparing environment for:
    Koji task: {args.koji_task_id}
    Arch: {args.arch}
    """)

    logger.info("Downloading artifacts from Koji")
    subprocess.run(
        [
            "koji",
            "download-task",
            args.koji_task_id,
            "--arch=noarch",
            f"--arch={args.arch}",
        ],
        cwd=repo_path,
    )

    logger.info(f"Creating the repo: {repo_path}")
    subprocess.run(
        [
            "createrepo",
            f"{repo_path}",
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("koji_task_id")
    parser.add_argument("--arch", default="x86_64")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=os.environ.get("TMT_PLAN_DATA", "."),
    )

    args = parser.parse_args()

    main(args)
