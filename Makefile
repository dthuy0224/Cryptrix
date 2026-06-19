# ==========================================
# Cryptrix Project Command Orchestration
# ==========================================

.PHONY: help install dev-up dev-down lint format test build-all clean

help:
	@echo "Cryptrix CLI Tooling - Available Targets:"
	@echo "  install        Install uv workspace and dependencies locally"
	@echo "  dev-up         Launch local services using Docker Compose"
	@echo "  dev-down       Tear down local Docker Compose services"
	@echo "  lint           Run code analysis and linting checks (Ruff)"
	@echo "  format         Auto-format codebases (Ruff)"
	@echo "  test           Execute python testing suites (pytest)"
	@echo "  build-all      Build all production Docker images"
	@echo "  clean          Remove temporary folders, cache, and build files"

install:
	pip install uv
	uv venv
	uv pip install -e .[dev]

dev-up:
	docker-compose up -d --build

dev-down:
	docker-compose down

lint:
	uv run ruff check .
	cd frontend && npm run lint || true

format:
	uv run ruff format .
	cd frontend && npm run format || true

test:
	uv run pytest tests/

build-all:
	docker build -t cryptrix-backend:latest ./backend
	docker build -t cryptrix-frontend:latest ./frontend

clean:
	rm -rf .venv/
	rm -rf node_modules/
	rm -rf frontend/node_modules/
	rm -rf frontend/.next/
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
