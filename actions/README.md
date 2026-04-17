# GitHub Actions for RedHat BDD Framework

This directory contains custom actions used by GitHub Actions workflows in this repository.

## Available actions

### `actions/discovery`

- Name: `RedHat BDD Framework - Discovery`
- What it does:
  - Discovers all `.feature` files in the project.
  - Produces a `matrix` output containing the list of feature file paths.
  - Returns `has_features=true` if features are found, and `false` otherwise.
- Typical use:
  - Generate a matrix for parallel BDD test execution.
  - Use the `matrix` output directly in `strategy.matrix.features`.

### `actions/main`

- Name: `RedHat BDD Framework`
- What it does:
  - Installs the BDD framework and project dependencies.
  - Runs the BDD tests using `python -m redhat_bdd_framework`.
  - Uploads test report artifacts (`reports/junit/*.xml`) when available.
- Important inputs:
  - `service`: service name used for artifact naming.
  - `feature_file`: specific `.feature` file to run.
  - `python_version`: Python version used for the test environment.
  - `test_requirements` and `service_package`: optional extra packages.

### `actions/publish-reports`

- Name: `RedHat BDD Framework - Publish Reports`
- What it does:
  - Publishes unit test results from XML report files.
  - Uses `EnricoMi/publish-unit-test-result-action@v2`.
- Main input:
  - `report_path`: pattern or path to XML report files.

## Usage examples

There is no need to duplicate the workflow code here; see `.github/workflows/` for real examples.

Check:

- `.github/workflows/ci_example.yml`
- `.github/workflows/ci_parallel_example.yml`

Those files show how these actions are wired into a complete workflow.
