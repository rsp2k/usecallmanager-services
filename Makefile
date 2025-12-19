.PHONY: help dev prod build up down logs shell clean lint test sync

help:
	@echo "usecallmanager-services management"
	@echo ""
	@echo "Usage:"
	@echo "  make dev      - Start in development mode (hot-reload)"
	@echo "  make prod     - Start in production mode"
	@echo "  make build    - Rebuild containers"
	@echo "  make up       - Start containers"
	@echo "  make down     - Stop containers"
	@echo "  make logs     - View container logs"
	@echo "  make shell    - Open shell in container"
	@echo "  make clean    - Remove containers and volumes"
	@echo "  make lint     - Run linter"
	@echo "  make test     - Run tests"
	@echo "  make sync     - Sync dependencies with uv"

dev:
	DEV_MODE=true docker compose up -d --build
	docker compose logs -f

prod:
	DEV_MODE=false docker compose up -d --build
	docker compose logs -f

build:
	docker compose build --no-cache

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec services /bin/bash

clean:
	docker compose down -v --remove-orphans

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

format:
	uv run ruff check --fix src tests
	uv run ruff format src tests

test:
	uv run pytest tests/ -v

sync:
	uv sync --dev
