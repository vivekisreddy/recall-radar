# Common commands. Run `make help` to list them.
.DEFAULT_GOAL := help
SAMPLES := research/api-exploration/data/samples
TEST_DB := postgresql+psycopg://recall:recall@localhost:5432/recall_radar_test

help: ## Show this list
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

## --- Everything in Docker -------------------------------------------------
up: ## Start the whole stack (db, redis, api, worker, beat, web)
	docker compose up --build -d
	@echo "web http://localhost:3000   api http://localhost:8000/docs"

down: ## Stop the stack (keeps the database volume)
	docker compose down

logs: ## Follow logs from every service
	docker compose logs -f

seed: ## Load the 60 saved sample recalls into the running stack
	docker compose exec api recall-radar seed /samples

## --- Local development (db + redis in Docker, code on your machine) ------
services: ## Start only Postgres and Redis
	docker compose up -d db redis

install: ## Install backend and web dependencies
	cd backend && uv sync
	cd web && npm install

migrate: ## Apply database migrations
	cd backend && uv run alembic upgrade head

migration: ## Create a migration from model changes: make migration m="add items.color"
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

seed-local: ## Load sample recalls into the local database
	cd backend && uv run recall-radar seed ../$(SAMPLES)

api: ## Run the API with auto-reload on :8000
	cd backend && uv run uvicorn recall_radar.api.main:app --reload

worker: ## Run a Celery worker
	cd backend && uv run celery -A recall_radar.workers.celery_app worker --loglevel=info

web: ## Run the Next.js dev server on :3000
	cd web && npm run dev

## --- Quality -------------------------------------------------------------
test: ## Run backend tests (needs `make services`)
	cd backend && DATABASE_URL=$(TEST_DB) uv run pytest

lint: ## Lint and type-check everything
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd web && npm run lint && npx next typegen && npx tsc --noEmit

fmt: ## Auto-format the backend
	cd backend && uv run ruff check --fix . && uv run ruff format .

.PHONY: help up down logs seed services install migrate migration seed-local api worker web test lint fmt
