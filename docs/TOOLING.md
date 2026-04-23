# Tooling

## Goals

The project should not rely on remembered shell commands.

We standardise the developer workflow through:

- `Makefile`
- linting
- formatting
- unit and regression tests
- one-step quality checks
- Docker-based service lifecycle commands

## Required workflows

- create local virtual environment
- install runtime dependencies
- install development dependencies
- run the app locally
- format code
- lint code
- run test suite
- run all checks in one command
- build and run the Docker service

## Quality baseline

### Formatting

Use `ruff format` for Python formatting.

### Linting

Use `ruff check`.

### Tests

Use `pytest`.

Testing layers to add:

- unit tests for domain rules
- service tests for expense and repayment workflows
- API tests for core endpoints
- regression tests for DLA balance behaviour

## Makefile targets

Expected first targets:

- `make help`
- `make venv`
- `make install`
- `make dev-install`
- `make run`
- `make fmt`
- `make lint`
- `make test`
- `make check`
- `make docker-build`
- `make docker-up`
- `make docker-down`
- `make docker-logs`
- `make clean`

## Regression focus

The highest-value regression scenarios are:

- expense paid personally creates linked DLA entry
- repayment reduces DLA balance correctly
- search and filtering return the right records
- pre-trading flag persists correctly
- exports include expected records and fields
- attachment metadata is preserved
