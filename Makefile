PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PYTEST := $(BIN)/pytest
RUFF := $(BIN)/ruff
UVICORN := $(BIN)/uvicorn
COMPOSE ?= docker compose

.DEFAULT_GOAL := help

help:
	@printf "Available targets:\n"
	@printf "  make venv         Create virtual environment\n"
	@printf "  make install      Install runtime dependencies\n"
	@printf "  make dev-install  Install runtime and development dependencies\n"
	@printf "  make run          Start local development server\n"
	@printf "  make fmt          Format Python code\n"
	@printf "  make lint         Run lint checks\n"
	@printf "  make test         Run test suite\n"
	@printf "  make check        Run lint and tests\n"
	@printf "  make docker-build Build the Docker image\n"
	@printf "  make docker-up    Start the Docker service\n"
	@printf "  make docker-down  Stop the Docker service\n"
	@printf "  make docker-logs  Tail Docker service logs\n"
	@printf "  make clean        Remove caches\n"

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

dev-install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

run:
	$(UVICORN) app.main:app --reload

fmt:
	$(RUFF) format .

lint:
	$(RUFF) check .

test:
	$(PYTEST)

check: lint test

docker-build:
	$(COMPOSE) build

docker-up:
	$(COMPOSE) up -d

docker-down:
	$(COMPOSE) down

docker-logs:
	$(COMPOSE) logs -f

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
