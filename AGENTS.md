# AI Agent Guide for RedHat-BDD-Framework

This file is for AI coding agents working in this repository.

## What this repo is

- A Python-based BDD framework plus example support files.
- Core app under `redhat_bdd_framework/`.
- Scripts in `scripts/` for report generation and test utilities.
- Custom GitHub Actions in `actions/` for discovery, test execution, and report publishing.

## Primary tasks for AI agents

- Fix or extend backend Python code in `redhat_bdd_framework/`.
- Update action metadata and scripts under `actions/`.
- Add or improve tests under `tests/`.
- Maintain English-only comments and user-facing text in code.

## Important commands

Use these commands when editing or validating changes:

- `make install-backend` — install backend dependencies from `backend/requirements.txt`
- `make install-tests` — install test dependencies from `tests/requirements.txt`
- `python -m unittest tests.test_junit_report_summary` — run the JUnit summary tests
- `python -m redhat_bdd_framework --config framework.yml` — run the framework CLI
- `python tests/run_bdd_tests.py` — execute the repository BDD tests

## Style and conventions

- Use English in all code comments, docstrings, log messages, CLI help text, and user-facing strings.
- Keep Python code compatible with `python>=3.8` as defined in `pyproject.toml`.
- Follow the `ruff` configuration in `pyproject.toml` for formatting and linting.
- Prefer helper functions in `scripts/` to be reusable and testable.

## Key repository locations

- `pyproject.toml` — package metadata, dependencies, `ruff` config, and entry points.
- `Makefile` — common repo commands.
- `actions/main/action.yml` — main composite action for running the framework.
- `actions/discovery/action.yml` — feature discovery action.
- `actions/publish-reports/action.yml` — report publishing workflow.
- `scripts/junit_report_summary.py` — report summary generator used by CI.
- `tests/` — unit tests and BDD test suite examples.

## Notes for change suggestions

- Link to README sections rather than copying long documentation.
- Avoid changing external workflow behavior unless necessary.
- When modifying report generation, preserve the CI-compatible Markdown and XML parsing behavior.

## References

- [README.md](README.md) — installation, CI examples, and architecture overview.
- [pyproject.toml](pyproject.toml) — Python project and tool config.
