SHELL := /bin/bash

# =============================================================================
# Variables
# =============================================================================

.DEFAULT_GOAL:=help
.ONESHELL:
.EXPORT_ALL_VARIABLES:
MAKEFLAGS += --no-print-directory

# Define colors and formatting
BLUE := $(shell printf "\033[1;34m")
GREEN := $(shell printf "\033[1;32m")
RED := $(shell printf "\033[1;31m")
YELLOW := $(shell printf "\033[1;33m")
NC := $(shell printf "\033[0m")
INFO := $(shell printf "$(BLUE)ℹ$(NC)")
OK := $(shell printf "$(GREEN)✓$(NC)")
WARN := $(shell printf "$(YELLOW)⚠$(NC)")
ERROR := $(shell printf "$(RED)✖$(NC)")

# Define configuration
COMPOSE_INFRA_FILE := deploy/docker-compose.infra.yaml
COMPOSE_INFRA      := docker compose -f $(COMPOSE_INFRA_FILE)
POSTGRES_CONTAINER := postgres_V18_iron_track
PGBOUNCER_USERLIST := deploy/pgbouncer/conf/userlist.txt
SYNC_USERS ?= 'alfacat', 'admin', 'monitor'

##@ General
.PHONY: help
help: ## Display this help text
	@echo ""
	@echo "  Usage: make $(BLUE)<target>$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(NC)\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
# Development
# =============================================================================
##@ Development

.PHONY: install-uv
install-uv: ## Install latest version of uv
	@if command -v uv >/dev/null 2>&1; then \
		echo "${OK} uv is already installed"; \
	else \
		echo "${INFO} Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; \
		echo "${OK} uv installed successfully"; \
	fi

.PHONY: install
install: destroy clean ## Install project dependencies and dev packages
	@echo "${INFO} Starting fresh installation (Python 3.12)..."
	@uv python pin 3.12 >/dev/null 2>&1
	@uv venv >/dev/null 2>&1
	@uv sync --all-extras --dev
	@echo "${OK} Installation complete! 🎉"

.PHONY: lock
lock: ## Rebuild lockfiles from scratch
	@echo "${INFO} Rebuilding lockfiles... 🔄"
	@uv lock --upgrade >/dev/null 2>&1
	@echo "${OK} Lockfiles updated"

.PHONY: upgrade
upgrade: ## Upgrade all dependencies to the latest stable versions
	@echo "${INFO} Updating all dependencies... 🔄"
	@uv lock --upgrade
	@echo "${OK} Dependencies updated 🔄"
	@echo "${INFO} Updating pre-commit hooks..."
	@uv run pre-commit autoupdate
	@echo "${OK} Updated Pre-commit hooks 🔄"

.PHONY: clean
clean: ## Cleanup temporary build artifacts and caches
	@echo "${INFO} Cleaning working directory..."
	@rm -rf build/ dist/ .eggs/ .pytest_cache .ruff_cache .mypy_cache .coverage coverage.xml htmlcov/ .hypothesis >/dev/null 2>&1
	@find . -name '*.egg-info' -exec rm -rf {} + >/dev/null 2>&1
	@find . -type f -name '*.py[co]' -delete >/dev/null 2>&1
	@find . -name '__pycache__' -exec rm -rf {} + >/dev/null 2>&1
	@find . -name '*~' -exec rm -f {} + >/dev/null 2>&1
	@echo "${OK} Working directory cleaned"
	@$(MAKE) docs-clean

.PHONY: destroy
destroy: ## Destroy the virtual environment
	@echo "${INFO} Destroying virtual environment... 🗑️"
	@rm -rf .venv
	@echo "${OK} Virtual environment destroyed 🗑️"

.PHONY: release
release: ## Bump version and create tag (usage: make release bump=[major|minor|patch])
	@if [ -z "$(bump)" ]; then \
		echo "${ERROR} Argument 'bump' is missing! Use: make release bump=patch"; \
		exit 1; \
	fi
	@echo "${INFO} Starting release process ($(bump))... 📦"
	@uv run bump-my-version bump $(bump)
	@echo "${OK} Version bumped and tag created 🎉"

# =============================================================================
# Quality Control
# =============================================================================
##@ Quality Control

.PHONY: mypy
mypy: ## Run static type checking with mypy
	@echo "${INFO} Running mypy... 🔍"
	@uv run dmypy run src/app
	@echo "${OK} Mypy checks passed ✨"

.PHONY: pre-commit
pre-commit: ## Run all pre-commit hooks (ruff, codespell, etc.)
	@echo "${INFO} Running pre-commit checks... 🔎"
	@uv run pre-commit run --color=always --all-files
	@echo "${OK} Pre-commit checks passed ✨"

.PHONY: fix
fix: ## Auto-fix linting issues and format code
	@echo "${INFO} Running code formatters... 🔧"
	@uv run ruff check --fix --unsafe-fixes
	@uv run ruff format
	@echo "${OK} Code formatting complete ✨"

.PHONY: lint
lint: pre-commit mypy ## Run all linting and type checking
	@echo "${OK} All linting checks passed ✨"

.PHONY: test
test: ## Run tests in parallel (2 workers)
	@echo "${INFO} Running test cases... 🧪"
	@uv run pytest tests -n 2 --quiet
	@echo "${OK} Tests passed ✨"

.PHONY: coverage
coverage: ## Run tests and generate coverage reports (HTML/XML)
	@echo "${INFO} Running tests with coverage... 📊"
	@uv run pytest tests --cov -n auto --quiet
	@uv run coverage html >/dev/null 2>&1
	@uv run coverage xml >/dev/null 2>&1
	@echo "${OK} Coverage report generated (htmlcov/index.html) ✨"

.PHONY: check-all
check-all: lint test coverage ## Run everything: linting, tests, and coverage

# =============================================================================
# Documentation
# =============================================================================
##@ Documentation

.PHONY: docs-clean
docs-clean: ## Dump the existing built docs
	@echo "${INFO} Cleaning documentation build assets... 🧹"
	@rm -rf docs/_build >/dev/null 2>&1
	@echo "${OK} Documentation assets cleaned"

.PHONY: docs-serve
docs-serve: docs-clean ## Serve the docs locally with live-reload
	@echo "${INFO} Starting documentation server... 📚"
	@uv run sphinx-autobuild docs docs/_build/ -j auto --host 0.0.0.0 --port 8002 \
		--watch src/app --watch docs --watch tests --watch CONTRIBUTING.rst

.PHONY: docs
docs: docs-clean ## Build the HTML documentation
	@echo "${INFO} Building documentation... 📝"
	@uv run sphinx-build -M html docs docs/_build/ -E -a -j auto -W --keep-going
	@echo "${OK} Documentation built successfully"

.PHONY: docs-linkcheck
docs-linkcheck: ## Run internal link check on the docs
	@echo "${INFO} Checking documentation links... 🔗"
	@uv run sphinx-build -b linkcheck ./docs ./docs/_build -D linkcheck_ignore='http://.*','https://.*' >/dev/null 2>&1
	@echo "${OK} Link check complete"

.PHONY: docs-linkcheck-full
docs-linkcheck-full: ## Run full link check (including external URLs)
	@echo "${INFO} Running full link check... 🔗"
	@uv run sphinx-build -b linkcheck ./docs ./docs/_build -D linkcheck_anchors=0 >/dev/null 2>&1
	@echo "${OK} Full link check complete"

# =============================================================================
# Local Infrastructure
# =============================================================================
##@ Infrastructure

.PHONY: infra-up
infra-up: ## Start local infrastructure containers
	@echo "${INFO} Starting local infrastructure... 🚀"
	@$(COMPOSE_INFRA) up -d --force-recreate
	@echo "${OK} Infrastructure is ready"

.PHONY: infra-down
infra-down: ## Stop local infrastructure containers
	@echo "${INFO} Stopping infrastructure... 🛑"
	@$(COMPOSE_INFRA) down
	@echo "${OK} Infrastructure stopped"

.PHONY: infra-wipe
infra-wipe: ## Remove local containers, volumes and orphans
	@echo "${INFO} Wiping infrastructure... 🧹"
	@$(COMPOSE_INFRA) down -v --remove-orphans
	@echo "${OK} Infrastructure wiped clean"

.PHONY: infra-logs
infra-logs: ## Tail infrastructure logs
	@echo "${INFO} Tailing infrastructure logs... 📋"
	@$(COMPOSE_INFRA) logs -f

# =============================================================================
# Maintenance
# =============================================================================
##@ Maintenance

.PHONY: seed
seed: ## Populate database with initial data
	@echo "${INFO} Seeding database... 🌱"
	@uv run python -m src.app.scripts.seeder
	@echo "${OK} Seeding complete"

.PHONY: pgbouncer-sync
pgbouncer-sync: ## Sync Postgres roles to PgBouncer userlist (usage: make pgbouncer-sync SYNC_USERS="'user1','user2'")
	@echo "${INFO} Checking if PostgreSQL container is healthy... 🔍"
	@STATUS=$$(docker inspect --format='{{.State.Health.Status}}' $(POSTGRES_CONTAINER) 2>/dev/null); \
	if [ "$$STATUS" != "healthy" ]; then \
		echo "${ERROR} Container $(POSTGRES_CONTAINER) is not ready (Status: $$STATUS)"; \
		exit 1; \
	fi
	@echo "${INFO} Syncing users: $(SYNC_USERS) -> $(PGBOUNCER_USERLIST)"
	@mkdir -p $$(dirname $(PGBOUNCER_USERLIST))
	@rm -f $(PGBOUNCER_USERLIST)
	@docker exec -i $(POSTGRES_CONTAINER) psql -U postgres -d postgres -t -q -A -c \
		"SELECT '\"' || rolname || '\" \"' || rolpassword || '\"' FROM pg_authid WHERE rolname IN ($(SYNC_USERS));" \
		>> $(PGBOUNCER_USERLIST)
	@chmod 644 $(PGBOUNCER_USERLIST)
	@echo "${OK} Sync complete! ✨"