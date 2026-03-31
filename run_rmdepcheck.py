#!/usr/bin/python3
# /// script
# dependencies = [
#   "fedora-distro-aliases",
# ]
# ///

import argparse
import logging
import os
import subprocess
from pathlib import Path

from fedora_distro_aliases import (
    filter_distro,
    Distro,
    bodhi_active_releases,
    get_distro_aliases,
)

aliases = get_distro_aliases()
# Workaround the fact that eln is not in the aliases right now
# https://github.com/rpm-software-management/fedora-distro-aliases/issues/30
eln_distro = [
    Distro.from_bodhi_release(release)
    for release in bodhi_active_releases()
    if release["branch"] == "eln"
]
aliases["eln"] = eln_distro

logging.basicConfig(level="INFO")
logger = logging.getLogger(Path(__file__).name)

# TODO: Move this into Fedora-CI tmt profile
KOJI_BASE = r"https://kojipkgs.fedoraproject.org/repos/{distro_build}/latest/{arch}"

def get_distro_build(dist_git_branch: str) -> str:
    distro_info = filter_distro(aliases, branch=dist_git_branch)
    if not distro_info:
        logger.error(f"Could not identify distro for branch '{dist_git_branch}'")
        exit(1)
    # Seems we have many special cases for each branch :/
    match distro_info.product:
        case "fedora":
            if distro_info.branch == "eln":
                return "eln-build"
            else:
                return f"f{distro_info.version_number}-build"
        case "epel":
            # Note this does not account for epel9-next
            return f"epel{distro_info.version_number}-build"
        case _:
            logger.error(f"Unrecognized distro.product '{distro_info.product}' of '{dist_git_branch}'")
            exit(1)


def main(args: argparse.Namespace) -> None:
    repo_path: Path = args.workdir / "repo"
    subprocess.run(
        [
            "rmdepcheck.py",
            KOJI_BASE.format(
                distro_build=get_distro_build(args.dist_git_branch),
                arch=args.arch,
            ),
            f"file://{repo_path}",
        ],
        check=True,
    )
    logger.info("All is good!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Actually run rmdepcheck")
    parser.add_argument("dist_git_branch")
    parser.add_argument("--arch", default="x86_64")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=os.environ.get("TMT_PLAN_DATA", "."),
    )

    args = parser.parse_args()

    try:
        main(args)
    except (subprocess.CalledProcessError, SystemExit):
        logger.error("Rmdepcheck failed!")
        raise SystemExit(1)
    except Exception as exc:
        logger.error("Unexpected rmdepcheck failure", exc_info=exc)
        raise SystemExit(2)
