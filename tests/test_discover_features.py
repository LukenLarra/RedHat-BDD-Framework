"""Unit tests for the discover_features script.

This module verifies that discover_features.discover() handles missing configuration,
invalid YAML, missing required configuration keys, missing feature directories,
and proper feature discovery including exclusions.
"""

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure the scripts directory is importable from tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from discover_features import discover


class TestDiscoverFeatures(unittest.TestCase):
    """Test cases for the discover_features.discover() helper."""

    def setUp(self):
        """Prepare test fixtures before each test runs."""
        pass

    @patch("discover_features.Path.exists", return_value=False)
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_missing_config_file(self, mock_stderr, mock_exists):
        """When the config file does not exist, the script should exit with code 1.

        This test verifies that discover() detects a missing YAML file and writes
        the expected error message to stderr.
        """
        with self.assertRaises(SystemExit) as cm:
            discover("non_existent.yml")

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("non_existent.yml not found", mock_stderr.getvalue())

    @patch("discover_features.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="invalid: [yaml\n")
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_invalid_yaml(self, mock_stderr, mock_open, mock_exists):
        """When the config YAML is malformed, the script should exit with code 1.

        This test ensures parse errors are caught and formatted as an error message.
        """
        with self.assertRaises(SystemExit) as cm:
            discover("framework.yml")

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error parsing YAML", mock_stderr.getvalue())

    @patch("discover_features.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="tests:\n  other: 1\n")
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_missing_tests_bdd_features(self, mock_stderr, mock_open, mock_exists):
        """When the config lacks tests.bdd.features, the script should exit with code 1.

        This covers invalid configuration structures where the feature directory path
        cannot be resolved.
        """
        with self.assertRaises(SystemExit) as cm:
            discover("framework.yml")

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Could not find tests.bdd.features in config", mock_stderr.getvalue())

    @patch("discover_features.Path.exists")
    @patch("discover_features.Path.is_dir", return_value=False)
    @patch(
        "builtins.open",
        new_callable=unittest.mock.mock_open,
        read_data="tests:\n  bdd:\n    features: tests/features\n",
    )
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_missing_features_dir(self, mock_stderr, mock_open, mock_is_dir, mock_exists):
        """When the features directory is missing, the script should exit with code 1.

        This test simulates a valid YAML config with a bad features path.
        """
        mock_exists.side_effect = [True, False]

        with self.assertRaises(SystemExit) as cm:
            discover("framework.yml")

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("not found or is not a directory", mock_stderr.getvalue())

    @patch("discover_features.Path.exists", return_value=True)
    @patch("discover_features.Path.is_dir", return_value=True)
    @patch("discover_features.Path.rglob")
    @patch(
        "builtins.open",
        new_callable=unittest.mock.mock_open,
        read_data="tests:\n  bdd:\n    features: tests/features\n",
    )
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_successful_discovery(
        self, mock_stdout, mock_open, mock_rglob, mock_is_dir, mock_exists
    ):
        """When feature files exist, the script should print them as a JSON list.

        This test validates that a standard discovery run returns all .feature paths
        in deterministic order and writes JSON to stdout.
        """
        mock_file1 = Path("tests/features/feature1.feature")
        mock_file2 = Path("tests/features/feature2.feature")
        mock_rglob.return_value = [mock_file1, mock_file2]

        discover("framework.yml")

        output = mock_stdout.getvalue().strip()
        self.assertEqual(json.loads(output), [mock_file1.as_posix(), mock_file2.as_posix()])

    @patch("discover_features.Path.exists", return_value=True)
    @patch("discover_features.Path.is_dir", return_value=True)
    @patch("discover_features.Path.rglob")
    @patch(
        "builtins.open",
        new_callable=unittest.mock.mock_open,
        read_data="tests:\n  bdd:\n    features: tests/features\n    exclude:\n      - feature2.feature\n",
    )
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_successful_discovery_with_excludes(
        self, mock_stdout, mock_open, mock_rglob, mock_is_dir, mock_exists
    ):
        """When exclude rules are present, the script should omit those feature files.

        This test ensures that feature paths listed under tests.bdd.exclude are filtered
        out from the final JSON output.
        """
        mock_file1 = Path("tests/features/feature1.feature")
        mock_file2 = Path("tests/features/feature2.feature")
        mock_rglob.return_value = [mock_file1, mock_file2]

        discover("framework.yml")

        output = mock_stdout.getvalue().strip()
        self.assertEqual(json.loads(output), [mock_file1.as_posix()])

    def test_command_with_txt_file(self):
        """When command contains @file.txt, discovery reads features from that file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # Create feature files
            features_dir = tmp / "features"
            features_dir.mkdir()
            (features_dir / "smoke.feature").touch()
            (features_dir / "caching.feature").touch()
            (features_dir / "multicluster.feature").touch()

            # Create txt file listing only two features
            test_list_dir = tmp / "test_list"
            test_list_dir.mkdir()
            txt_file = test_list_dir / "my_service.txt"
            txt_file.write_text(
                "features/smoke.feature\nfeatures/caching.feature\n", encoding="utf-8"
            )

            config = {
                "tests": {
                    "path": ".",
                    "command": "python -m behave @test_list/my_service.txt --junit --format pretty",
                    "bdd": {"features": str(features_dir)},
                }
            }

            import yaml

            config_file = tmp / "framework.yml"
            config_file.write_text(yaml.dump(config), encoding="utf-8")

            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                discover(str(config_file))

            result = json.loads(mock_stdout.getvalue().strip())
            result_names = sorted(Path(p).name for p in result)
            self.assertEqual(result_names, ["caching.feature", "smoke.feature"])
            self.assertNotIn("multicluster.feature", result_names)

    def test_command_with_txt_file_root_relative(self):
        """When command uses @file.txt relative to the config root, discovery resolves it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            features_dir = tmp / "tests" / "features"
            features_dir.mkdir(parents=True)
            (features_dir / "smoke.feature").touch()
            (features_dir / "caching.feature").touch()

            test_list_dir = tmp / "test_list"
            test_list_dir.mkdir()
            txt_file = test_list_dir / "upgrades_data_eng_service.txt"
            txt_file.write_text(
                "tests/features/smoke.feature\n",
                encoding="utf-8",
            )

            config = {
                "tests": {
                    "path": "tests",
                    "command": "python -m behave @test_list/upgrades_data_eng_service.txt --junit --format pretty",
                    "bdd": {"features": str(features_dir)},
                }
            }

            import yaml

            config_file = tmp / "framework.yml"
            config_file.write_text(yaml.dump(config), encoding="utf-8")

            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                discover(str(config_file))

            result = json.loads(mock_stdout.getvalue().strip())
            result_names = sorted(Path(p).name for p in result)
            self.assertEqual(result_names, ["smoke.feature"])

    def test_command_with_inline_features(self):
        """When command contains inline .feature paths, discovery uses exactly those."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            features_dir = tmp / "features"
            features_dir.mkdir()
            (features_dir / "smoke.feature").touch()
            (features_dir / "caching.feature").touch()
            (features_dir / "multicluster.feature").touch()

            config = {
                "tests": {
                    "path": ".",
                    "command": (
                        "python -m behave features/smoke.feature features/caching.feature"
                        " --junit --format pretty"
                    ),
                    "bdd": {"features": str(features_dir)},
                }
            }

            import yaml

            config_file = tmp / "framework.yml"
            config_file.write_text(yaml.dump(config), encoding="utf-8")

            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                discover(str(config_file))

            result = json.loads(mock_stdout.getvalue().strip())
            result_names = sorted(Path(p).name for p in result)
            self.assertEqual(result_names, ["caching.feature", "smoke.feature"])
            self.assertNotIn("multicluster.feature", result_names)

    def test_command_with_tags_does_not_confuse_at_symbol(self):
        """--tags @smoke should not be mistaken for a @file.txt reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            features_dir = tmp / "features"
            features_dir.mkdir()
            (features_dir / "smoke.feature").touch()
            (features_dir / "other.feature").touch()

            config = {
                "tests": {
                    "path": ".",
                    "command": "python -m behave --tags @smoke --junit --format pretty",
                    "bdd": {"features": str(features_dir)},
                }
            }

            import yaml

            config_file = tmp / "framework.yml"
            config_file.write_text(yaml.dump(config), encoding="utf-8")

            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                discover(str(config_file))

            result = json.loads(mock_stdout.getvalue().strip())
            result_names = sorted(Path(p).name for p in result)
            # Should fall back to directory scan since no explicit feature targets
            self.assertEqual(result_names, ["other.feature", "smoke.feature"])


if __name__ == "__main__":
    unittest.main()
