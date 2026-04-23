"""CLI implementation for the RedHat BDD Framework."""

import argparse
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from redhat_bdd_framework.behave_utils import (
    BEHAVE_FLAGS_WITH_VALUES,
    is_feature_target,
    iterate_tokens,
    resolve_path,
)


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class BDDFramework:
    """Main class to manage the BDD framework."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
        self.root_path = Path(self.config_path).absolute().parent

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            self._log("INFO", f"Configuration loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            self._log("ERROR", f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            self._log("ERROR", f"YAML parsing error: {e}")
            sys.exit(1)

    def _validate_config(self):
        """Validate minimal config structure."""
        if "tests" not in self.config:
            self._log("ERROR", "Section 'tests' not found in config")
            sys.exit(1)

    def _log(self, level: str, message: str):
        """Simple color logger."""
        colors = {
            "DEBUG": Colors.CYAN,
            "INFO": Colors.GREEN,
            "WARNING": Colors.WARNING,
            "ERROR": Colors.FAIL,
        }
        color = colors.get(level, Colors.ENDC)
        timestamp = time.strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] [{level}]{Colors.ENDC} {message}")

    def _validate_bdd_structure(self, bdd_config: Dict):
        """Validate that the configured BDD structure exists."""
        features_path = bdd_config.get("features")
        steps_path = bdd_config.get("steps")
        environment_path = bdd_config.get("environment")

        if features_path:
            full_features_path = self.root_path / features_path
            if not full_features_path.exists():
                self._log("WARNING", f"Features directory not found: {features_path}")
            else:
                self._log("INFO", f"Features found at: {features_path}")

        if steps_path:
            full_steps_path = self.root_path / steps_path
            if not full_steps_path.exists():
                self._log("WARNING", f"Steps directory not found: {steps_path}")
            else:
                self._log("INFO", f"Steps found at: {steps_path}")

        if environment_path:
            full_env_path = self.root_path / environment_path
            if not full_env_path.exists():
                self._log("WARNING", f"environment.py file not found: {environment_path}")
            else:
                self._log("INFO", f"Environment found at: {environment_path}")

    def _normalize_at_file_targets(
        self, parts: List[str], tests_path: Path, behave_cwd: Path
    ) -> List[str]:
        """Convert behave @file targets to absolute paths so cwd changes do not break them."""
        normalized: List[str] = []
        base_candidates = [self.root_path, tests_path, behave_cwd]

        for token, is_flag_value in iterate_tokens(parts, BEHAVE_FLAGS_WITH_VALUES):
            if is_flag_value or not token.startswith("@") or len(token) <= 1:
                normalized.append(token)
                continue
            resolved = resolve_path(Path(token[1:]), base_candidates)
            normalized.append(f"@{resolved}" if resolved else token)

        return normalized

    def _ensure_reports_directory(self, command: str, extra_args: Optional[List[str]] = None):
        """Create reports directory if it does not exist."""
        cmd_parts = shlex.split(command)
        if extra_args:
            cmd_parts.extend(extra_args)

        for i, part in enumerate(cmd_parts):
            if part == "--junit-directory" and i + 1 < len(cmd_parts):
                reports_dir = self.root_path / cmd_parts[i + 1]
                reports_dir.mkdir(parents=True, exist_ok=True)
                self._log("INFO", f"Reports directory created: {cmd_parts[i + 1]}")
                break
            if part.startswith("--junit-directory="):
                dir_path = part.split("=", 1)[1]
                reports_dir = self.root_path / dir_path
                reports_dir.mkdir(parents=True, exist_ok=True)
                self._log("INFO", f"Reports directory created: {dir_path}")
                break

    def _get_behave_working_dir(self, tests_path: Path, bdd_config: Dict[str, Any]) -> Path:
        """Return the feature root directory for behave path resolution."""
        steps_path = bdd_config.get("steps") if bdd_config else None
        if steps_path:
            candidate = self.root_path / Path(steps_path).parent
            if candidate.exists():
                return candidate
        return tests_path

    def _expand_at_file_targets(
        self, parts: List[str], tests_path: Path, behave_root: Path
    ) -> Tuple[List[str], List[str]]:
        """Expand behave @file.txt targets into explicit feature paths.

        This allows us to run behave from a stable cwd while still selecting
        scenario files listed in @file targets.
        """
        expanded: List[str] = []
        extracted_features: List[str] = []
        base_candidates = [self.root_path, tests_path, behave_root]

        for token, is_flag_value in iterate_tokens(parts, BEHAVE_FLAGS_WITH_VALUES):
            if is_flag_value or not token.startswith("@") or len(token) <= 1:
                expanded.append(token)
                continue
            resolved = resolve_path(Path(token[1:]), base_candidates)
            if resolved and resolved.exists() and resolved.suffix == ".txt":
                try:
                    with open(resolved, encoding="utf-8") as f:
                        for line in f:
                            entry = line.strip()
                            if entry and not entry.startswith("#"):
                                extracted_features.append(entry)
                    continue
                except OSError:
                    pass
            expanded.append(token)

        return expanded, extracted_features

    def _ensure_behave_search_root(self, parts: List[str], behave_root: Path) -> List[str]:
        """Ensure behave receives an explicit search root directory."""
        behave_index = next((i for i, t in enumerate(parts) if t == "behave"), None)
        inspect_parts = parts[behave_index + 1 :] if behave_index is not None else parts

        has_path_target = any(
            not is_flag_value
            and not token.startswith("-")
            and not token.startswith("@")
            and not is_feature_target(token)
            for token, is_flag_value in iterate_tokens(inspect_parts, BEHAVE_FLAGS_WITH_VALUES)
        )

        return parts if has_path_target else parts + [str(behave_root)]

    def _collect_explicit_feature_targets(
        self, cmd_parts: List[str], extra_args: Optional[List[str]]
    ) -> List[str]:
        """Return explicit .feature targets from the behave command and extra args."""
        parts = cmd_parts[:] + (extra_args or [])
        behave_index = next((i for i, t in enumerate(parts) if t == "behave"), None)
        if behave_index is not None:
            parts = parts[behave_index + 1 :]

        return [
            token
            for token, is_flag_value in iterate_tokens(parts, BEHAVE_FLAGS_WITH_VALUES)
            if not is_flag_value
            and not token.startswith("-")
            and not token.startswith("@")
            and is_feature_target(token)
        ]

    def _clean_feature_targets(self, parts: List[str]) -> List[str]:
        """Remove explicit feature path tokens from a parsed command segment."""
        return [
            token
            for token, is_flag_value in iterate_tokens(parts, BEHAVE_FLAGS_WITH_VALUES)
            if is_flag_value or not is_feature_target(token)
        ]

    def _build_include_args(
        self, feature_targets: List[str], tests_path: Path, cwd: Path
    ) -> List[str]:
        """Convert explicit feature paths into behave --include filter arguments."""
        include_args = []
        cwd_resolved = cwd.resolve(strict=False)

        for feature in feature_targets:
            feature_path = Path(feature)
            if not feature_path.is_absolute():
                feature_path = (tests_path / feature_path).resolve(strict=False)
            else:
                feature_path = feature_path.resolve(strict=False)

            try:
                relative = feature_path.relative_to(cwd_resolved)
                pattern = re.escape(relative.as_posix())
            except ValueError:
                pattern = re.escape(feature_path.name)

            include_args.append(f"--include={pattern}")

        return include_args

    def _prepare_behave_command(
        self,
        command: str,
        tests_path: Path,
        behave_cwd: Path,
        extra_args: Optional[List[str]],
    ) -> Tuple[List[str], Optional[List[str]]]:
        """Parse command, fix interpreter, normalize and expand @file targets."""
        cmd_parts = shlex.split(command)

        if cmd_parts[0].lower() in ["python", "python3", "python.exe"]:
            cmd_parts[0] = sys.executable
        elif cmd_parts[0].lower() == "behave":
            cmd_parts = [sys.executable, "-m", "behave"] + cmd_parts[1:]

        cmd_parts = self._normalize_at_file_targets(cmd_parts, tests_path, behave_cwd)
        if extra_args:
            extra_args = self._normalize_at_file_targets(extra_args, tests_path, behave_cwd)

        cmd_parts, at_file_features = self._expand_at_file_targets(
            cmd_parts, tests_path, behave_cwd
        )
        if extra_args:
            extra_args, extra_at_file_features = self._expand_at_file_targets(
                extra_args, tests_path, behave_cwd
            )
            at_file_features.extend(extra_at_file_features)

        if at_file_features:
            extra_args = list(extra_args or []) + at_file_features

        return cmd_parts, extra_args

    def _apply_feature_filters(
        self,
        cmd_parts: List[str],
        extra_args: Optional[List[str]],
        tests_path: Path,
        behave_cwd: Path,
    ) -> List[str]:
        """Convert explicit .feature targets into --include filters; absorb junit-directory paths."""
        cmd_parts = self._ensure_behave_search_root(cmd_parts, behave_cwd)

        explicit_features = self._collect_explicit_feature_targets(cmd_parts, extra_args)
        if explicit_features:
            cmd_parts = self._clean_feature_targets(cmd_parts)
            if extra_args:
                extra_args = self._clean_feature_targets(extra_args)
            cmd_parts.extend(self._build_include_args(explicit_features, tests_path, behave_cwd))

        for i, part in enumerate(cmd_parts):
            if part == "--junit-directory" and i + 1 < len(cmd_parts):
                cmd_parts[i + 1] = str(self.root_path / cmd_parts[i + 1])
            elif part.startswith("--junit-directory="):
                dir_path = part.split("=", 1)[1]
                cmd_parts[i] = f"--junit-directory={self.root_path / dir_path}"

        if extra_args:
            cmd_parts.extend(extra_args)

        return cmd_parts

    def _execute_behave(self, cmd_parts: List[str], tests_path: Path, env: Dict) -> int:
        """Run the behave subprocess and return its exit code."""
        try:
            self._log("DEBUG", f"Final command: {' '.join(cmd_parts)}")
            self._log("DEBUG", f"CWD: {tests_path}")
            result = subprocess.run(cmd_parts, cwd=str(tests_path), env=env)
            if result.returncode == 0:
                self._log("INFO", "Tests executed successfully")
            else:
                self._log("ERROR", f"Tests failed with code {result.returncode}")
            return result.returncode
        except Exception as e:
            self._log("ERROR", f"Error running tests: {e}")
            return 1

    def _run_tests(self, extra_args: Optional[List[str]] = None) -> int:
        """Run BDD tests."""
        tests_config = self.config.get("tests", {})

        if not tests_config.get("enabled", True):
            self._log("INFO", "Tests disabled in config")
            return 0

        bdd_config = tests_config.get("bdd", {})
        if bdd_config:
            self._validate_bdd_structure(bdd_config)

        self._log("INFO", "Running BDD tests...")

        tests_path = self.root_path / tests_config["path"]
        command = tests_config["command"]

        if "--junit-directory" in command or (
            extra_args and any("--junit-directory" in arg for arg in extra_args)
        ):
            self._ensure_reports_directory(command, extra_args)

        behave_cwd = self._get_behave_working_dir(tests_path, bdd_config)
        cmd_parts, extra_args = self._prepare_behave_command(
            command, tests_path, behave_cwd, extra_args
        )
        cmd_parts = self._apply_feature_filters(cmd_parts, extra_args, tests_path, behave_cwd)

        custom_env_str = {str(k): str(v) for k, v in (tests_config.get("env", {}) or {}).items()}
        env = {**os.environ, **custom_env_str}

        return self._execute_behave(cmd_parts, tests_path, env)

    def run(self, extra_test_args: Optional[List[str]] = None) -> int:
        """Run the framework."""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}BDD Framework - Running Tests{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")

        try:
            test_result = self._run_tests(extra_test_args)

            print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
            if test_result == 0:
                print(f"{Colors.BOLD}{Colors.GREEN}Framework executed successfully{Colors.ENDC}")
            else:
                print(f"{Colors.BOLD}{Colors.FAIL}Framework executed with errors{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")

            return test_result

        except Exception as e:
            self._log("ERROR", f"Unexpected error: {e}")
            return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BDD Framework - Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python -m redhat_bdd_framework --config framework.yml
  bdd-framework --config framework.yml --tags @smoke
  python -m redhat_bdd_framework --config framework.yml --tags @critical --no-capture
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="framework.yml",
        help="Path to the YAML configuration file (default: framework.yml)",
    )
    parser.add_argument(
        "--tags",
        type=str,
        help="Behave tags to filter tests (e.g.: @smoke, @critical)",
    )
    parser.add_argument(
        "--no-capture", action="store_true", help="Do not capture stdout (pass to Behave)"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["pretty", "plain", "json"],
        help="Behave output format",
    )
    parser.add_argument(
        "--feature-file",
        type=str,
        help="Specific feature file to execute (e.g. path/to/file.feature)",
    )
    return parser


def run_cli(argv: Optional[List[str]] = None) -> int:
    """Run the CLI and return an exit code."""
    parser = _build_parser()
    args, unknown = parser.parse_known_args(argv)

    extra_args: List[str] = []
    if args.tags:
        extra_args.append(f"--tags={args.tags}")
    if args.no_capture:
        extra_args.append("--no-capture")
    if args.format:
        extra_args.append(f"--format={args.format}")
    if args.feature_file:
        extra_args.append(args.feature_file)
    extra_args.extend(unknown)

    framework = BDDFramework(args.config)
    return framework.run(extra_args if extra_args else None)


def main() -> None:
    """Process entrypoint."""
    raise SystemExit(run_cli())
