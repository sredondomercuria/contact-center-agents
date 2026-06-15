# Atajos. Usa el venv .venv si existe.
PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
.PHONY: help install dev batch dry-run web agent-setup test lint fmt clean

help:  ## Ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## Instala el paquete
	$(PY) -m pip install -e .

dev:  ## Instala con dev + integraciones
	$(PY) -m pip install -e ".[dev,integrations]"

batch:  ## Procesa tickets abiertos (respeta DRY_RUN)
	$(PY) -m contact_center.run_batch

dry-run:  ## Procesa en modo simulación (no envía nada)
	DRY_RUN=true $(PY) -m contact_center.run_batch

web:  ## Dashboard de revisión/aprobación (http://localhost:8080)
	$(PY) -m contact_center.webapp.app

agent-setup:  ## Crea el Managed Agent en la plataforma de Claude e imprime los IDs
	$(PY) -m contact_center.integrations.managed_agents setup

test:  ## Tests
	$(PY) -m pytest -q

lint:  ## Linter
	$(PY) -m ruff check src tests

fmt:  ## Formatea
	$(PY) -m ruff format src tests

clean:  ## Limpia artefactos
	rm -rf output **/__pycache__ .pytest_cache .ruff_cache
