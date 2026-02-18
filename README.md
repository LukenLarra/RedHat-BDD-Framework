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

- **Backend y Tests (Python):**

```bash
make install-backend
make install-tests
```

- **Frontend (Node.js):**

```bash
cd ../frontend
npm install
```

### 3. Ejecutar el framework

Para ejecutar el framework completo, utiliza uno de los siguientes comandos:

- **Con Python:**

```bash
python bdd_framework.py --config framework.yml
```

- **Con Make:**

```bash
make run-backend
make run-tests
```

---

## 📦 **Instalación Completa**

### Requisitos

- **Python 3.10+**
- **Node.js 18+**
- **pip** y **npm** instalados

### Configuración

1. Asegúrate de tener un archivo `framework.yml` configurado correctamente.
2. Define los servicios, dependencias y pruebas en el archivo de configuración.

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

## 🚀 **Ejecución del Framework**

El framework utiliza una configuración de producción unificada que funciona tanto en desarrollo local como en entornos CI/CD. Esto garantiza consistencia entre todos los entornos.

### Ejecución Básica

```bash
python bdd_framework.py --config framework.yml
```

### Características de la Ejecución

- **Health checks robustos:** Timeout de 60 segundos con intervalo de 2 segundos
- **Variables de entorno de producción:** `FLASK_ENV=production`, `NODE_ENV=test`
- **Reportes JUnit automáticos:** Se generan en `reports/junit/` para integración con CI/CD
- **Delay de inicio:** 5 segundos para asegurar estabilidad de servicios
- **Stop on failure:** Los tests se detienen al primer fallo

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
        run: python bdd_framework.py --config framework.yml
```

---

## 🏗️ **Arquitectura del Framework**

- **Backend:** Python (FastAPI) con SQLite
- **Frontend:** Node.js (Express)
- **BDD Tests:** Python (Behave)
- **Orquestador:** `bdd_framework.py` para gestionar servicios y pruebas

---

## 🔧 **Code Quality & Pre-commit**

El proyecto usa **pre-commit** para mantener un formato de código consistente en todo el equipo.

### Instalación Rápida

```bash
npm run install:dev
```

### Herramientas Incluidas

- **Python:** Black (formateo), isort (ordenar imports), Flake8 (linting)
- **JavaScript:** Prettier (formateo)
- **General:** Validación de YAML/JSON, limpieza de whitespace

### Comandos Útiles

```bash
npm run format        # Formatear todo el código
npm run lint          # Verificar estilo sin modificar
npm run precommit     # Ejecutar todos los checks manualmente
```

📖 **Ver [Guía Completa de Pre-commit](docs/PRE-COMMIT-GUIDE.md)** para más detalles.

---
