# CLAUDE.md

This file is the entry point for AI coding agents (Claude Code and equivalents).

## Primary rules

`AGENTS.md` is the authoritative source for product boundaries, domain assumptions, coding expectations, and UX rules in this repository. Read it before making any substantial change.

Repo docs that extend `AGENTS.md`:

- `docs/PRODUCT_CONCEPT.md` — product definition and operating model
- `docs/IA_UX_BLUEPRINT.md` — screen responsibilities and navigation
- `docs/V1_BLUEPRINT.md` — data model, fields, routes
- `docs/ARCHITECTURE.md` — module layout
- `docs/UK_RULES.md` — UK accounting assumptions
- `docs/TOOLING.md` — commands and quality workflow
- `docs/IMPLEMENTATION_PLAN.md` — current execution plan

## Runtime

This project runs in Docker, not as a local Python process.

- `make docker-build` / `make docker-up` / `make docker-down` are the standard entry points.
- Default host port is `8040`.
- SQLite, uploaded files, and exports live in the host-mounted `./data`, `./storage`, `./exports`.

Do not start `uvicorn` or any local Python server from the agent side to smoke-test UI. The sanctioned way to bring the app up for runtime checks is the Docker targets in the `Makefile` (`make docker-build`, `make docker-up`, `make docker-logs`, `make docker-down`). Lint/tests run locally with the venv (`make lint`, `make test`, `make check`).

## Frontend

Server-rendered Jinja2 templates under `app/web/templates/`. CSS lives in `app/static/css/` and is split into `tokens.css`, `layout.css`, `components.css`, and per-page files under `pages/`.

When a template introduces a new class name, the corresponding CSS must land in the same change. Broken visual regressions from unstyled classes count as a UI regression, not a stylistic preference.

### Content rules (see `AGENTS.md` → "Content rules")

Never render raw code identifiers (`category_code`, `document_role`, `processing_status`, etc.) in the UI. Map every enum to a human label through `app/services/labels.py` and the `humanize` Jinja filter. UI language is plain English — no snake_case on screen.

### Visual style (see `AGENTS.md` → "Visual style")

Back-office operating tool, not a branded product page. No serif fonts, no clamp display headings, radius ≤6px, no box-shadows, no `backdrop-filter`, no decorative gradients, no KPI-style cards in page headers, no rise-in/fade-in animations. One sans-serif family, flat 1px-bordered panels, dense padding (8–14px), single accent colour, tables and forms as the primary surface, H1 ≤22px. Primary action = filled accent button, secondary = ghost with 1px border, destructive = ghost in danger colour.

## Quality bar before finishing

- `make lint`
- `make test`
- update the relevant docs listed in `AGENTS.md` when behaviour changes
- rebuild Docker if UI or runtime behaviour changed (`make docker-build && make docker-up`)

## What not to do

- Do not turn this into a full bookkeeping suite or SaaS-style product (see `AGENTS.md` → "Product boundaries").
- Do not blur `Document`, `Expense`, and `DirectorLoanEntry` into one model.
- Do not add dashboard-style decorative screens; `Expenses` is the home workflow.
- Do not commit without being asked. Do not push, force-push, or open PRs without being asked.
