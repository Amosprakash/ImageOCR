# Makefile
.PHONY: help install test lint format type-check security clean docker-build docker-up docker-down

help:
	@echo "ImageAI Document AI Platform - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make install-dev      Install dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-cov         Run tests with coverage"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linting (flake8)"
	@echo "  make format           Format code (black, isort)"
	@echo "  make type-check       Run type checking (mypy)"
	@echo "  make security         Run security checks"
	@echo "  make pre-commit       Run all pre-commit hooks"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker images"
	@echo "  make docker-up        Start all services"
	@echo "  make docker-down      Stop all services"
	@echo "  make docker-logs      View logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts"
	@echo "  make clean-all        Remove all generated files"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pre-commit install

test:
	pytest

test-cov:
	pytest --cov=core --cov=api --cov=utils --cov-report=html --cov-report=term

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

lint:
	flake8 core/ api/ utils/ tests/

format:
	black core/ api/ utils/ tests/
	isort core/ api/ utils/ tests/

type-check:
	mypy core/ api/ utils/

security:
	bandit -r core/ api/ utils/
	safety check

pre-commit:
	pre-commit run --all-files

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

clean-all: clean
	rm -rf models/vector_stores/*
	rm -rf examples/output/*
	rm -f log.txt
