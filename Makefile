# Makefile to simplify the execution of the BDD framework

# Variables
PYTHON := python
UV := uv

# Rules
.PHONY: install-uv install-backend install-tests run-backend run-tests clean act-list act-run act-help

install-uv: ## Install uv package manager
	@echo "Installing uv..."
	@pip install uv

install-backend: ## Install backend Python dependencies from backend/requirements.txt
	@echo "Installing backend dependencies..."
	@$(UV) pip install --system -r backend/requirements.txt

install-tests: ## Install test dependencies from tests/requirements.txt
	@echo "Installing test dependencies..."
	@$(UV) pip install --system -r tests/requirements.txt

run-backend: ## Start the backend server (backend/app.py)
	@echo "Running the backend..."
	@$(PYTHON) backend/app.py

run-tests: ## Execute BDD tests via tests/run_bdd_tests.py
	@echo "Running BDD tests..."
	@$(PYTHON) tests/run_bdd_tests.py

clean: ## Remove __pycache__ dirs and .pyc files
	@echo "Cleaning temporary files..."
	@find . -type d -name __pycache__ -exec rm -r {} +
	@find . -type f -name '*.pyc' -delete

# act - GitHub Actions local runner
act-list: ## List available GitHub Actions workflows (act -l)
	@echo "Listing available workflows..."
	@act -l

act-run: ## Run GitHub Actions workflow locally on push event (act push)
	@echo "Running workflow locally with act..."
	@act push

help: ## Show this help screen
	@echo 'Usage: make <OPTIONS> ... <TARGETS>'
	@echo ''
	@echo 'Available targets are:'
	@echo ''
	@grep -E '^[ a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ''
