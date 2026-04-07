#!/usr/bin/env python3
"""
Script to discover BDD feature files based on a YAML configuration.

This script parses a framework configuration file, locates the features directory,
handles exclusion rules, and outputs a JSON array of discovered feature files.
It is primarily used to generate a matrix for GitHub Actions parallel execution.
"""

import json
import sys
from pathlib import Path

import yaml


def discover(config_path="framework.yml"):
    """
    Discover `.feature` files based on the provided configuration file.

    Args:
        config_path (str): The path to the YAML configuration file. Defaults to "framework.yml".

    Outputs:
        Prints a JSON formatted list of discovered feature file paths to standard output.
        Prints error or warning messages to standard error.

    Raises:
        SystemExit: Exits with code 1 if the configuration file is missing, invalid,
                    or if the features directory cannot be found.
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

    try:
        features_dir = config["tests"]["bdd"]["features"]
    except KeyError:
        print("Error: Could not find tests.bdd.features in config", file=sys.stderr)
        sys.exit(1)

    features_path = Path(features_dir)
    if not features_path.exists() or not features_path.is_dir():
        print(
            f"Error: Features directory '{features_dir}' not found or is not a directory.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Read optional exclude list from framework configuration file.
    exclude_raw = config.get("tests", {}).get("bdd", {}).get("exclude") or []
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

    # Find all .feature files and sort them for deterministic order across runs
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

    # Output as JSON array for GitHub Actions matrix
    print(json.dumps(feature_files))


if __name__ == "__main__":
    config_arg = "framework.yml"
    if len(sys.argv) > 1:
        config_arg = sys.argv[1]
    discover(config_arg)
