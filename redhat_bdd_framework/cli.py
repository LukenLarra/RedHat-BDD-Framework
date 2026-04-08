"""CLI implementation for the RedHat BDD Framework."""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class Colors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
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

    def _ensure_reports_directory(self, command: str, extra_args: Optional[List[str]] = None):
        """Create reports directory if it does not exist."""
        cmd_parts = command.split()
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

        cmd_parts = command.split()

        if cmd_parts[0].lower() in ["python", "python3", "python.exe"]:
            cmd_parts[0] = sys.executable
        elif cmd_parts[0].lower() == "behave":
            cmd_parts = [sys.executable, "-m", "behave"] + cmd_parts[1:]

        for i, part in enumerate(cmd_parts):
            if part == "--junit-directory" and i + 1 < len(cmd_parts):
                reports_path = self.root_path / cmd_parts[i + 1]
                cmd_parts[i + 1] = str(reports_path)
            elif part.startswith("--junit-directory="):
                dir_path = part.split("=", 1)[1]
                reports_path = self.root_path / dir_path
                cmd_parts[i] = f"--junit-directory={reports_path}"

        if extra_args:
            for i, arg in enumerate(extra_args):
                if not arg.startswith("-") and ".feature" in arg:
                    parts = arg.split(":", 1)
                    feat_path = Path(parts[0])
                    if not feat_path.is_absolute():
                        feat_path = self.root_path / feat_path
                    if feat_path.exists():
                        parts[0] = str(feat_path.absolute())
                        extra_args[i] = ":".join(parts)
            cmd_parts.extend(extra_args)

        custom_env_str = {str(k): str(v) for k, v in (tests_config.get("env", {}) or {}).items()}
        env = {**os.environ, **custom_env_str}

        try:
            result = subprocess.run(cmd_parts, cwd=str(tests_path), env=env)

            if result.returncode == 0:
                self._log("INFO", "Tests executed successfully")
            else:
                self._log("ERROR", f"Tests failed with code {result.returncode}")

            return result.returncode

        except Exception as e:
            self._log("ERROR", f"Error running tests: {e}")
            return 1

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
  python bdd_framework.py --config framework.yml
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
    if getattr(args, "feature-file", None):
        extra_args.append(f"--feature-file={args.feature_file}")
    extra_args.extend(unknown)

    framework = BDDFramework(args.config)
    return framework.run(extra_args if extra_args else None)


def main() -> None:
    """Process entrypoint."""
    raise SystemExit(run_cli())
