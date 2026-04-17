# RedHat BDD Framework

## 📖 Description

The **RedHat BDD Framework** is a framework designed to standardize the writing and execution of BDD (Behavior-Driven Development) tests. It allows testing integrations between services and specific behaviors easily, using mock data or stub services. This framework is technology stack-independent and can run both locally and in CI/CD environments.

---

## ⚡ **Quick Start**

### 1. Clone the repository

```bash
git clone https://github.com/LukenLarra/RedHat-BDD-Framework.git
cd RedHat-BDD-Framework
```

### 2. Install dependencies

- **Backend and Tests (Python):**

```bash
make install-backend
make install-tests
```

- **Frontend (Node.js):**

```bash
cd ../frontend
npm install
```

### 3. Run the framework

- **With Python:**

```bash
python -m redhat_bdd_framework --config framework.yml
```

- **As an installed package (recommended):**

```bash
pip install -e .
bdd-framework --config framework.yml
```

---

## 📦 **Complete Installation**

### Requirements

> The requirements below apply to the **example project** included in this repository (Python backend + Node.js frontend + PostgreSQL). Your own project may have a completely different stack.

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 12+** (to run locally)
- **pip** and **npm** installed

### Database Configuration

The framework is database-agnostic — it does not connect to any database directly. Your application manages its own database connection using the `DATABASE_URL` environment variable (or whichever variable your stack uses). The example project in this repository uses **PostgreSQL** with **SQLAlchemy ORM**. There are two options to run it:

#### Option 1: Local PostgreSQL (Development)

1. **Install PostgreSQL** (if you don’t have it):
   - Windows: Download from [postgresql.org](https://www.postgresql.org/download/)
   - Linux: `sudo apt-get install postgresql`
   - macOS: `brew install postgresql`

2. **Create the database**:

   ```bash
   # Connect to PostgreSQL
   psql -U postgres

   # Create the database
   CREATE DATABASE movies_db;
   \q
   ```

   Or use graphical tools like **pgAdmin** or **DBeaver**.

3. **Configure the connection** in `framework.yml`:

   ```yaml
   env:
     DATABASE_URL: "postgresql://postgres:postgres@localhost:5432/movies_db"
   ```

   Adjust user, password, host, and port according to your installation.

4. The schema and sample data are created **automatically** when running the framework.

#### Option 2: GitHub Actions (CI/CD)

In GitHub Actions, declare the database as a job-level `services:` container — GitHub manages its full lifecycle. Set `DATABASE_URL` as a job-level `env:` and the action will pick it up automatically. See the [CI/CD Configuration](#cicd-configuration) section below.

### CI/CD Configuration

The framework is distributed as **composite actions** under `actions/` (`actions/main`, `actions/discovery`, and `actions/publish-reports`) that you can wire in your workflow:

1. **Composite Action (Sequential)**: Runs as a `uses:` step inside your job, sharing the same runner. The framework installs its own dependencies in an isolated virtual environment, so they never conflict with your project's packages.
2. **Discovery + Matrix (Parallel)**: The discovery action scans `.feature` files and outputs a JSON list. Your workflow then uses that list in a matrix strategy to run multiple jobs concurrently.
3. **Publish Reports**: A separate action for publishing JUnit-style XML results to the GitHub check interface.

#### Option A: Composite Action (Sequential execution)

Declare your database as a [job-level `services:`](https://docs.github.com/en/actions/using-containerized-services) container — GitHub spins it up before the first step and tears it down when the job ends. Set `DATABASE_URL` as a job-level `env:` variable; the action and all BDD tests inherit it automatically.

```yaml
# .github/workflows/ci_example.yml in YOUR repository
jobs:
  bdd-tests:
    runs-on: ubuntu-latest

    services:
      postgres: # or mysql, mongo, redis…
        image: postgres:15-alpine
        env:
          POSTGRES_USER: ${{ secrets.DB_USER }}
          POSTGRES_PASSWORD: ${{ secrets.DB_PASSWORD }}
          POSTGRES_DB: my_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DATABASE_URL: "postgresql://user:pass@localhost:5432/my_db"

    steps:
      - uses: actions/checkout@v4

      # 1. Set up YOUR runtime — use whatever your stack needs
      - uses: actions/setup-python@v5 # Python
        with:
          python-version: "3.12"

      # 2. Install YOUR project's dependencies
      - run: pip install -r requirements.txt

      # 3. Call the framework — DATABASE_URL is inherited from the job env
      - uses: LukenLarra/RedHat-BDD-Framework/actions/main@main
        with:
          service: "my-service"
          # python_version: "3.12"                # optional, lets uv build the venv using a specific python version
          # bdd_config: "framework.yml"           # optional, default: framework.yml
          # artifacts_log_dir: "junit"            # optional, default: junit
          # test_requirements: "tests/requirements.txt"  # optional, see below
          # service_package: "."                  # optional, install an importable package into the framework venv
```

#### Option B: Parallel Matrix Execution

If your test suite is large, you can speed up CI by discovering all `.feature` files dynamically and distributing them across GitHub runners. This allows you to keep using your `services:` and exact configuration seamlessly.

> Note: For this repository, each matrix runner still installs Python and Node dependencies locally. Because this stack uses interpreted languages with large dependency graphs, GitHub Actions native caching is usually faster than uploading/downloading full dependency artifacts between separate runners. Still, evaluate your own workflow: if your project can install shared dependencies once before the parallel matrix, that may be worth trying.

```yaml
# .github/workflows/ci_parallel_example.yml in YOUR repository
jobs:
  # 1. Discovery Job: calculates the JSON matrix dynamically
  discovery:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.discover.outputs.matrix }}
      has_features: ${{ steps.discover.outputs.has_features }}
    steps:
      - uses: actions/checkout@v4
      - id: discover
        uses: LukenLarra/RedHat-BDD-Framework/actions/discovery@main

  # 2. Runner Job: spins up isolated machines in parallel
  parallel-bdd:
    needs: discovery
    if: needs.discovery.outputs.has_features == 'true'
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      max-parallel: 16
      matrix:
        feature_file: ${{ fromJson(needs.discovery.outputs.matrix) }}

    services:
      postgres: # Works perfectly with matrix natively
        image: postgres:15-alpine
        env:
          POSTGRES_USER: ${{ secrets.DB_USER }}
          POSTGRES_PASSWORD: ${{ secrets.DB_PASSWORD }}
          POSTGRES_DB: my_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DATABASE_URL: "postgresql://user:pass@localhost:5432/my_db"

    steps:
      - uses: actions/checkout@v4

      # [ Insert your setup steps: python, dependencies, etc. exact same as Sequential ]

      - name: Run BDD Framework
        uses: LukenLarra/RedHat-BDD-Framework/actions/main@main
        with:
          service: "my-service"
          feature_file: ${{ matrix.feature_file }}
          artifact_name_suffix: "-${{ strategy.job-index }}"

  # 3. Report Job: unifies all XMLs
  publish-report:
    needs: parallel-bdd
    runs-on: ubuntu-latest
    if: always()
    permissions:
      contents: read
      checks: write
      pull-requests: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          pattern: bdd-test-reports-my-service-*
          path: reports/junit
          merge-multiple: true

      - uses: LukenLarra/RedHat-BDD-Framework/actions/publish-reports@main
        with:
          report_path: "reports/junit/*.xml"
          # The action now also generates a Markdown summary and uploads it as an artifact.
          # summary_output: "reports/bdd-test-summary.md"
          # summary_to_job: "true"
          # summary_artifact_name: "bdd-test-summary"
          # summary_artifact_name: "bdd-test-summary"
```

> **Tip:** The `services:` health check guarantees the database is fully ready before step 1 runs — no manual wait loops needed.

> **When NOT to use `services:`:** If a container needs custom CLI arguments, a non-default entrypoint, or wait logic beyond the built-in health-check flags, start it as a step instead.
>
> ```yaml
> # services: — standard image, no custom args, built-in health check is enough
> services:
>   redis:
>     image: redis:7-alpine
>     ports: ["6379:6379"]
>     options: >-
>       --health-cmd "redis-cli ping"
>       --health-interval 10s
>       --health-timeout 5s
>       --health-retries 5
>
> steps:
>   # would NOT work in services: — needs a custom server sub-command and
>   # its readiness endpoint is not a simple TCP check.
>   - name: Start MinIO
>     run: |
>       docker run -d --name minio \
>         -p 9000:9000 -p 9001:9001 \
>         -e MINIO_ROOT_USER=minioadmin \
>         -e MINIO_ROOT_PASSWORD=minioadmin \
>         quay.io/minio/minio server /data --console-address ":9001"
>
>   - name: Wait for MinIO
>     run: |
>       for i in $(seq 1 30); do
>         curl -sf http://localhost:9000/minio/health/live && echo "MinIO ready" && break
>         echo "  attempt $i/30..."; sleep 2
>       done
> ```

### Extra dependencies for step files (`test_requirements`)

The framework installs its own dependencies (`behave`, `requests`, `PyYAML`) in an **isolated virtual environment**. Behave runs inside that venv, so any `import` in your step files must resolve there.

If your step files import packages that are not bundled with the framework, provide a `requirements.txt` via the `test_requirements` input. The framework will install those packages into its venv before running the tests.

For import resolution of project modules, the framework sets `PYTHONPATH` in the test subprocess environment to include the project root. This is automatic and does not require adding `PYTHONPATH` manually in `framework.yml`.

---

## 🔧 **Framework Configuration**

The `framework.yml` file is the core of the configuration. Here, services, dependencies, and tests are defined.

### Workflow and Configuration Requirements

To use the framework in your own project, you must provide a `framework.yml` configuration file with the following keys:

- `tests.path`: Path to your BDD tests directory.
- `tests.command`: Command to execute your tests (e.g., `python run_bdd_tests.py ...`).
- `tests.bdd.features`: Path to your `.feature` files.
- `tests.bdd.steps`: Path to your step definitions (Python files).
- `tests.bdd.environment`: Path to your `environment.py` file for Behave.
- `tests.env`: Any environment variables required for your tests (e.g., `API_URL`, `DATABASE_URL`).

In your CI workflow, you must:

- Define global environment variables such as `DATABASE_URL` (or the variable your stack uses).
- Ensure all paths in your configuration file exist and are accessible to the framework.
- If your step files require additional dependencies, provide a `requirements.txt` and pass it as the `test_requirements` input to the framework.
- The framework runs Python-based BDD tests. You can specify the exact Python version to use for tests by passing the `python_version` input (e.g., `python_version: "3.12"`). If omitted, it will fall back to the environment's default Python.

---

### 📂 Required Users Project Structure

The framework does not enforce a fixed directory structure, but the paths specified in your `framework.yml` must exist and be correct. For example:

```
tests/
  features/
    your_features.feature
    steps/
      your_steps.py
    environment.py
```

You can customize the names and locations, but you must update the configuration file accordingly. If any path is missing, the framework will issue warnings and may fail to run your tests.

---

### Configuration Example

The `start_command` values are just shell commands — use whatever your stack requires (`bundle exec rails server`, `mvn spring-boot:run`, `node server.js`, etc.).

```yaml
project:
  name: "RedHat-BDD-Framework"
  version: "1.0.0"

services:
  api:
    enabled: true
    path: "backend"
    start_command: "python app.py" # or: bundle exec rails s, mvn spring-boot:run, node server.js…
    port: 8000

  web:
    enabled: true
    path: "frontend"
    start_command: "node server.js" # optional — omit this block if you have no frontend
    port: 3000

tests:
  enabled: true
  path: "tests"
  command: "python run_bdd_tests.py --junit --junit-directory reports/junit --format pretty"
```

---

### ⚠️ Framework Limitations

- The framework requires all configured paths to exist; missing directories or files will result in warnings or errors.
- Only basic dependencies (`behave`, `requests`, `PyYAML`) are installed automatically. Any additional dependencies must be managed by the user via `test_requirements`.
- The framework is database-agnostic; your application must handle its own database connection using an environment variable (e.g., `DATABASE_URL`).
- The framework does not validate the internal logic of your tests or guarantee compatibility with non-standard stacks.
- No built-in support for stacks or languages outside Python for BDD steps.

---

## 🧪 **Writing BDD Tests**

### Feature Structure

BDD tests are written in Gherkin format. Example:

```gherkin
Feature: Movie management
  Scenario: Retrieve all movies
    Given the API is running
    When I make a GET request to "/api/movies"
    Then I get a response with status code 200
    And the response contains a list of movies
```

### Steps in Python

Steps are defined in Python using `behave`. Example:

```python
from behave import given, when, then

@given('the API is running')
def step_api_running(context):
    # Verify that the API is active
    pass
```

---

## 🚀 **Running the Framework**

The framework uses a unified production configuration that works both in local development and CI/CD environments. This ensures consistency across all environments.

### Basic Execution

```bash
python -m redhat_bdd_framework --config framework.yml
```

### Execution Features

- **Robust health checks:** 60-second timeout with 2-second intervals
- **Environment variables:** Configured per service in `framework.yml`
- **Automatic JUnit reports:** Generated in `reports/junit/` for CI/CD integration
- **New report summary artifacts:** added in PR [#67](https://github.com/LukenLarra/RedHat-BDD-Framework/actions/runs/24399282526?pr=67)
- **Startup delay:** 5 seconds to ensure service stability
- **Stop on failure:** Tests stop at the first failure

### Testing CI/CD Locally with act

You can run the GitHub Actions workflow locally using [act](https://github.com/nektos/act), which allows you to test CI/CD changes before pushing to GitHub.

#### Prerequisites

- **Docker Desktop** must be installed and running
- **act** installed:
  - **Windows:** `winget install nektos.act`
  - **macOS:** `brew install act`
  - **Linux:** `curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash`

#### Usage

```bash
# List available workflows
make act-list

# Run the push workflow locally
make act-run

# Or use act directly
act push
```

#### How it works

When you run `act push`:

1. act pulls the required Docker images (runner + any database image defined in your workflow's `services:` block).
2. Creates and starts the database container using the `services:` configuration in your workflow file.
3. **Caches dependencies**: act uses its built-in cache server to restore `uv` and `npm` dependencies, significantly reducing installation time on subsequent runs.

   > **Note:** The built-in cache server in act is only briefly mentioned in the [official man page](https://man.archlinux.org/man/extra/act/act.1.en), and there is currently no dedicated documentation available for its usage. However, this functionality is available and works in act.

4. **Optimized execution**: The framework now uses hardlinks for `uv` dependencies in `/tmp`, avoiding redundant file copies.
5. Executes the workflow steps as defined in your GitHub Actions file.

#### Important notes

- **First run takes longer** as it downloads Docker images (~2-3 GB)
- The "Upload test reports" and "Publish test results" steps are automatically skipped (require GitHub API)
- All other steps run identically to GitHub Actions
- PostgreSQL is handled automatically by act - no manual setup needed
- **Windows users**: Test reports are generated inside the Docker container but may not appear in the local filesystem due to Docker Desktop's bind mount behavior. The workflow still validates correctly.

---

## 📊 **Generating Test Reports Locally**

The framework includes a script to generate a human-readable Markdown summary from the JUnit XML reports generated by the BDD tests. This is the same script used in CI/CD to add summary comments to Pull Requests.

To run it locally:

```bash
# Ensure you have run your tests first which generates XML files in reports/junit/
# Then generate the report:
python scripts/junit_report_summary.py --report-path "reports/junit/*.xml" --output "reports/bdd-test-summary.md"
```

This will parse the XML reports and output a `bdd-test-summary.md` file in the `reports/` folder, displaying totals and a breakdown of passed, failed, and skipped scenarios.

---

## 🏗️ **Framework Architecture**

- **Backend:** Python (FastAPI + Uvicorn) with PostgreSQL + SQLAlchemy ORM
- **Frontend:** Node.js (Express)
- **BDD Tests:** Python (Behave)
- **Orchestrator:** `-m redhat_bdd_framework` to manage services and tests
- **Database:** PostgreSQL 12+ (ephemeral in CI, local in development)

---
