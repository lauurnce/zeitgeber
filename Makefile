.PHONY: setup lint typecheck test api-dev web-dev web-test all

setup:
	uv sync --all-extras
	pnpm -C web install --frozen-lockfile
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .
	pnpm -C web lint
	pnpm -C web format:check

typecheck:
	uv run mypy
	pnpm -C web typecheck

test:
	uv run pytest

api-dev:
	uv run uvicorn api.main:app --reload --port 8000

web-dev:
	pnpm -C web dev

web-test:
	pnpm -C web test

all: lint typecheck test web-test
