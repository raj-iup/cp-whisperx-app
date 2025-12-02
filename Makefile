# Makefile (skeleton) — CP-WhisperX-App
# Usage:
#   make help
#   make venv-common
#   make test
#   make quickstart

SHELL := /bin/bash

COMMON_VENV := venv/common
PY := $(COMMON_VENV)/bin/python
PIP := $(COMMON_VENV)/bin/pip

.PHONY: help venv-common bootstrap test lint format quickstart run clean

help:
	@echo ""
	@echo "CP-WhisperX-App — common commands"
	@echo ""
	@echo "  make venv-common   Create common venv and install common deps"
	@echo "  make bootstrap     Run repo bootstrap (creates multiple venvs)"
	@echo "  make test          Run tests"
	@echo "  make quickstart    Run quickstart script (CI-like smoke test)"
	@echo "  make lint          Run linter (if installed)"
	@echo "  make format        Run formatter (if installed)"
	@echo "  make clean         Remove local venvs and caches (careful)"
	@echo ""

venv-common:
	@mkdir -p venv
	@test -d $(COMMON_VENV) || python3 -m venv $(COMMON_VENV)
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements/requirements-common.txt

bootstrap:
	@chmod +x ./bootstrap.sh
	@./bootstrap.sh

test: venv-common
	@$(PIP) install -U pytest
	@$(PY) -m pytest -q tests

# Optional: install tools in common venv as needed
lint: venv-common
	@$(PIP) install -U ruff || true
	@$(PY) -m ruff check . || true

format: venv-common
	@$(PIP) install -U ruff || true
	@$(PY) -m ruff format . || true

quickstart:
	@chmod +x ./test-glossary-quickstart.sh
	@./test-glossary-quickstart.sh --help >/dev/null || true
	@echo "Tip: run with a short clip range to keep it fast."
	@echo "Example:"
	@echo "  ./test-glossary-quickstart.sh --clip 00:00:00-00:00:20 --job-dir out/job-quickstart --device mps"

run:
	@chmod +x ./run-pipeline.sh
	@./run-pipeline.sh --help || true

clean:
	@rm -rf venv .pytest_cache .ruff_cache __pycache__ **/__pycache__ || true
