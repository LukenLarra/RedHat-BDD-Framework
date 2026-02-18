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

- **With npm:**

```bash
npm test
```

---

## 📦 **Complete Installation**

### Requirements

- **Python 3.10+**
- **Node.js 18+**
- **pip** and **npm** installed

### Configuration

1. Ensure you have a properly configured `framework.yml` file.
2. Define the services, dependencies, and tests in the configuration file.

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
- **Production environment variables:** `FLASK_ENV=production`, `NODE_ENV=test`
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

---

## 🏗️ **Framework Architecture**

- **Backend:** Python (FastAPI) con SQLite
- **Frontend:** Node.js (Express)
- **BDD Tests:** Python (Behave)
- **Orchestrator:** `bdd_framework.py` to manage services and tests

---
