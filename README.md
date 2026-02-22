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

In GitHub Actions, the framework uses an **ephemeral PostgreSQL service** that:

- Is created automatically at the start of the workflow
- Is configured with default credentials
- Is destroyed at the end of execution
- **Requires no additional configuration**

See `.github/workflows/bdd-tests.yml` for details.

### Framework Configuration

#### GitHub Actions Inputs

The workflow `.github/workflows/bdd-tests.yml` includes the following configurable inputs:

- **`service`**: Name of the service being tested. Default value: `bdd-framework`.
- **`artifacts_log_dir`**: Directory where test reports are stored. Default value: `junit`.
- **`bdd_config`**: Framework configuration file. Default value: `framework.yml`.
- **`postgres_db`**: Name of the PostgreSQL database. Default value: `movies_db`.
- **`has_frontend`**: Indicates whether the service has a frontend. Default value: `true`.

#### Configuration Example

If you want to override the default values, you can do so when calling the workflow from another workflow or manually. Example:

```yaml
jobs:
  call-bdd-tests:
    uses: ./.github/workflows/bdd-tests.yml
    with:
      service: "my-service"
      artifacts_log_dir: "custom-logs"
      bdd_config: "custom-config.yml"
```

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

### CI/CD

The framework includes a preconfigured GitHub Actions workflow:

```yaml
jobs:
  bdd_tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Run BDD Framework
        run: python bdd_framework.py --config framework.yml
```

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

1. act automatically pulls the `postgres:15-alpine` image from Docker Hub
2. Creates and starts the PostgreSQL container with the correct configuration
3. Executes all workflow steps (setup Python, Node.js, install dependencies, run tests)
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
