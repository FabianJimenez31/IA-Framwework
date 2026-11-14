#!/usr/bin/env python3
"""Decide which CI and deploy lanes a set of changed files activates.

The pipeline validates and deploys only what a change touches: a frontend-only
pull request does not run the backend suite or restart the backend, and a
docs-only one deploys nothing. Lanes are declared in ``lanes.json`` next to this
script, so a project adapts the rules without editing code.

Two safety defaults: a path nobody classified falls into the default lane, and
when the diff cannot be computed every lane runs.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence

CONFIG_PATH = Path(__file__).with_name("lanes.json")
ZERO_SHA = "0" * 40
DEPLOY_EVERYTHING = "--all"


@dataclass(frozen=True)
class Lane:
    name: str
    paths: tuple[str, ...]
    deploy: tuple[str, ...]
    default: bool = False


@dataclass(frozen=True)
class LaneConfig:
    lanes: tuple[Lane, ...]
    neutral_prefixes: tuple[str, ...]
    neutral_files: frozenset[str]
    neutral_root_extensions: tuple[str, ...]
    test_only_prefixes: tuple[str, ...]
    pipeline_paths: frozenset[str]

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(lane.name for lane in self.lanes)

    @property
    def default_lane(self) -> str | None:
        return next((lane.name for lane in self.lanes if lane.default), None)


def load_config(path: Path = CONFIG_PATH) -> LaneConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    lanes = tuple(
        Lane(
            name=item["name"],
            paths=tuple(item.get("paths", ())),
            deploy=tuple(item.get("deploy", ())),
            default=bool(item.get("default", False)),
        )
        for item in raw["lanes"]
    )
    if sum(lane.default for lane in lanes) > 1:
        raise ValueError("lanes.json: at most one lane may be marked as default")
    return LaneConfig(
        lanes=lanes,
        neutral_prefixes=tuple(raw.get("neutral_prefixes", ())),
        neutral_files=frozenset(raw.get("neutral_files", ())),
        neutral_root_extensions=tuple(raw.get("neutral_root_extensions", ())),
        test_only_prefixes=tuple(raw.get("test_only_prefixes", ())),
        pipeline_paths=frozenset(raw.get("pipeline_paths", ())),
    )


def _normalize(paths: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                PurePosixPath(path.strip().replace("\\", "/")).as_posix()
                for path in paths
                if path.strip()
            }
        )
    )


def _is_neutral(path: str, config: LaneConfig) -> bool:
    if path in config.neutral_files or path.startswith(config.neutral_prefixes):
        return True
    return "/" not in path and path.lower().endswith(config.neutral_root_extensions)


def lane_for(path: str, config: LaneConfig) -> str | None:
    """Lane of a single file, or ``None`` when it activates nothing."""
    for lane in config.lanes:
        if lane.paths and path.startswith(lane.paths):
            return lane.name
    if path in config.pipeline_paths or _is_neutral(path, config):
        return None
    return config.default_lane


def _lanes_of(paths: Iterable[str], config: LaneConfig) -> tuple[str, ...]:
    found = {lane_for(path, config) for path in paths}
    return tuple(name for name in config.names if name in found)


def ci_lanes(paths: Iterable[str], config: LaneConfig) -> tuple[str, ...]:
    """Lanes to validate. A change to the pipeline itself runs all of them."""
    changed = _normalize(paths)
    if any(path in config.pipeline_paths for path in changed):
        return config.names
    return _lanes_of(changed, config)


def deploy_lanes(paths: Iterable[str], config: LaneConfig) -> tuple[str, ...]:
    """Lanes to deploy. Tests are validated in CI but never reach production."""
    shipped = [
        path for path in _normalize(paths) if not path.startswith(config.test_only_prefixes)
    ]
    return _lanes_of(shipped, config)


def deploy_flags(lanes: Sequence[str], config: LaneConfig) -> str:
    return " ".join(flag for lane in config.lanes if lane.name in lanes for flag in lane.deploy)


def changed_files(base: str, head: str) -> tuple[str, ...] | None:
    """Files between two refs, or ``None`` when the diff cannot be computed."""
    if not base or base == ZERO_SHA:
        return None
    result = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return _normalize(result.stdout.splitlines())


def _emit(pairs: dict[str, str]) -> None:
    lines = [f"{key}={value}" for key, value in pairs.items()]
    print("\n".join(lines))
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="base ref of the diff")
    parser.add_argument("--head", default="HEAD", help="final ref of the diff (default: HEAD)")
    parser.add_argument(
        "--mode",
        choices=("ci", "deploy"),
        default="ci",
        help="ci: lanes to validate; deploy: flags for the deploy script",
    )
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="path to lanes.json")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    files = changed_files(args.base, args.head)
    if files is None:
        print("ci-lanes: the diff could not be computed; every lane is activated.", file=sys.stderr)
        lanes = config.names
    elif args.mode == "ci":
        lanes = ci_lanes(files, config)
    else:
        lanes = deploy_lanes(files, config)

    pairs = {name: str(name in lanes).lower() for name in config.names}
    pairs["any"] = str(bool(lanes)).lower()
    if args.mode == "deploy":
        # Without a trustworthy diff, deploy everything rather than guess.
        pairs["flags"] = DEPLOY_EVERYTHING if files is None else deploy_flags(lanes, config)
    _emit(pairs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
