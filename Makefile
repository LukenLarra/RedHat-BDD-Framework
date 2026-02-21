# Makefile para simplificar la ejecución del framework BDD

# Variables
PYTHON := python
PIP := pip

# Reglas
.PHONY: install-backend install-tests run-backend run-tests clean act-list act-run act-help

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

# act - GitHub Actions local runner
act-list:
	@echo "Listando workflows disponibles..."
	@act -l

act-run:
	@echo "Ejecutando workflow localmente con act..."
	@act push --verbose

act-help:
	@echo "Comandos disponibles para act:"
	@echo "  make act-list  - Lista todos los workflows disponibles"
	@echo "  make act-run   - Ejecuta el workflow de push localmente"
	@echo ""
	@echo "Requisito: Docker Desktop debe estar corriendo"
	@echo "Instalación de act: https://github.com/nektos/act"
