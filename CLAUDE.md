# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Installation

```bash
pip install -r requirements.txt           # Framework core
pip install -r requirements-dev.txt       # Dev tools (ruff, pre-commit)
uv pip install --system -r backend/requirements.txt
uv pip install --system -r tests/requirements.txt
cd frontend && npm install
```

### Running Tests

```bash
# All BDD tests
python tests/run_bdd_tests.py

# Single feature file
python tests/run_bdd_tests.py tests/features/movies.feature

# Single scenario by line number
python tests/run_bdd_tests.py tests/features/movies.feature:8

# By tag
python tests/run_bdd_tests.py --tags=@ai --format pretty

# Via installed CLI
bdd-framework --config framework.yml
```

### Linting & Formatting

```bash
ruff check .           # lint
ruff format .          # format
ruff check --fix .     # lint + auto-fix
pre-commit run --all-files
```

### Makefile shortcuts

```bash
make install-backend   # install backend deps via uv
make install-tests     # install test deps via uv
make run-tests         # run full BDD suite
make act-run           # run CI workflow locally with act (requires Docker)
```

### Required Environment Variables (for local testing)

```bash
export API_URL=http://localhost:8000
export FRONTEND_URL=http://localhost:3000
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/movies_db"
export GROQ_API_KEY=your_key_here   # only for AI-powered test scenarios
```

## Architecture

This is a **stack-agnostic BDD testing framework** that orchestrates services, runs Gherkin-based tests via Behave, and publishes results to GitHub Checks. It serves both as a runnable example (movies API + frontend) and as a published GitHub Actions composite action.

### Core Framework (`redhat_bdd_framework/`)

- `cli.py`: Main orchestrator — loads `framework.yml`, validates config, health-checks services (60s timeout), injects env vars, runs `python -m behave` with JUnit reporting
- `__main__.py`: Entry point for the `bdd-framework` CLI

### Backend (`backend/`)

FastAPI REST API (port 8000) with SQLAlchemy 2.0 + PostgreSQL. Routes: `GET /api/movies`, `GET /api/movies/{id}`, `POST /api/movies`. Schema validation via Pydantic.

### Frontend (`frontend/`)

Express.js web server (port 3000) serving static files from `public/`.

### BDD Test Suite (`tests/`)

- `features/*.feature`: Gherkin scenarios — basic API tests, AI-powered semantic assertions, frontend UI tests
- `features/steps/movie_steps.py`: HTTP request steps using `requests`
- `features/steps/frontend_steps.py`: Browser automation via Playwright
- `features/environment.py`: Behave hooks — starts Playwright browser, MCP session manager for AI, waits for API health, resets DB between scenarios
- `run_bdd_tests.py`: Wrapper that passes CLI args to Behave

### GitHub Actions (`actions/`)

Three reusable composite actions published as `LukenLarra/RedHat-BDD-Framework/actions/*@main`:

- `main/`: Runs BDD tests in isolated Python venv
- `discovery/`: Scans for `.feature` files, outputs a JSON matrix for parallel CI runs
- `publish-reports/`: Aggregates JUnit XMLs and posts results to GitHub Checks API

### Configuration (`framework.yml`)

Single source of truth for test execution: feature paths, step paths, environment.py path, service health-check URLs, extra env vars, and optional `test_requirements` for extra pip packages.

### AI-Powered Testing

Scenarios tagged `@ai` use Groq/OpenAI API via MCP protocol (`mcp` package) for semantic validation — fuzzy matching and schema checks without hardcoded expected values. The MCP session is initialized in `environment.py:before_all`.

### Parallel CI

`ci_parallel_example.yml` uses the discovery action to fan out: one job per `.feature` file across up to 16 GitHub runners, then aggregates results via the publish-reports action.
