# Makefile to simplify the execution of the BDD framework

# Variables
PYTHON := python
PIP := pip

# Rules
.PHONY: install-backend install-tests run-backend run-tests clean act-list act-run act-help

install-backend:
	@echo "Installing backend dependencies..."
	@$(PIP) install -r backend/requirements.txt

install-tests:
	@echo "Installing test dependencies..."
	@$(PIP) install -r tests/requirements.txt

run-backend:
	@echo "Running the backend..."
	@$(PYTHON) backend/app.py

run-tests:
	@echo "Running BDD tests..."
	@$(PYTHON) tests/run_bdd_tests.py

clean:
	@echo "Cleaning temporary files..."
	@find . -type d -name __pycache__ -exec rm -r {} +
	@find . -type f -name '*.pyc' -delete

# act - GitHub Actions local runner
act-list:
	@echo "Listing available workflows..."
	@act -l

act-run:
	@echo "Running workflow locally with act..."
	@act push

act-help:
	@echo "Available commands for act:"
	@echo "  make act-list  - Lists all available workflows"
	@echo "  make act-run   - Runs the push workflow locally"
	@echo ""
	@echo "Requirement: Docker Desktop must be running"
	@echo "act installation: https://github.com/nektos/act"
