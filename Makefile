# Makefile para simplificar la ejecución del framework BDD

# Variables
PYTHON := python
PIP := pip

# Reglas
.PHONY: install-backend install-tests run-backend run-tests clean

install-backend:
	@echo "Instalando dependencias del backend..."
	@$(PIP) install -r backend/requirements.txt

install-tests:
	@echo "Instalando dependencias de pruebas..."
	@$(PIP) install -r tests/requirements.txt

run-backend:
	@echo "Ejecutando el backend..."
	@$(PYTHON) backend/app.py

run-tests:
	@echo "Ejecutando pruebas BDD..."
	@$(PYTHON) tests/run_bdd_tests.py

clean:
	@echo "Limpiando archivos temporales..."
	@find . -type d -name __pycache__ -exec rm -r {} +
	@find . -type f -name '*.pyc' -delete