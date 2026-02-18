# RedHat BDD Framework

## 📖 Descripción

El **RedHat BDD Framework** es un framework diseñado para estandarizar la escritura y ejecución de pruebas BDD (Behavior-Driven Development). Permite probar integraciones entre servicios y comportamientos específicos de manera sencilla, utilizando datos simulados o servicios stub. Este framework es independiente del stack tecnológico y puede ejecutarse tanto localmente como en entornos de CI/CD.

---

## ⚡ **Quick Start**

### 1. Clonar el repositorio

```bash
git clone https://github.com/LukenLarra/RedHat-BDD-Framework.git
cd RedHat-BDD-Framework
```

### 2. Instalar dependencias

- **Backend (Python):**

```bash
cd backend
pip install -r requirements.txt
```

- **Frontend (Node.js):**

```bash
cd ../frontend
npm install
```

- **Tests:**

```bash
cd ../tests
pip install -r requirements.txt
```

### 3. Ejecutar el framework

- **Con Python:**

```bash
python bdd_framework.py --config framework.yml --profile local
```

- **Con npm en local:**

```bash
npm test
```

- **Con npm en CI:**

```bash
npm test:ci
```

---

## 📦 **Instalación Completa**

### Requisitos

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

## 🔧 **Configuración del Framework**

El archivo `framework.yml` es el núcleo de la configuración. Aquí se definen los servicios, dependencias y pruebas.

### Ejemplo de Configuración

```yaml
project:
  name: "RedHat-BDD-Framework"
  version: "1.0.0"

services:
  api:
    enabled: true
    path: "backend"
    start_command: "python app.py"
    port: 5000

  web:
    enabled: true
    path: "frontend"
    start_command: "node server.js"
    port: 3000

tests:
  enabled: true
  path: "tests"
  command: "python run_bdd_tests.py --no-capture --format pretty"
```

---

## 🧪 **Escribir Tests BDD**

### Estructura de Features

Los tests BDD se escriben en formato Gherkin. Ejemplo:

```gherkin
Feature: Movie management
  Scenario: Retrieve all movies
    Given the API is running
    When I make a GET request to "/api/movies"
    Then I get a response with status code 200
    And the response contains a list of movies
```

### Steps en Python

Los steps se definen en Python utilizando `behave`. Ejemplo:

```python
from behave import given, when, then

@given('the API is running')
def step_api_running(context):
    # Verificar que la API está activa
    pass
```

---

## 🚀 **Ejecución Local vs CI**

### Local

```bash
python bdd_framework.py --config framework.yml --profile local
```

### CI/CD

El framework incluye un workflow de GitHub Actions preconfigurado:

```yaml
jobs:
  bdd_tests:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Run BDD Framework
        run: python bdd_framework.py --config framework.yml --profile ci
```

---

## 🏗️ **Arquitectura del Framework**

- **Backend:** Python (Flask) con PostgreSQL + SQLAlchemy ORM
- **Frontend:** Node.js (Express)
- **BDD Tests:** Python (Behave)
- **Orquestador:** `bdd_framework.py` para gestionar servicios y pruebas
- **Base de Datos:** PostgreSQL 12+ (efímera en CI, local en desarrollo)

---
