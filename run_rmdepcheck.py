#!/usr/bin/python3
# /// script
# dependencies = [
#   "fedora-distro-aliases",
# ]
# ///

import argparse
import logging
import os
import re
import subprocess
from pathlib import Path


from fedora_distro_aliases import get_distro_aliases

# TODO: There is no clean way to break down the `fedora-rawhide` from the aliases right now, using
#   fedora-all alias instead
# https://github.com/rpm-software-management/fedora-distro-aliases/issues/29
fedora_all = get_distro_aliases()["fedora-all"]

logging.basicConfig(level="INFO")
logger = logging.getLogger(Path(__file__).name)

KOJI_BASE = r"https://kojipkgs.fedoraproject.org/repos/{distro_build}/latest/{arch}"


def get_distro_build(distro_name: str) -> str:
    if fedora_match := re.match(r"fedora-(?P<branch>.+)", distro_name):
        branch = fedora_match.group("branch")
        if branch != "rawhide":
            # For numbered branches (e.g. fedora-42)
            branch = f"f{branch}"
    else:
        # TODO: Deal with epel and eln
        raise NotImplementedError
    distro_info = next(d for d in fedora_all if d.branch == branch)
    return f"f{distro_info.version_number}-build"


def main(args: argparse.Namespace) -> None:
    repo_path: Path = args.workdir / "repo"
    out = subprocess.run(
        [
            "rmdepcheck.py",
            KOJI_BASE.format(
                distro_build=get_distro_build(args.distro),
                arch=args.arch,
            ),
            f"file://{repo_path}",
        ],
        check=False,
    )
    if out.returncode == 0:
        print("All is good!")
    else:
        print("Rmdepcheck failed!")
        raise SystemExit(out.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Actually run rmdepcheck")
    parser.add_argument("distro")
    parser.add_argument("--arch", default="x86_64")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=os.environ.get("TMT_PLAN_DATA", "."),
    )

    args = parser.parse_args()

    main(args)
