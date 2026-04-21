#!/usr/bin/env python3
"""
Script to discover BDD feature files based on a YAML configuration.

This script parses a framework configuration file, locates the features directory,
handles exclusion rules, and outputs a JSON array of discovered feature files.
It is primarily used to generate a matrix for GitHub Actions parallel execution.
"""

import json
import shlex
import sys
from pathlib import Path

import yaml

# Behave flags that consume the next token as a value (not a feature path).
_FLAGS_WITH_VALUES = {
    "--tags",
    "-t",
    "--format",
    "-f",
    "--outfile",
    "-o",
    "--junit-directory",
    "--include",
    "-i",
    "--exclude",
    "-e",
    "--stage",
    "--lang",
    "--logging-level",
    "--logging-format",
    "--logging-filter",
    "--logging-filename",
    "--logging-filemode",
    "--logging-datefmt",
}


def _read_txt_feature_list(txt_path: Path, tests_path: Path) -> list:
    """Read feature paths from a behave @file.txt."""
    features = []
    with open(txt_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                features.append(str((tests_path / line).as_posix()))
    return features


def _features_from_command(command: str, tests_path: Path) -> list:
    """
    Extract feature files from a behave command string.

    Returns a list of feature paths if the command explicitly names them
    (via @file.txt or inline .feature args), or an empty list if the command
    contains no explicit feature targets.
    """
    try:
        parts = shlex.split(command)
    except ValueError:
        return []

    # Locate the 'behave' token to skip interpreter prefix (python -m behave / behave).
    behave_idx = None
    for i, p in enumerate(parts):
        if p == "behave":
            behave_idx = i
            break
    if behave_idx is None:
        return []

    txt_files = []
    feature_files = []
    skip_next = False

    for part in parts[behave_idx + 1 :]:
        if skip_next:
            skip_next = False
            continue
        if part in _FLAGS_WITH_VALUES:
            skip_next = True
            continue
        if part.startswith("-"):
            continue
        if part.startswith("@"):
            txt_files.append(part[1:])
        elif ".feature" in part:
            feature_files.append(part)

    if txt_files:
        features = []
        for txt in txt_files:
            txt_path = tests_path / txt
            if not txt_path.exists():
                print(f"Warning: @{txt} not found at {txt_path}", file=sys.stderr)
                continue
            features.extend(_read_txt_feature_list(txt_path, tests_path))
        return features

    if feature_files:
        return [str((tests_path / f).as_posix()) for f in feature_files]

    return []


def discover(config_path="framework.yml"):
    """
    Discover `.feature` files based on the provided configuration file.

    Priority:
    1. Explicit feature targets in tests.command (@file.txt or inline .feature paths)
    2. Fallback: rglob scan of tests.bdd.features directory (respects exclude list)

    Args:
        config_path (str): Path to the YAML configuration file. Defaults to "framework.yml".

    Outputs:
        Prints a JSON formatted list of discovered feature file paths to standard output.
        Prints error or warning messages to standard error.

    Raises:
        SystemExit: Exits with code 1 if the configuration file is missing or invalid.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"Error: {config_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(config_file, encoding="utf-8") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}", file=sys.stderr)
            sys.exit(1)

    tests_config = config.get("tests", {})
    tests_path = config_file.parent / tests_config.get("path", ".")

    # --- Priority 1: derive feature list from command ---
    command = tests_config.get("command", "")
    if command:
        command_features = _features_from_command(command, tests_path)
        if command_features:
            command_features.sort()
            print(json.dumps(command_features))
            return

    # --- Priority 2: fallback — scan bdd.features directory ---
    bdd_config = tests_config.get("bdd", {})
    features_dir = bdd_config.get("features") if bdd_config else None

    if not features_dir:
        print("Error: Could not find tests.bdd.features in config", file=sys.stderr)
        sys.exit(1)

    features_path = Path(features_dir)
    if not features_path.exists() or not features_path.is_dir():
        print(
            f"Error: Features directory '{features_dir}' not found or is not a directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    exclude_raw = bdd_config.get("exclude") or []
    if isinstance(exclude_raw, str):
        exclude_entries = [exclude_raw]
    elif isinstance(exclude_raw, (list, tuple, set)):
        exclude_entries = [str(e) for e in exclude_raw if e]
    else:
        print(
            "Warning: tests.bdd.exclude should be a string or a list. Ignoring invalid value.",
            file=sys.stderr,
        )
        exclude_entries = []

    exclude_names = {Path(e).name for e in exclude_entries}
    exclude_full_paths = {
        str((config_file.parent / Path(e)).resolve().as_posix()) for e in exclude_entries
    }

    feature_files = []
    for p in features_path.rglob("*.feature"):
        if p.name in exclude_names:
            continue
        if str(p.resolve().as_posix()) in exclude_full_paths:
            continue
        feature_files.append(str(p.as_posix()))

    feature_files.sort()

    if not feature_files:
        print(f"Warning: No .feature files found in '{features_dir}'.", file=sys.stderr)

    print(json.dumps(feature_files))


if __name__ == "__main__":
    config_arg = "framework.yml"
    if len(sys.argv) > 1:
        config_arg = sys.argv[1]
    discover(config_arg)
