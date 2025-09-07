# XP Telegram Bot Makefile
# Common development and deployment tasks

.PHONY: help install install-dev run test lint format clean docs

# Default target
help:
	@echo "XP Telegram Bot Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  setup        Complete setup including virtual environment"
	@echo ""
	@echo "Development Commands:"
	@echo "  run          Run the bot"
	@echo "  test         Run tests"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black"
	@echo "  type-check   Run type checking with mypy"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  clean        Clean up generated files"
	@echo "  docs         Generate documentation"
	@echo "  requirements Update requirements.txt"

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

setup:
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  Windows: venv\\Scripts\\activate"
	@echo "  Unix/macOS: source venv/bin/activate"
	@echo "Then run: make install-dev"

# Development targets
run:
	python bot.py

test:
	pytest tests/ -v

lint:
	flake8 src/ bot.py
	black --check src/ bot.py

format:
	black src/ bot.py
	isort src/ bot.py

type-check:
	mypy src/ bot.py

# Maintenance targets
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.log" -delete

docs:
	@echo "Documentation is in README.md"
	@echo "Consider adding Sphinx documentation in the future"

requirements:
	pip-compile requirements.in

# Deployment targets
docker-build:
	docker build -t xp-telegram-bot .

docker-run:
	docker run --env-file .env xp-telegram-bot

# Check if .env exists
check-env:
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Copy .env.example to .env and configure it."; \
		exit 1; \
	fi

# Run with environment check
run-safe: check-env run