#!/usr/bin/env python3
"""
BDD Framework - Test Runner
============================

Runs BDD tests using the configuration defined in framework.yml.
All services (backend, frontend, etc.) must be started before
calling this framework — see ci_example.yml for reference.

Usage:
    python bdd_framework.py --config framework.yml
    python bdd_framework.py --config framework.yml --tags @smoke
    python bdd_framework.py --help
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class BDDFramework:
    """Main class to manage the BDD framework"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
        self.root_path = Path(self.config_path).resolve().parent

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
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
        """Validate minimal config structure"""
        if "tests" not in self.config:
            self._log("ERROR", "Section 'tests' not found in config")
            sys.exit(1)

    def _log(self, level: str, message: str):
        """Simple color logger"""
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
        """
        Validate that the configured BDD structure exists

        Args:
            bdd_config: BDD config with paths for features, steps, and environment
        """
        features_path = bdd_config.get("features")
        steps_path = bdd_config.get("steps")
        environment_path = bdd_config.get("environment")

        if features_path:
            full_features_path = self.root_path / features_path
            if not full_features_path.exists():
                self._log("WARNING", f"Features directory not found: {features_path}")
            else:
                self._log("INFO", f"✅ Features found at: {features_path}")

        if steps_path:
            full_steps_path = self.root_path / steps_path
            if not full_steps_path.exists():
                self._log("WARNING", f"Steps directory not found: {steps_path}")
            else:
                self._log("INFO", f"✅ Steps found at: {steps_path}")

        if environment_path:
            full_env_path = self.root_path / environment_path
            if not full_env_path.exists():
                self._log("WARNING", f"environment.py file not found: {environment_path}")
            else:
                self._log("INFO", f"✅ Environment found at: {environment_path}")

    def _ensure_reports_directory(self, command: str, extra_args: Optional[List[str]] = None):
        """
        Create reports directory if it does not exist

        Args:
            command: Test command that may contain --junit-directory
            extra_args: Additional arguments
        """
        # Find the reports directory path in the command
        cmd_parts = command.split()
        if extra_args:
            cmd_parts.extend(extra_args)

        for i, part in enumerate(cmd_parts):
            if part == "--junit-directory" and i + 1 < len(cmd_parts):
                reports_dir = self.root_path / cmd_parts[i + 1]
                reports_dir.mkdir(parents=True, exist_ok=True)
                self._log("INFO", f"📁 Reports directory created: {cmd_parts[i + 1]}")
                break
            elif part.startswith("--junit-directory="):
                dir_path = part.split("=", 1)[1]
                reports_dir = self.root_path / dir_path
                reports_dir.mkdir(parents=True, exist_ok=True)
                self._log("INFO", f"📁 Reports directory created: {dir_path}")
                break

    def _inject_workspace_path(self):
        """
        Injects the project's root path into the Python environment
        by creating a .pth file in the site-packages directory.
        This allows tests to import modules from the root path without
        messing with PYTHONPATH.
        """
        try:
            import site

            # Use getsitepackages() if available, otherwise fallback to user site packages
            if hasattr(site, "getsitepackages"):
                site_packages = site.getsitepackages()
            else:
                site_packages = [site.getusersitepackages()]

            if not site_packages:
                self._log("WARNING", "No site-packages directories found to inject workspace path")
                return

            # Generally the first one is the active venv's site-packages
            target_site = site_packages[0]
            pth_file = Path(target_site) / "bdd_framework_workspace.pth"

            # Ensure the directory exists
            Path(target_site).mkdir(parents=True, exist_ok=True)

            with open(pth_file, "w", encoding="utf-8") as f:
                f.write(str(self.root_path) + "\n")

            self._log("DEBUG", f"Workspace path injected via {pth_file}")
        except Exception as e:
            self._log("WARNING", f"Failed to inject workspace path via .pth file: {e}")

    def _run_tests(self, extra_args: Optional[List[str]] = None) -> int:
        """
        Run BDD tests

        Args:
            extra_args: Additional arguments for the tests

        Returns:
            Exit code from the tests
        """
        tests_config = self.config.get("tests", {})

        if not tests_config.get("enabled", True):
            self._log("INFO", "Tests disabled in config")
            return 0

        # Validate BDD structure if configured
        bdd_config = tests_config.get("bdd", {})
        if bdd_config:
            self._validate_bdd_structure(bdd_config)

        # Inject workspace path into the Python environment seamlessly
        self._inject_workspace_path()

        self._log("INFO", "🧪 Running BDD tests...")

        tests_path = self.root_path / tests_config["path"]
        command = tests_config["command"]

        # Create reports directory if required by the command
        if "--junit-directory" in command or (
            extra_args and any("--junit-directory" in arg for arg in extra_args)
        ):
            self._ensure_reports_directory(command, extra_args)

        # Parse the full command
        cmd_parts = command.split()

        # Resolve the interpreter/entrypoint to the framework's virtual environment
        # so that python, python3 and behave are always found regardless of PATH.
        if cmd_parts[0].lower() in ["python", "python3", "python.exe"]:
            cmd_parts[0] = sys.executable
        elif cmd_parts[0].lower() == "behave":
            cmd_parts = [sys.executable, "-m", "behave"] + cmd_parts[1:]

        # Make relative paths in the command absolute
        # Behave runs from tests/, but reports should go to root/reports
        for i, part in enumerate(cmd_parts):
            if part == "--junit-directory" and i + 1 < len(cmd_parts):
                reports_path = self.root_path / cmd_parts[i + 1]
                cmd_parts[i + 1] = str(reports_path)
            elif part.startswith("--junit-directory="):
                dir_path = part.split("=", 1)[1]
                reports_path = self.root_path / dir_path
                cmd_parts[i] = f"--junit-directory={reports_path}"

        # Detect if extra_args contains a specific feature file (parallel mode)
        has_specific_feature = bool(extra_args) and any(
            not arg.startswith("-") and arg.endswith(".feature") for arg in extra_args
        )

        if has_specific_feature:
            # PARALLEL MODE: a specific feature file has been injected via --feature-file.
            interpreter_tokens = {sys.executable, "-m", "behave", "python", "python3", "python.exe"}
            # Behave flags that are simple toggles and do not consume a following value.
            no_value_flags = {
                "--junit",
                "--no-capture",
                "--capture",
                "--no-color",
                "--color",
                "--dry-run",
                "--stop",
                "--summary",
                "--no-summary",
                "--verbose",
                "--quiet",
                "-v",
                "-q",
            }
            flags_and_interpreter = []
            i = 0
            while i < len(cmd_parts):
                part = cmd_parts[i]
                if part in interpreter_tokens:
                    flags_and_interpreter.append(part)
                    i += 1
                elif part.startswith("-"):
                    flags_and_interpreter.append(part)
                    # Preserve flag values when present (e.g. --junit-directory reports/junit).
                    if (
                        part not in no_value_flags
                        and i + 1 < len(cmd_parts)
                        and not cmd_parts[i + 1].startswith("-")
                    ):
                        flags_and_interpreter.append(cmd_parts[i + 1])
                        i += 1
                    i += 1
                else:
                    # Token posicional sin flag — es el directorio de features, lo saltamos
                    i += 1

            feature_files = [
                arg for arg in extra_args if not arg.startswith("-") and arg.endswith(".feature")
            ]
            other_extra = [arg for arg in extra_args if arg.startswith("-")]
            cmd_parts = flags_and_interpreter + feature_files + other_extra
            self._log("INFO", f"⚡ Parallel mode: running single feature → {feature_files[0]}")

        else:
            # SEQUENTIAL MODE: no specific feature file, run the full command as-is.
            if extra_args:
                cmd_parts.extend(extra_args)

        test_env = tests_config.get("env") or {}
        env = {**test_env, **os.environ}

        self._log("DEBUG", f"Command: {' '.join(cmd_parts)}")
        self._log("DEBUG", f"CWD: {tests_path}")

        try:
            result = subprocess.run(cmd_parts, cwd=str(tests_path), env=env)

            if result.returncode == 0:
                self._log("INFO", "✅ Tests executed successfully")
            else:
                self._log("ERROR", f"❌ Tests failed with code {result.returncode}")

            return result.returncode

        except Exception as e:
            self._log("ERROR", f"Error running tests: {e}")
            return 1

    def run(self, extra_test_args: Optional[List[str]] = None) -> int:
        """
        Run the framework

        Args:
            extra_test_args: Additional arguments for the tests

        Returns:
            Exit code (0 = success, 1 = error)
        """
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}BDD Framework - Running Tests{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")

        try:
            test_result = self._run_tests(extra_test_args)

            print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
            if test_result == 0:
                print(f"{Colors.BOLD}{Colors.GREEN}✅ Framework executed successfully{Colors.ENDC}")
            else:
                print(f"{Colors.BOLD}{Colors.FAIL}❌ Framework executed with errors{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.ENDC}\n")

            return test_result

        except Exception as e:
            self._log("ERROR", f"Unexpected error: {e}")
            return 1


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="BDD Framework - Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""",
Usage examples:
  python bdd_framework.py --config framework.yml
  python bdd_framework.py --config framework.yml --tags @smoke
  python bdd_framework.py --config framework.yml --tags @critical --no-capture
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
        help="Specific feature file to execute (overrides feature directory execution)",
    )

    args, unknown = parser.parse_known_args()

    # Build extra arguments for the tests
    extra_args = []
    if args.tags:
        extra_args.append(f"--tags={args.tags}")
    if args.no_capture:
        extra_args.append("--no-capture")
    if args.format:
        extra_args.append(f"--format={args.format}")
    if args.feature_file:
        feature_path = Path(args.feature_file).resolve()
        extra_args.append(str(feature_path))

    # Add unknown arguments (for flexibility)
    extra_args.extend(unknown)

    # Run framework
    framework = BDDFramework(args.config)
    exit_code = framework.run(extra_args if extra_args else None)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
