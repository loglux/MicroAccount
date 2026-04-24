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

## Standard development loop

For normal work on the repository, use this order:

1. read the relevant docs for the area being changed
2. identify the primary object and primary user action of the workflow
3. make the code or UI change
4. update tests when behaviour changes
5. update docs when behaviour or structure changes
6. run `make check`
7. if the change affects runtime behaviour or UI, rebuild and restart Docker

## Quality baseline

### Formatting

Use `ruff format` for Python formatting.

### Linting

Use `ruff check`.

### Tests

Use `pytest`.

Testing layers:

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

## Before changing UI

Before making a meaningful UI change, confirm:

- which screen is being changed
- what the primary object on that screen is
- what the primary action on that screen is
- whether the screen belongs to `Expenses`, `Documents`, `DLA`, or later `Income`
- whether the change improves workflow clarity or only adds chrome

UI changes should be rejected if they:

- make the primary workflow less obvious
- add equal visual weight to unrelated areas
- turn the app into a dashboard-card composition
- duplicate the same create flow across multiple screens without a clear reason
- blur `document`, `expense`, and `ledger entry` responsibilities

## Before changing workflow or data model

Before changing behaviour or model shape, check:

- `docs/PRODUCT_CONCEPT.md`
- `docs/IA_UX_BLUEPRINT.md`
- `docs/V1_BLUEPRINT.md`
- `docs/UK_RULES.md`

If the intended change contradicts those docs, update the docs in the same change.

## Pre-commit checklist

Before creating a commit, confirm:

- tests relevant to the change were added or updated if needed
- `make check` passes
- changed docs are updated
- no local company data or uploaded documents are being committed
- no temporary debugging code remains
- naming still matches the domain language of the project

## Docker verification

When a change affects web routes, templates, CSS, JS, runtime config, or startup behaviour:

- run `make docker-build`
- run `make docker-up`
- verify the affected pages or endpoints respond correctly

Container verification is not optional for UI and runtime-facing changes.
