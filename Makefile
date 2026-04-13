PYTHON ?= python3
CONFIG ?= config/humanatlas.yml

.PHONY: install build-db run presentation test

install:
	$(PYTHON) -m pip install -e ".[dev]"

build-db:
	$(PYTHON) scripts/build_duckdb.py --config $(CONFIG)

run:
	streamlit run app/dashboard.py -- --config $(CONFIG)

presentation:
	$(PYTHON) scripts/generate_presentation.py

test:
	pytest
