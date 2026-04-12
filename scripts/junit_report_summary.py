#!/usr/bin/env python3
import argparse
import datetime
import glob
import os
import xml.etree.ElementTree as ET


def local_name(tag: str) -> str:
    return tag.split("}")[-1]


def parse_testcase(testcase, suite_name):
    result = {
        "suite": suite_name,
        "name": testcase.get("name", "<unknown>") or "<unknown>",
        "classname": testcase.get("classname", ""),
        "file": testcase.get("file", ""),
        "line": testcase.get("line", ""),
        "time": float(testcase.get("time", "0") or 0),
        "status": "passed",
        "message": "",
        "details": "",
    }
    for child in testcase:
        tag = local_name(child.tag)
        if tag == "failure":
            result["status"] = "failed"
            result["message"] = child.get("message", "") or child.text or ""
            result["details"] = (child.text or "").strip()
            break
        if tag == "error":
            result["status"] = "error"
            result["message"] = child.get("message", "") or child.text or ""
            result["details"] = (child.text or "").strip()
            break
        if tag == "skipped":
            result["status"] = "skipped"
            result["message"] = child.get("message", "") or child.text or ""
            result["details"] = (child.text or "").strip()
            break
    return result


def iter_testsuites(root):
    if local_name(root.tag) == "testsuite":
        yield root
    for child in root:
        yield from iter_testsuites(child)


def parse_report_file(path):
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as exc:
        return {
            "file": path,
            "error": f"XML parse error: {exc}",
            "tests": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 0.0,
            "testcases": [],
        }

    testcases = []
    suites = list(iter_testsuites(root))
    total_time = 0.0
    for suite in suites:
        suite_name = suite.get("name", "<suite>")
        for testcase in suite.findall("testcase"):
            parsed = parse_testcase(testcase, suite_name)
            testcases.append(parsed)
            total_time += parsed["time"]

    totals = {
        "file": path,
        "error": None,
        "tests": len(testcases),
        "failures": sum(1 for t in testcases if t["status"] == "failed"),
        "errors": sum(1 for t in testcases if t["status"] == "error"),
        "skipped": sum(1 for t in testcases if t["status"] == "skipped"),
        "passed": sum(1 for t in testcases if t["status"] == "passed"),
        "time": total_time,
        "testcases": testcases,
        "suites": len(suites),
    }

    return totals


def format_duration(seconds: float) -> str:
    return str(datetime.timedelta(seconds=round(seconds, 2)))


def write_summary(reports, output_path, patterns):
    total_tests = sum(report["tests"] for report in reports)
    total_failures = sum(report["failures"] for report in reports)
    total_errors = sum(report["errors"] for report in reports)
    total_skipped = sum(report["skipped"] for report in reports)
    total_passed = sum(report["passed"] for report in reports)
    total_time = sum(report["time"] for report in reports)
    total_suites = sum(report["suites"] for report in reports)
    all_testcases = [tc for report in reports for tc in report["testcases"]]
    failures = [tc for tc in all_testcases if tc["status"] == "failed"]
    skipped = [tc for tc in all_testcases if tc["status"] == "skipped"]

    lines = [
        "# BDD CI Test Report Summary",
        "",
        f"Generated: {datetime.datetime.utcnow().isoformat()}Z",
        f"Report files: `{', '.join(patterns)}`",
        "",
        "## Totals",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Test suites | {total_suites} |",
        f"| Tests executed | {total_tests} |",
        f"| Passed | {total_passed} |",
        f"| Failed | {total_failures} |",
        f"| Errors | {total_errors} |",
        f"| Skipped | {total_skipped} |",
        f"| Total duration | {format_duration(total_time)} |",
        "",
    ]

    if failures:
        lines.extend(
            [
                "## Failed scenarios",
                "",
                "| Scenario | Suite | Location | Message |",
                "|---|---|---|---|",
            ]
        )
        for testcase in failures[:25]:
            location = testcase["file"] or testcase["classname"] or "<unknown>"
            if testcase["line"]:
                location = f"{location}:{testcase['line']}"
            message = testcase["message"].strip().replace("\n", " ")
            if len(message) > 220:
                message = message[:217].rstrip() + "..."
            lines.append(f"| {testcase['name']} | {testcase['suite']} | {location} | {message} |")
        remaining = len(failures) - 25
        if remaining > 0:
            lines.append("")
            lines.append(f"_And {remaining} more failed scenarios not shown._")
        lines.append("")

    if skipped:
        lines.extend(
            [
                "## Skipped scenarios",
                "",
                "| Scenario | Suite | Reason |",
                "|---|---|---|",
            ]
        )
        for testcase in skipped[:25]:
            reason = testcase["message"].strip().replace("\n", " ") or "-"
            lines.append(f"| {testcase['name']} | {testcase['suite']} | {reason} |")
        if len(skipped) > 25:
            lines.append("")
            lines.append(f"_And {len(skipped) - 25} more skipped scenarios not shown._")
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- Este resumen se genera a partir de los archivos JUnit XML producidos por Behave.",
            "- Los archivos de reporte originales se conservan y se pueden descargar desde los artefactos de CI.",
        ]
    )

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    return output_path


def gather_report_paths(patterns):
    paths = []
    for pattern in patterns:
        paths.extend(glob.glob(pattern, recursive=True))
    return sorted(set(paths))


def main():
    parser = argparse.ArgumentParser(
        description="Generate a Markdown summary from JUnit XML reports."
    )
    parser.add_argument(
        "--report-path",
        default="reports/junit/*.xml",
        help="Pattern or path to JUnit XML reports.",
    )
    parser.add_argument(
        "--output",
        default="reports/bdd-test-summary.md",
        help="Path to the Markdown summary output file.",
    )
    args = parser.parse_args()

    patterns = [pattern.strip() for pattern in args.report_path.split(",") if pattern.strip()]
    report_paths = gather_report_paths(patterns)

    if not report_paths:
        summary_path = args.output
        if os.path.dirname(summary_path):
            os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as handle:
            handle.write("# BDD CI Test Report Summary\n\n")
            handle.write("No JUnit XML reports were found for the pattern(s):\n")
            for pattern in patterns:
                handle.write(f"- `{pattern}`\n")
            handle.write(
                "\nCheck that the test runner produced XML reports in the expected path.\n"
            )
        print(f"No report files found for: {patterns}")
        print(f"Summary written to {summary_path}")
        return 1

    reports = [parse_report_file(path) for path in report_paths]
    summary_path = write_summary(reports, args.output, patterns)
    print(f"Generated summary: {summary_path}")
    print(open(summary_path, encoding="utf-8").read())


if __name__ == "__main__":
    raise SystemExit(main())
