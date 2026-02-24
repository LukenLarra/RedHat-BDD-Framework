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
python bdd_framework.py --config framework.yml
```

---

## 📦 **Complete Installation**

### Requirements

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 12+** (to run locally)
- **pip** and **npm** installed

### Database Configuration

The framework uses **PostgreSQL** with **SQLAlchemy ORM**. There are two options to run it:

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

In GitHub Actions, the reusable workflow starts a **database container** (`docker run`) at the beginning of the job and tears it down automatically when the job finishes. The caller workflow is responsible for passing the image, credentials, and connection string via inputs and secrets.

See the [Creating Your Caller Workflow](#creating-your-caller-workflow) section for configuration details.

### CI/CD Configuration

#### Workflow Architecture

`.github/workflows/bdd-tests.yml` is a **reusable workflow** (`workflow_call` only). It is never triggered directly — it must always be invoked by a caller workflow that you create in your own repository.

The recommended pattern for the caller workflow is a two-job setup:

1. **`setup-deps`** — sets up the runtime (Python, Node.js, etc.), installs dependencies, and saves them to the cache using `actions/cache`.
2. **`bdd-tests`** — calls `.github/workflows/bdd-tests.yml`, passing the cache keys/paths generated in `setup-deps` and any database or service configuration.

This design means the reusable workflow is fully agnostic to language, runtime, and database technology. The caller is responsible for everything environment-specific.

#### Creating Your Caller Workflow

Create a file such as `.github/workflows/ci.yml` in your repository. The `setup-deps` job is entirely yours to define — install whatever runtimes and dependencies your project needs (Python, Java, Node.js, Ruby, Go, etc.) and cache them. The `bdd-tests` job then calls the reusable workflow and passes those cache details.

The structure always looks like this:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  checks: write
  pull-requests: write

jobs:
  setup-deps:
    runs-on: ubuntu-latest
    outputs:
      # Expose the cache key so the bdd-tests job can reference it
      deps_cache_key: ${{ steps.keys.outputs.deps_cache_key }}

    steps:
      - uses: actions/checkout@v4

      - name: Compute cache key
        id: keys
        run: |
          # Build a unique key based on your lockfile / dependency manifest
          echo "deps_cache_key=<runtime>-${{ runner.os }}-${{ hashFiles('<your-lockfile>') }}" >> $GITHUB_OUTPUT

      # ---------------------------------------------------------------
      # Set up your runtime here.
      # Examples:
      #   Python  → actions/setup-python
      #   Java    → actions/setup-java
      #   Node.js → actions/setup-node
      #   Ruby    → ruby/setup-ruby
      #   Go      → actions/setup-go
      # ---------------------------------------------------------------

      - name: Restore dependency cache
        id: cache
        uses: actions/cache@v4
        with:
          path: <path-to-your-dependency-directory> # e.g. .venv / node_modules / ~/.m2
          key: ${{ steps.keys.outputs.deps_cache_key }}

      - name: Install dependencies
        if: steps.cache.outputs.cache-hit != 'true'
        run: <your install command> # e.g. pip install / npm ci / mvn install

  bdd-tests:
    needs: setup-deps
    uses: ./.github/workflows/bdd-tests.yml
    with:
      service: "my-service"
      bdd_config: "framework.yml"

      # Pass the cache produced by setup-deps
      cache_key: ${{ needs.setup-deps.outputs.deps_cache_key }}
      cache_path: "<path-to-your-dependency-directory>"

      # Set to '' if your project is not Python-based
      python_venv_path: ""

      # Database — adjust image and URL to your technology
      db_enabled: true
      db_image: "postgres:15-alpine" # or mysql:8, mongo:7, etc.
      db_name: "my_db"
      db_port: "5432"
      database_url: "<full connection string for your DATABASE_URL env var>"
    secrets:
      db_user: ${{ secrets.DB_USER }}
      db_password: ${{ secrets.DB_PASSWORD }}
```

> **Tip:** If your project has a second set of dependencies to cache (e.g. a frontend alongside a backend), expose a second cache key from `setup-deps` and pass it via `secondary_cache_key` / `secondary_cache_path`.

---

## 🔧 **Framework Configuration**

The `framework.yml` file is the core of the configuration. Here, services, dependencies, and tests are defined.

### Configuration Example

```yaml
project:
  name: "RedHat-BDD-Framework"
  version: "1.0.0"

services:
  api:
    enabled: true
    path: "backend"
    start_command: "python app.py"
    port: 8000

  web:
    enabled: true
    path: "frontend"
    start_command: "node server.js"
    port: 3000

tests:
  enabled: true
  path: "tests"
  command: "python run_bdd_tests.py --junit --junit-directory reports/junit --format pretty"
```

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
python bdd_framework.py --config framework.yml
```

### Execution Features

- **Robust health checks:** 60-second timeout with 2-second intervals
- **Environment variables:** Configured per service in `framework.yml`
- **Automatic JUnit reports:** Generated in `reports/junit/` for CI/CD integration
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

1. act pulls the required Docker images (runner + any database image defined in your caller workflow)
2. Creates and starts the database container with the configuration you passed as inputs
3. Executes all workflow steps (install dependencies, run tests)
4. Generates test reports in `reports/junit/`
5. Cleans up containers when done

#### Important notes

- **First run takes longer** as it downloads Docker images (~2-3 GB)
- The "Upload test reports" and "Publish test results" steps are automatically skipped (require GitHub API)
- All other steps run identically to GitHub Actions
- PostgreSQL is handled automatically by act - no manual setup needed
- **Windows users**: Test reports are generated inside the Docker container but may not appear in the local filesystem due to Docker Desktop's bind mount behavior. The workflow still validates correctly.

---

## 🏗️ **Framework Architecture**

- **Backend:** Python (FastAPI + Uvicorn) with PostgreSQL + SQLAlchemy ORM
- **Frontend:** Node.js (Express)
- **BDD Tests:** Python (Behave)
- **Orchestrator:** `bdd_framework.py` to manage services and tests
- **Database:** PostgreSQL 12+ (ephemeral in CI, local in development)

---
