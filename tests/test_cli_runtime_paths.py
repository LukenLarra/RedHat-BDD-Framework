import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from shepherd_bdd.cli import BDDFramework


class TestBDDCliRuntimePaths(unittest.TestCase):
    def test_at_file_from_repo_root_keeps_tests_cwd_and_generates_include(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            features_root = root / "insights-behavioral-spec" / "features"
            steps_dir = features_root / "steps"
            suite_dir = features_root / "dvo-writer"
            suite_dir.mkdir(parents=True)
            steps_dir.mkdir(parents=True)

            feature_file = suite_dir / "dvo.feature"
            feature_file.write_text("Feature: DVO\n", encoding="utf-8")

            test_list_dir = root / "insights-behavioral-spec" / "test_list"
            test_list_dir.mkdir(parents=True)
            test_list_file = test_list_dir / "dvo_writer.txt"
            test_list_file.write_text(
                "insights-behavioral-spec/features/dvo-writer/dvo.feature\n",
                encoding="utf-8",
            )

            config = {
                "tests": {
                    "enabled": True,
                    "path": ".",
                    "command": (
                        "python -m behave "
                        "@insights-behavioral-spec/test_list/dvo_writer.txt "
                        "--junit --junit-directory reports/junit --format pretty"
                    ),
                    "bdd": {
                        "features": "insights-behavioral-spec/features/dvo-writer",
                        "steps": "insights-behavioral-spec/features/steps",
                        "environment": "insights-behavioral-spec/features/environment.py",
                    },
                }
            }

            config_path = root / "framework.yml"
            config_path.write_text(yaml.dump(config), encoding="utf-8")

            framework = BDDFramework(str(config_path))

            with patch("shepherd_bdd.cli.subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.returncode = 0
                mock_run.return_value = mock_proc

                exit_code = framework.run()

            self.assertEqual(exit_code, 0)
            args = mock_run.call_args[0][0]
            run_cwd = Path(mock_run.call_args[1]["cwd"])

            self.assertEqual(run_cwd, root)
            self.assertIn(str(features_root), args)
            self.assertTrue(
                any(arg.startswith("--include=") and "dvo" in arg for arg in args),
                f"Expected an include filter for dvo feature, got: {args}",
            )
            self.assertFalse(any(arg.startswith("@") for arg in args))

    def test_multiple_features_in_txt_produce_single_include_with_or(self):
        """Multiple features in @file.txt must generate one --include with | not N separate flags.

        behave's --include uses argparse `store` action, so each flag overwrites the
        previous one. Passing N separate --include flags would silently drop all but
        the last feature.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            features_root = root / "features"
            features_root.mkdir(parents=True)
            for name in ("alpha.feature", "beta.feature", "gamma.feature"):
                (features_root / name).write_text(f"Feature: {name}\n", encoding="utf-8")

            test_list_dir = root / "test_list"
            test_list_dir.mkdir()
            txt_file = test_list_dir / "suite.txt"
            txt_file.write_text(
                "features/alpha.feature\nfeatures/beta.feature\nfeatures/gamma.feature\n",
                encoding="utf-8",
            )

            config = {
                "tests": {
                    "enabled": True,
                    "path": ".",
                    "command": "python -m behave @test_list/suite.txt --format pretty",
                    "bdd": {"features": "features"},
                }
            }

            config_path = root / "framework.yml"
            config_path.write_text(yaml.dump(config), encoding="utf-8")

            framework = BDDFramework(str(config_path))

            with patch("shepherd_bdd.cli.subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.returncode = 0
                mock_run.return_value = mock_proc
                framework.run()

            args = mock_run.call_args[0][0]
            include_args = [a for a in args if a.startswith("--include=")]

            self.assertEqual(
                len(include_args), 1, f"Expected exactly one --include, got: {include_args}"
            )
            pattern = include_args[0].split("=", 1)[1]
            self.assertIn("alpha", pattern)
            self.assertIn("beta", pattern)
            self.assertIn("gamma", pattern)
            self.assertIn("|", pattern)


if __name__ == "__main__":
    unittest.main()
