import shutil
import tempfile
import unittest
from pathlib import Path

from redhat_bdd_framework.behave_utils import (
    BEHAVE_FLAGS_WITH_VALUES,
    is_feature_target,
    iterate_tokens,
    resolve_path,
)


class TestIterateTokens(unittest.TestCase):
    def test_flag_value_is_marked(self):
        parts = ["--tags", "@smoke", "features/a.feature"]
        result = list(iterate_tokens(parts, BEHAVE_FLAGS_WITH_VALUES))
        self.assertEqual(result[0], ("--tags", False))
        self.assertEqual(result[1], ("@smoke", True))
        self.assertEqual(result[2], ("features/a.feature", False))

    def test_plain_tokens_pass_through(self):
        parts = ["features/a.feature", "--dry-run"]
        result = list(iterate_tokens(parts, BEHAVE_FLAGS_WITH_VALUES))
        self.assertEqual(result, [("features/a.feature", False), ("--dry-run", False)])

    def test_consecutive_flags_with_values(self):
        parts = ["--tags", "@a", "--format", "json"]
        result = list(iterate_tokens(parts, BEHAVE_FLAGS_WITH_VALUES))
        self.assertTrue(result[1][1])
        self.assertTrue(result[3][1])

    def test_empty_input(self):
        self.assertEqual(list(iterate_tokens([], BEHAVE_FLAGS_WITH_VALUES)), [])

    def test_unknown_flags_not_skipped(self):
        parts = ["--dry-run", "features/a.feature"]
        result = list(iterate_tokens(parts, BEHAVE_FLAGS_WITH_VALUES))
        self.assertEqual(result[0], ("--dry-run", False))
        self.assertEqual(result[1], ("features/a.feature", False))


class TestIsFeatureTarget(unittest.TestCase):
    def test_plain_feature(self):
        self.assertTrue(is_feature_target("features/movies.feature"))

    def test_feature_with_line_number(self):
        self.assertTrue(is_feature_target("features/movies.feature:8"))

    def test_tag_at_symbol_not_feature(self):
        self.assertFalse(is_feature_target("@smoke"))

    def test_txt_file_not_feature(self):
        self.assertFalse(is_feature_target("@tests.txt"))

    def test_plain_flag_not_feature(self):
        self.assertFalse(is_feature_target("--dry-run"))


class TestResolvePath(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_returns_none_when_not_found(self):
        result = resolve_path(Path("nonexistent.feature"), [Path(self.tmp)])
        self.assertIsNone(result)

    def test_resolves_relative_against_base(self):
        f = Path(self.tmp) / "a.feature"
        f.touch()
        result = resolve_path(Path("a.feature"), [Path(self.tmp)])
        self.assertEqual(result, f.resolve())

    def test_absolute_path_returned_directly(self):
        f = Path(self.tmp) / "a.feature"
        f.touch()
        result = resolve_path(f, [])
        self.assertEqual(result, f)

    def test_absolute_missing_returns_none(self):
        result = resolve_path(Path(self.tmp) / "missing.feature", [])
        self.assertIsNone(result)

    def test_tries_bases_in_order(self):
        tmp2 = tempfile.mkdtemp()
        try:
            f = Path(tmp2) / "b.feature"
            f.touch()
            result = resolve_path(Path("b.feature"), [Path(self.tmp), Path(tmp2)])
            self.assertEqual(result, f.resolve())
        finally:
            shutil.rmtree(tmp2)

    def test_first_match_wins(self):
        f1 = Path(self.tmp) / "a.feature"
        f1.touch()
        tmp2 = tempfile.mkdtemp()
        try:
            f2 = Path(tmp2) / "a.feature"
            f2.touch()
            result = resolve_path(Path("a.feature"), [Path(self.tmp), Path(tmp2)])
            self.assertEqual(result, f1.resolve())
        finally:
            shutil.rmtree(tmp2)
