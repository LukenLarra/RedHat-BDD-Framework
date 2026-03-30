#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import yaml


def discover(config_path="framework.yml"):
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

    # Find all .feature files and sort them for deterministic order across runs
    feature_files = sorted(str(p.as_posix()) for p in features_path.rglob("*.feature"))

    if not feature_files:
        print(f"Warning: No .feature files found in '{features_dir}'.", file=sys.stderr)

    # Output as JSON array for GitHub Actions matrix
    print(json.dumps(feature_files))


if __name__ == "__main__":
    config_arg = "framework.yml"
    if len(sys.argv) > 1:
        config_arg = sys.argv[1]
    discover(config_arg)
