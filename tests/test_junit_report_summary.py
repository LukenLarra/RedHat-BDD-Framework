import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

from scripts.junit_report_summary import (
    format_duration,
    local_name,
    parse_report_file,
    parse_testcase,
)


class TestJunitReportSummary(unittest.TestCase):
    def test_local_name(self):
        self.assertEqual(local_name("testsuite"), "testsuite")
        self.assertEqual(local_name("{http://namespace.com}testsuite"), "testsuite")

    def test_format_duration(self):
        self.assertEqual(format_duration(0.123), "0:00:00.120000")
        self.assertEqual(format_duration(65.5), "0:01:05.500000")
        self.assertEqual(format_duration(3600), "1:00:00")

    def test_parse_testcase_passed(self):
        element = ET.Element(
            "testcase",
            attrib={
                "name": "Test1",
                "classname": "feature.Test",
                "file": "test.feature",
                "line": "10",
                "time": "1.5",
            },
        )
        result = parse_testcase(element, "SuiteA")
        self.assertEqual(result["name"], "Test1")
        self.assertEqual(result["suite"], "SuiteA")
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["time"], 1.5)

    def test_parse_testcase_failed(self):
        element = ET.Element("testcase", attrib={"name": "Test2", "time": "2.0"})
        failure = ET.SubElement(element, "failure", attrib={"message": "Assertion Error"})
        failure.text = "Traceback here"

        result = parse_testcase(element, "SuiteB")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["message"], "Assertion Error")
        self.assertEqual(result["details"], "Traceback here")

    def test_parse_report_file_success(self):
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <testsuites>
            <testsuite name="SuiteC">
                <testcase name="PassedTest" time="1.0" classname="C" />
                <testcase name="FailedTest" time="0.5" classname="C">
                    <failure message="Failed" />
                </testcase>
                <testcase name="SkippedTest" time="0.0" classname="C">
                    <skipped message="Skip" />
                </testcase>
            </testsuite>
        </testsuites>
        """
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xml", encoding="utf-8"
        ) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            result = parse_report_file(temp_path)
            self.assertEqual(result["tests"], 3)
            self.assertEqual(result["passed"], 1)
            self.assertEqual(result["failures"], 1)
            self.assertEqual(result["skipped"], 1)
            self.assertEqual(result["errors"], 0)
            self.assertEqual(result["time"], 1.5)
            self.assertEqual(result["suites"], 1)
        finally:
            os.remove(temp_path)

    def test_parse_report_file_invalid_xml(self):
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".xml", encoding="utf-8"
        ) as f:
            f.write("Not an xml file")
            temp_path = f.name

        try:
            result = parse_report_file(temp_path)
            self.assertIn("error", result)
            self.assertTrue(result["error"].startswith("XML parse error"))
            self.assertEqual(result["tests"], 0)
        finally:
            os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
