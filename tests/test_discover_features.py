"""Unit tests for the discover_features script.

This module verifies that discover_features.discover() handles missing configuration,
invalid YAML, missing required configuration keys, missing feature directories,
and proper feature discovery including exclusions.
"""

import io
import json
import os
import sys
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


if __name__ == "__main__":
    unittest.main()
