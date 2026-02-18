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
python bdd_framework.py --config framework.yml
```

---

## 📦 **Complete Installation**

### Requirements

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 12+** (para ejecutar localmente)
- **pip** y **npm** instalados

### Configuración de Base de Datos

El framework utiliza **PostgreSQL** con **SQLAlchemy ORM**. Hay dos opciones para ejecutar:

#### Opción 1: PostgreSQL Local (Desarrollo)

1. **Instalar PostgreSQL** (si no lo tienes):
   - Windows: Descargar de [postgresql.org](https://www.postgresql.org/download/)
   - Linux: `sudo apt-get install postgresql`
   - macOS: `brew install postgresql`

2. **Crear la base de datos**:

   ```bash
   # Conectar a PostgreSQL
   psql -U postgres

   # Crear la base de datos
   CREATE DATABASE movies_db;
   \q
   ```

   O usando herramientas gráficas como **pgAdmin** o **DBeaver**.

3. **Configurar la conexión** en `framework.yml`:

   ```yaml
   env:
     DATABASE_URL: "postgresql://postgres:postgres@localhost:5432/movies_db"
   ```

   Ajusta usuario, contraseña, host y puerto según tu instalación.

4. El schema y los datos de ejemplo se crear**automáticamente** al ejecutar el framework.

#### Opción 2: GitHub Actions (CI/CD)

En GitHub Actions, el framework usa un **servicio PostgreSQL efímero** que:

- Se crea automáticamente al inicio del workflow
- Se configura con las credenciales por defecto
- Se destruye al finalizar la ejecución
- **No requiere configuración adicional**

Ver `.github/workflows/bdd-tests.yml` para detalles.

### Configuración del Framework

1. Asegúrate de tener un archivo `framework.yml` configurado correctamente.
2. Define los servicios, dependencias y pruebas en el archivo de configuración.
3. Verifica que `DATABASE_URL` apunte a tu instancia PostgreSQL.

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

- **Backend:** Python (Flask) con PostgreSQL + SQLAlchemy ORM
- **Frontend:** Node.js (Express)
- **BDD Tests:** Python (Behave)
- **Orquestador:** `bdd_framework.py` para gestionar servicios y pruebas
- **Base de Datos:** PostgreSQL 12+ (efímera en CI, local en desarrollo)

---
